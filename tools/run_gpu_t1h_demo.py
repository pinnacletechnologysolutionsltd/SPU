#!/usr/bin/env python3
"""Replay frozen T1H scalar-diagnostic scenes A/B/C/A with operator gates."""

import argparse
import grp
import hashlib
import json
import os
import pwd
import select
import secrets
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENDER = ROOT / "tools/send_gpu_t1h_scene.py"
PORT_DEFAULT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
SCENES = ("A", "B", "C", "A")
OBSERVATION_REQUIREMENTS = (
    "stable lock; grayscale threshold image matches frozen Scene A reference",
    "stable lock; visible change from A; grayscale threshold image matches Scene B reference",
    "stable lock; visible change from B; grayscale threshold image matches Scene C reference",
    "stable lock; return to frozen Scene A reference; report whether purple edge fringe is visible",
)
DWELL_SECONDS = 3
OBSERVATION_TIMEOUT_SECONDS = 180
MIN_START_TO_START_NS = 31_100_000
SEND_RESERVE_GUARD_SECONDS = 1.0


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_manifest(path, manifest):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    temporary.replace(path)
    status = manifest.get("status")
    if status not in ("RUNNING", "VALIDATED_ONLY",
                      "SEQUENCE_CONFIRMED_PENDING_CLOSE"):
        marker = ("PASS" if status == "PASS" else
                  "FAIL" if status in ("FAILED", "INTERRUPTED", "OPERATOR_STOP")
                  else "INCOMPLETE")
        for name in ("PASS", "INCOMPLETE", "FAIL"):
            marker_path = path.parent / name
            if name == marker:
                marker_path.write_text(marker + "\n")
            elif marker_path.exists():
                marker_path.unlink()


def process_identity():
    uid = os.geteuid()
    gid = os.getegid()
    groups = sorted(set(os.getgroups()) | {gid})
    try:
        username = pwd.getpwuid(uid).pw_name
    except KeyError:
        username = None
    group_names = []
    for group_id in groups:
        try:
            group_names.append(grp.getgrgid(group_id).gr_name)
        except KeyError:
            group_names.append(str(group_id))
    return {"uid": uid, "username": username, "gid": gid,
            "supplementary_gids": groups, "group_names": group_names}


def port_snapshot(port):
    snapshot = {"path": port}
    try:
        info = os.stat(port)
    except OSError as exc:
        snapshot.update({"present": False, "stat_error": repr(exc),
                         "errno": exc.errno})
        return snapshot
    snapshot.update({"present": True, "resolved_path": os.path.realpath(port),
                     "mode": stat.S_IMODE(info.st_mode), "uid": info.st_uid,
                     "gid": info.st_gid,
                     "readable": os.access(port, os.R_OK),
                     "writable": os.access(port, os.W_OK)})
    try:
        snapshot["group_name"] = grp.getgrgid(info.st_gid).gr_name
    except KeyError:
        snapshot["group_name"] = str(info.st_gid)
    return snapshot


def current_boot_id():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def load_attempt_deadline(load_evidence):
    load_evidence = Path(load_evidence).resolve()
    build_root = (ROOT / "build").resolve()
    if build_root not in load_evidence.parents:
        raise ValueError("load evidence must be beneath build/")
    result_path = load_evidence / "result.json"
    result = json.loads(result_path.read_text())
    markers = [name for name in ("COMPLETE", "FAILED", "TIMEOUT")
               if (load_evidence / name).is_file()]
    if markers != ["COMPLETE"] or result.get("status") != "COMPLETE":
        raise ValueError("load evidence must have exactly one COMPLETE marker")
    started = result.get("attempt_started_monotonic_ns")
    deadline_ns = result.get("attempt_deadline_monotonic_ns")
    attempt_limit = result.get("attempt_limit_seconds")
    if type(started) is not int or type(deadline_ns) is not int or \
            type(attempt_limit) is not int or attempt_limit < 76:
        raise ValueError("load evidence lacks the shared monotonic attempt deadline")
    if deadline_ns != started + attempt_limit * 1_000_000_000:
        raise ValueError("load evidence deadline does not match its first-action anchor")
    commands = result.get("commands", [])
    if not commands or commands[0].get("started_monotonic_ns") != started:
        raise ValueError("attempt deadline anchor does not match the first loader command")
    if result.get("host_boot_id") != current_boot_id():
        raise ValueError("load evidence belongs to a different host boot")
    return load_evidence, deadline_ns / 1_000_000_000, attempt_limit


def read_operator_observation(deadline, timeout=OBSERVATION_TIMEOUT_SECONDS):
    remaining = min(deadline - time.monotonic(), timeout)
    if remaining <= 0:
        return None
    readable, _writable, _exceptional = select.select(
        [sys.stdin], [], [], remaining)
    if not readable:
        return None
    return sys.stdin.readline().strip()


def read_confirmation(prefix, deadline, timeout=OBSERVATION_TIMEOUT_SECONDS):
    """Accept only a fresh, exact gate prefix before its bounded deadline."""
    gate_deadline = min(deadline, time.monotonic() + timeout)
    replies = []
    while time.monotonic() < gate_deadline:
        reply = read_operator_observation(gate_deadline)
        if reply is None:
            return None, replies
        replies.append({"text": reply, "received_utc": utc_now(),
                        "received_monotonic_ns": time.monotonic_ns()})
        if reply.startswith(prefix) and len(reply) > len(prefix):
            return reply, replies
        print(f"Reply did not match `{prefix}<details>`; "
              "re-enter the current gate response before timeout.", flush=True)
    return None, replies


def set_terminal(evidence, manifest, status):
    manifest["status"] = status
    manifest["finished_utc"] = utc_now()
    manifest["finished_monotonic_ns"] = time.monotonic_ns()
    write_manifest(evidence / "sequence.json", manifest)
    (evidence / status).write_text(status + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=PORT_DEFAULT)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--load-evidence-dir", type=Path,
                        help="programming evidence directory from this attempt")
    parser.add_argument("--observation-timeout-seconds", type=int,
                        default=OBSERVATION_TIMEOUT_SECONDS)
    parser.add_argument("--send-drain-bound-seconds", type=int,
                        help="frozen maximum write+tcdrain duration from the contract")
    parser.add_argument("--execute", action="store_true",
                        help="send packets to the selected UART")
    args = parser.parse_args()

    evidence = args.evidence_dir
    if not evidence.is_absolute():
        evidence = ROOT / evidence
    evidence = evidence.resolve()
    build_root = (ROOT / "build").resolve()
    if build_root not in evidence.parents:
        raise ValueError("evidence directory must be a new child of build/")
    if evidence.exists():
        raise FileExistsError(f"refusing existing evidence directory: {evidence}")

    fixtures = {}
    sys.path.insert(0, str(ROOT / "tools"))
    import send_gpu_t1h_scene as sender_module
    for scene in ("A", "B", "C"):
        relative, hex_hash, wire_hash, wire = sender_module.load_scene(scene)
        fixtures[scene] = {"fixture": relative, "hex_file_sha256": hex_hash,
                           "wire_sha256": wire_hash, "length": len(wire)}
    evidence.mkdir(parents=True)
    manifest_path = evidence / "sequence.json"
    manifest = {
        "format": "SPU_GPU_T1H_DEMO_SEQUENCE_V1",
        "status": "RUNNING" if args.execute else "VALIDATED_ONLY",
        "started_utc": utc_now(),
        "sender": str(SENDER.relative_to(ROOT)),
        "sender_sha256": sha256(SENDER),
        "port": args.port if args.execute else None,
        "load_evidence_dir": (str(args.load_evidence_dir)
                              if args.execute and args.load_evidence_dir else None),
        "execution_identity": process_identity() if args.execute else None,
        "port_preflight": port_snapshot(args.port) if args.execute else None,
        "baud": 115200,
        "framing": "8N1",
        "dwell_seconds": DWELL_SECONDS,
        "minimum_start_to_start_ns": MIN_START_TO_START_NS,
        "post_drain_delay_required_seconds": 0.020,
        "attempt_limit_seconds": None,
        "observation_timeout_seconds": args.observation_timeout_seconds,
        "sequence": list(SCENES),
        "gate_nonce": secrets.token_hex(6) if args.execute else None,
        "fixtures": fixtures,
        "sends": [],
    }
    write_manifest(manifest_path, manifest)

    if not args.execute:
        print(f"validated T1H A/B/C/A fixtures; evidence={evidence}")
        return 0
    fd = None
    deadline = None
    try:
        if args.load_evidence_dir is None:
            manifest["status"] = "FAILED"
            manifest["failure_stage"] = "attempt_deadline_preflight"
            manifest["error"] = "--execute requires --load-evidence-dir"
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(manifest["error"], file=sys.stderr)
            return 1
        if args.send_drain_bound_seconds is None or args.send_drain_bound_seconds <= 0:
            manifest["status"] = "FAILED"
            manifest["failure_stage"] = "send_drain_bound_preflight"
            manifest["error"] = "--execute requires a contract-frozen send/drain bound"
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(manifest["error"], file=sys.stderr)
            return 1
        try:
            load_evidence, deadline, attempt_limit = load_attempt_deadline(
                args.load_evidence_dir)
            manifest["load_evidence_dir"] = str(load_evidence.relative_to(ROOT))
            manifest["attempt_limit_seconds"] = attempt_limit
            manifest["attempt_deadline_monotonic_ns"] = int(
                deadline * 1_000_000_000)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            manifest["status"] = "FAILED"
            manifest["failure_stage"] = "attempt_deadline_preflight"
            manifest["error"] = repr(exc)
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(f"attempt deadline preflight failed; evidence={evidence}: {exc}",
                  file=sys.stderr)
            return 1
        if time.monotonic() + args.observation_timeout_seconds + args.send_drain_bound_seconds >= deadline:
            manifest["status"] = "ATTEMPT_TIME_LIMIT"
            manifest["failure_stage"] = "before_uart_open"
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            return 1
        if not sys.stdin.isatty():
            manifest["status"] = "FAILED"
            manifest["failure_stage"] = "operator_terminal_preflight"
            manifest["error"] = "--execute requires a terminal for per-scene operator gates"
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(manifest["error"], file=sys.stderr)
            return 1
        manifest["initial_lock_prompt_utc"] = utc_now()
        manifest["initial_lock_prompt_monotonic_ns"] = time.monotonic_ns()
        write_manifest(manifest_path, manifest)
        lock_prefix = f"READY: LOCK_STABLE {manifest['gate_nonce']}: "
        print("After the T1H diagnostic load, confirm stable VGA lock before any UART send. "
              f"Enter `{lock_prefix}<description>`.", flush=True)
        initial_reply, initial_replies = read_confirmation(
            lock_prefix, deadline, args.observation_timeout_seconds)
        manifest["initial_lock_replies"] = initial_replies
        if initial_reply is None:
            manifest["status"] = ("ATTEMPT_TIME_LIMIT" if time.monotonic() >= deadline
                                   else "OBSERVATION_TIMEOUT")
            manifest["failure_stage"] = "initial_lock_observation"
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            return 1
        manifest["initial_lock_confirmation"] = initial_reply
        manifest["initial_lock_confirmation_utc"] = utc_now()
        write_manifest(manifest_path, manifest)
        try:
            fd = sender_module.open_uart(args.port)
        except OSError as exc:
            manifest["status"] = "FAILED"
            manifest["failure_stage"] = "uart_open"
            manifest["transmission_classification"] = "UART_OPEN_FAILURE_ZERO_BYTES"
            manifest["bytes_written"] = 0
            manifest["error"] = repr(exc)
            manifest["finished_utc"] = utc_now()
            write_manifest(manifest_path, manifest)
            print(f"UART open failed; evidence={evidence}: {exc}",
                  file=sys.stderr)
            return 1
        manifest["uart_opened_utc"] = utc_now()
        write_manifest(manifest_path, manifest)
        for index, scene in enumerate(SCENES):
            if manifest["sends"]:
                previous_start = manifest["sends"][-1].get(
                    "write_start_monotonic_ns")
                if previous_start is not None:
                    earliest_start = previous_start + MIN_START_TO_START_NS
                    wait_ns = earliest_start - time.monotonic_ns()
                    if wait_ns > 0:
                        time.sleep(wait_ns / 1_000_000_000)
            send_observation_reserve = (
                args.observation_timeout_seconds + args.send_drain_bound_seconds)
            if time.monotonic() + send_observation_reserve + SEND_RESERVE_GUARD_SECONDS >= deadline:
                manifest["status"] = "ATTEMPT_TIME_LIMIT"
                manifest["failure_stage"] = "before_scene_send"
                manifest["failed_scene"] = scene
                write_manifest(manifest_path, manifest)
                break
            cycle = 1 if index < 3 else 2
            transcript = evidence / f"scene_{scene}_cycle_{cycle:02d}.json"
            stdout_path = evidence / f"scene_{scene}_cycle_{cycle:02d}.stdout.log"
            stderr_path = evidence / f"scene_{scene}_cycle_{cycle:02d}.stderr.log"
            started = utc_now()
            send = {"scene": scene, "cycle": cycle,
                    "started_utc": started,
                    "started_monotonic_ns": time.monotonic_ns(),
                    "send_observation_reserve_seconds": (
                        args.send_drain_bound_seconds +
                        args.observation_timeout_seconds),
                    "transcript": str(transcript.relative_to(ROOT)),
                    "stdout": str(stdout_path.relative_to(ROOT)),
                    "operator_observation": None}
            send["remaining_attempt_seconds_at_send_start"] = (
                deadline - time.monotonic())
            if send["remaining_attempt_seconds_at_send_start"] < send_observation_reserve:
                manifest["status"] = "ATTEMPT_TIME_LIMIT"
                manifest["failure_stage"] = "before_scene_send_reserve"
                manifest["failed_scene"] = scene
                manifest["sends_not_started"] = send
                write_manifest(manifest_path, manifest)
                break
            try:
                result = sender_module.send_scene_fd(
                    scene, fd, transcript, args.send_drain_bound_seconds,
                    overall_deadline=deadline)
                send["exit_code"] = 0
                send["finished_utc"] = utc_now()
                send["finished_monotonic_ns"] = time.monotonic_ns()
                send["transmission_classification"] = result[
                    "transmission_classification"]
                send["written"] = result["written"]
                send["write_calls"] = result["write_calls"]
                send["write_return_counts"] = result["write_return_counts"]
                send["send_drain_timeout_seconds"] = result[
                    "send_drain_timeout_seconds"]
                send["transport_worker_pid"] = result["transport_worker_pid"]
                send["transport_worker_exitcode"] = result[
                    "transport_worker_exitcode"]
                send["write_start_unix_ns"] = result["write_start_unix_ns"]
                send["write_start_monotonic_ns"] = result[
                    "write_start_monotonic_ns"]
                send["tcdrain_completed"] = result["tcdrain_completed"]
                send["drain_complete_unix_ns"] = result["drain_complete_unix_ns"]
                send["drain_complete_monotonic_ns"] = result[
                    "drain_complete_monotonic_ns"]
                send["post_drain_delay_seconds"] = result[
                    "post_drain_delay_seconds"]
                send["post_drain_delay_completed"] = result[
                    "post_drain_delay_completed"]
                send["post_drain_complete_monotonic_ns"] = result[
                    "post_drain_complete_monotonic_ns"]
                if (result["post_drain_delay_completed"] is not True or
                        result["post_drain_delay_seconds"] != 0.020):
                    raise RuntimeError(
                        "required 20 ms post-drain delay was not recorded as complete")
                if not result["tcdrain_completed"] or result["written"] != 151:
                    raise RuntimeError(
                        "T1H packet did not complete all 151 bytes and tcdrain")
                if manifest["sends"]:
                    previous_start = manifest["sends"][-1].get(
                        "write_start_monotonic_ns")
                    actual_gap = result["write_start_monotonic_ns"] - previous_start
                    send["prior_start_to_start_ns"] = actual_gap
                    if actual_gap < MIN_START_TO_START_NS:
                        raise RuntimeError(
                            "minimum start-to-start pacing was not met")
                stdout_path.write_text(
                    f"sent scene {scene}: {result['written']} bytes; "
                    f"transcript={transcript}\n")
                stderr_path.write_text("")
            except BaseException as exc:
                send["exit_code"] = 1
                send["finished_utc"] = utc_now()
                send["finished_monotonic_ns"] = time.monotonic_ns()
                send["error"] = repr(exc)
                if transcript.is_file():
                    try:
                        failed_send = json.loads(transcript.read_text())
                        for key in ("transmission_classification", "written",
                                    "write_calls", "tcdrain_completed",
                                    "write_return_counts", "uart_open_completed",
                                    "write_start_unix_ns", "write_start_monotonic_ns",
                                    "send_drain_timeout_seconds",
                                    "send_drain_timeout_stage",
                                    "device_write_state_unknown",
                                    "transport_worker_pid",
                                    "transport_worker_exitcode",
                                    "post_drain_delay_seconds",
                                    "post_drain_delay_completed",
                                    "post_drain_complete_monotonic_ns",
                                    "drain_complete_unix_ns",
                                    "drain_complete_monotonic_ns"):
                            if key in failed_send:
                                send[key] = failed_send[key]
                    except (OSError, json.JSONDecodeError):
                        pass
                stdout_path.write_text("")
                stderr_path.write_text(repr(exc) + "\n")
                manifest["sends"].append(send)
                manifest["status"] = "FAILED"
                manifest["failed_scene"] = scene
                write_manifest(manifest_path, manifest)
                break
            manifest["sends"].append(send)
            write_manifest(manifest_path, manifest)
            ordinal = index + 1
            prefix = (f"PASS {manifest['gate_nonce']} {ordinal:02d} "
                      f"cycle {send['cycle']} scene {scene}: ")
            send["observation_prefix"] = prefix
            requirement = OBSERVATION_REQUIREMENTS[index]
            send["observation_requirement"] = requirement
            print(f"HOST SEND COMPLETE for scene {scene}, cycle {send['cycle']}. "
                  f"Required observation: {requirement}. "
                  f"Enter `{prefix}<details>` only when confirmed.",
                  flush=True)
            print("operator> ", end="", flush=True)
            observation, replies = read_confirmation(
                prefix, deadline, args.observation_timeout_seconds)
            send["operator_replies"] = replies
            if observation is None:
                manifest["status"] = ("ATTEMPT_TIME_LIMIT" if time.monotonic() >= deadline
                                       else "OBSERVATION_TIMEOUT")
                manifest["failed_scene"] = scene
                manifest["stop_reason"] = "operator observation deadline expired"
                send["operator_observation"] = None
                write_manifest(manifest_path, manifest)
                break
            if time.monotonic() >= deadline:
                manifest["status"] = "ATTEMPT_TIME_LIMIT"
                manifest["failed_scene"] = scene
                manifest["stop_reason"] = "operator observation arrived at or after deadline"
                write_manifest(manifest_path, manifest)
                break
            send["operator_observation"] = observation
            send["observation_confirmed_utc"] = utc_now()
            send["observation_confirmed_monotonic_ns"] = time.monotonic_ns()
            write_manifest(manifest_path, manifest)
            if index + 1 < len(SCENES):
                remaining = deadline - time.monotonic()
                if remaining <= DWELL_SECONDS + args.observation_timeout_seconds + args.send_drain_bound_seconds:
                    manifest["status"] = "ATTEMPT_TIME_LIMIT"
                    manifest["failed_scene"] = SCENES[index + 1]
                    write_manifest(manifest_path, manifest)
                    break
                send["dwell_start_monotonic_ns"] = time.monotonic_ns()
                time.sleep(DWELL_SECONDS)
                send["dwell_complete_monotonic_ns"] = time.monotonic_ns()
                send["dwell_completed_seconds"] = (
                    send["dwell_complete_monotonic_ns"] -
                    send["dwell_start_monotonic_ns"]) / 1_000_000_000
                if send["dwell_completed_seconds"] < DWELL_SECONDS:
                    manifest["status"] = "FAILED"
                    manifest["failure_stage"] = "scene_dwell"
                    manifest["failed_scene"] = SCENES[index + 1]
                    manifest["stop_reason"] = "three-second dwell was not met"
                    write_manifest(manifest_path, manifest)
                    break
                write_manifest(manifest_path, manifest)
        else:
            manifest["status"] = "SEQUENCE_CONFIRMED_PENDING_CLOSE"
    except BaseException as exc:
        manifest["status"] = "INTERRUPTED"
        manifest["error"] = repr(exc)
        write_manifest(manifest_path, manifest)
        raise
    finally:
        if fd is not None:
            import os
            try:
                os.close(fd)
            except OSError as exc:
                manifest["status"] = "FAILED"
                manifest["failure_stage"] = "uart_close"
                manifest["error"] = repr(exc)
                manifest["finished_utc"] = utc_now()
                manifest["finished_monotonic_ns"] = time.monotonic_ns()
                write_manifest(manifest_path, manifest)

    if manifest["status"] == "SEQUENCE_CONFIRMED_PENDING_CLOSE":
        set_terminal(evidence, manifest, "PASS")
    else:
        manifest["finished_utc"] = utc_now()
        manifest["finished_monotonic_ns"] = time.monotonic_ns()
        write_manifest(manifest_path, manifest)
    print(f"T1H sequence {manifest['status']}; evidence={evidence}")
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
