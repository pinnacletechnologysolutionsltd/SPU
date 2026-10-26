#!/usr/bin/env python3
"""Send one frozen T1H scalar-diagnostic scene with durable evidence."""

import argparse
import hashlib
import json
import multiprocessing
import os
import tempfile
import termios
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POST_DRAIN_DELAY_SECONDS = 0.020
PORT_DEFAULT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
FIXTURES = {
    "A": ("fixtures/gpu_t1h_scene_a_wire_151b.hex",
          "93a4baf336ec166e69c802ecaeee43383810ad48b5597940229f83eff81db062",
          "656e4583753bd86d37b9fe0480cf6fa493e4f475232fb89271ae4bf5559ad3e3"),
    "B": ("fixtures/gpu_t1h_scene_b_wire_151b.hex",
          "6f913e4715f458d4caf70865649f7aff466520b46fc7366c2589c0a4e256dca5",
          "3858256dd7999634cf997afdf40318c16bf4d87a731b340148b31d1c49aed70a"),
    "C": ("fixtures/gpu_t1h_scene_c_wire_151b.hex",
          "df43e881a888ff96df09aab448f7c686d0367209ffcc6ae8e3d3060de573ee74",
          "f9415dcf3143604e25fa4591e49646d9cb446e28e81f87a1f3d771869cfb27d9"),
}


def configure_uart(fd):
    attrs = termios.tcgetattr(fd)
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR | termios.IGNCR |
                  termios.ICRNL | termios.IXON)
    attrs[1] &= ~termios.OPOST
    attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] |= termios.CS8 | termios.CLOCAL | termios.CREAD
    attrs[3] &= ~(termios.ECHONL | termios.ICANON | termios.ISIG |
                  termios.IEXTEN)
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


def load_scene(name):
    relative, expected_hex_hash, expected_wire_hash = FIXTURES[name]
    path = ROOT / relative
    text = path.read_text()
    hex_hash = hashlib.sha256(text.encode()).hexdigest()
    wire = bytes.fromhex(text)
    wire_hash = hashlib.sha256(wire).hexdigest()
    if hex_hash != expected_hex_hash or wire_hash != expected_wire_hash:
        raise ValueError(f"Scene {name}: frozen fixture hash mismatch")
    if len(wire) != 151 or wire[0] != 0xA5:
        raise ValueError(f"Scene {name}: expected 151 bytes beginning with A5")
    return relative, hex_hash, wire_hash, wire


def write_all(fd, wire, writer, on_progress):
    """Write the complete packet, reporting each confirmed partial write."""
    written = 0
    while written < len(wire):
        count = writer(fd, wire[written:])
        if type(count) is not int or count <= 0 or count > len(wire) - written:
            raise OSError(f"invalid UART write count {count!r} at offset {written}")
        written += count
        on_progress(written)
    return written


class SendDrainTimeout(TimeoutError):
    """The bounded transport worker did not finish before its deadline."""


def _transport_worker(fd, wire, deadline, connection, writer, drainer, sleeper):
    written = 0
    stage = "write"
    try:
        while written < len(wire):
            if time.monotonic() >= deadline:
                raise SendDrainTimeout("transport deadline expired before next write")
            count = writer(fd, wire[written:])
            if type(count) is not int or count <= 0 or count > len(wire) - written:
                raise OSError(f"invalid UART write count {count!r} at offset {written}")
            written += count
            connection.send({"type": "write_progress", "written": written,
                             "write_count": count,
                             "write_complete_unix_ns": time.time_ns(),
                             "write_complete_monotonic_ns": time.monotonic_ns()})
        stage = "drain"
        drainer(fd)
        connection.send({"type": "drain_complete",
                         "drain_complete_unix_ns": time.time_ns(),
                         "drain_complete_monotonic_ns": time.monotonic_ns()})
        stage = "post_drain_delay"
        sleeper(POST_DRAIN_DELAY_SECONDS)
        connection.send({"type": "complete",
                         "post_drain_delay_seconds": POST_DRAIN_DELAY_SECONDS,
                         "post_drain_delay_completed": True,
                         "post_drain_complete_unix_ns": time.time_ns(),
                         "post_drain_complete_monotonic_ns": time.monotonic_ns()})
    except BaseException as exc:
        try:
            connection.send({"type": "error", "error": repr(exc),
                             "timeout": isinstance(exc, TimeoutError),
                             "stage": stage})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def bounded_transport(fd, wire, result, transcript, timeout_seconds,
                      overall_deadline=None, writer=None, drainer=None,
                      sleeper=None):
    if timeout_seconds <= 0:
        raise ValueError("send/drain timeout must be positive")
    started_monotonic = time.monotonic()
    deadline = started_monotonic + timeout_seconds
    if overall_deadline is not None:
        deadline = min(deadline, overall_deadline)
    if deadline <= started_monotonic:
        raise SendDrainTimeout("global attempt deadline expired before transport")
    result["write_start_unix_ns"] = time.time_ns()
    result["write_start_monotonic_ns"] = time.monotonic_ns()
    result["send_drain_timeout_seconds"] = timeout_seconds
    result["send_drain_deadline_monotonic_ns"] = int(deadline * 1_000_000_000)
    result["write_return_counts"] = []
    result["write_calls"] = 0
    result["written"] = 0
    result["tcdrain_completed"] = False
    result["post_drain_delay_seconds"] = POST_DRAIN_DELAY_SECONDS
    result["post_drain_delay_completed"] = False
    save_transcript(transcript, result)

    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_transport_worker,
                              args=(fd, wire, deadline, sender,
                                    writer or os.write,
                                    drainer or termios.tcdrain,
                                    sleeper or time.sleep),
                              name="gpu-t1h-bounded-transport")
    failure = None
    completed = False
    timed_out = False

    def record_message(message):
        nonlocal failure, completed
        if message["type"] == "write_progress":
            result["written"] = message["written"]
            result["write_return_counts"].append(message["write_count"])
            result["write_calls"] += 1
            result["last_write_complete_unix_ns"] = message[
                "write_complete_unix_ns"]
            result["last_write_complete_monotonic_ns"] = message[
                "write_complete_monotonic_ns"]
            save_transcript(transcript, result)
        elif message["type"] == "drain_complete":
            result["tcdrain_completed"] = True
            result["drain_complete_unix_ns"] = message[
                "drain_complete_unix_ns"]
            result["drain_complete_monotonic_ns"] = message[
                "drain_complete_monotonic_ns"]
            save_transcript(transcript, result)
        elif message["type"] == "complete":
            result.update(message)
            completed = True
        elif message["type"] == "error":
            failure = (SendDrainTimeout(message["error"])
                       if message["timeout"] else OSError(message["error"]))
            result["error"] = message["error"]
            result["send_drain_timeout_stage"] = message["stage"]

    try:
        process.start()
        result["transport_worker_pid"] = process.pid
        save_transcript(transcript, result)
        sender.close()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                result["send_drain_timeout_stage"] = (
                    "post_drain_delay" if result.get("tcdrain_completed")
                    else "drain" if result["written"] == len(wire) else "write")
                failure = SendDrainTimeout(
                    f"send/drain deadline expired during "
                    f"{result['send_drain_timeout_stage']}")
                timed_out = True
                break
            if receiver.poll(min(remaining, 0.025)):
                try:
                    record_message(receiver.recv())
                except EOFError:
                    failure = OSError(
                        f"transport worker pipe closed; exit={process.exitcode}")
                    break
                if completed or failure is not None:
                    break
            elif not process.is_alive():
                failure = OSError("transport worker exited without a terminal record")
                break
        if failure is not None and process.is_alive():
            if timed_out:
                process.kill()
                result["transport_worker_stop_signal"] = "SIGKILL"
            else:
                process.terminate()
        process.join(timeout=0.05)
        if process.is_alive():
            process.kill()
            process.join(timeout=0.05)
        if process.is_alive():
            raise RuntimeError("bounded transport worker could not be stopped")
        while receiver.poll():
            try:
                record_message(receiver.recv())
            except EOFError:
                break
        if not completed and failure is None:
            failure = OSError(f"transport worker exited with status {process.exitcode}")
        if failure is not None:
            result["result"] = "FAIL"
            result["error"] = str(failure)
            result["transport_worker_exitcode"] = process.exitcode
            if timed_out and result.get("send_drain_timeout_stage") == "write":
                result["transmission_classification"] = (
                    "TRANSMISSION_STATE_UNKNOWN_AFTER_WRITE_TIMEOUT")
                result["device_write_state_unknown"] = True
            elif process.exitcode is not None and process.exitcode < 0 and \
                    result["written"] < len(wire):
                result["transmission_classification"] = (
                    "TRANSMISSION_STATE_UNKNOWN_AFTER_WORKER_EXIT")
                result["device_write_state_unknown"] = True
            else:
                result["transmission_classification"] = transmission_classification(
                    result["written"], result["length"],
                    result["tcdrain_completed"], result["uart_open_completed"])
            save_transcript(transcript, result)
            raise failure
        result["result"] = "PASS"
        result["transport_worker_exitcode"] = process.exitcode
        result["transmission_classification"] = transmission_classification(
            result["written"], result["length"], result["tcdrain_completed"],
            result["uart_open_completed"])
        save_transcript(transcript, result)
        return result
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=0.05)
            if process.is_alive():
                process.kill()
                process.join(timeout=0.05)
        receiver.close()
        if not sender.closed:
            sender.close()
        if process.pid is not None and not process.is_alive():
            process.close()


def transmission_classification(written, length, drained, opened):
    if not opened:
        return "UART_OPEN_FAILURE_ZERO_BYTES"
    if written == 0:
        return "ZERO_BYTE_WRITE_FAILURE"
    if written < length:
        return "PARTIAL_TRANSMISSION"
    if not drained:
        return "FULL_PACKET_WRITTEN_DRAIN_FAILED"
    return "COMPLETED_HOST_WRITE"


def open_uart(port):
    """Open and configure one UART handle for a complete bounded sequence."""
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_SYNC)
    try:
        configure_uart(fd)
    except BaseException:
        os.close(fd)
        raise
    return fd


def send_scene_fd(name, fd, transcript, timeout_seconds, overall_deadline=None,
                  writer=None, drainer=None, sleeper=None):
    """Transmit one frozen scene on an already-open UART and save its result."""
    relative, hex_hash, wire_hash, wire = load_scene(name)
    transcript = Path(transcript).resolve()
    build_root = (ROOT / "build").resolve()
    if build_root not in transcript.parents:
        raise ValueError("transcript must be a new file beneath build/")
    transcript.parent.mkdir(parents=True, exist_ok=True)
    with transcript.open("x"):
        pass
    result = {
        "format": "SPU_GPU_T1H_SINGLE_SCENE_V1",
        "scene": name,
        "fixture": relative,
        "hex_file_sha256": hex_hash,
        "wire_sha256": wire_hash,
        "length": len(wire),
        "port_fd": fd,
        "baud": 115200,
        "framing": "8N1",
        "written": 0,
        "write_calls": 0,
        "write_return_counts": [],
        "tcdrain_completed": False,
        "uart_open_completed": True,
        "result": "running",
    }
    save_transcript(transcript, result)
    try:
        return bounded_transport(fd, wire, result, transcript, timeout_seconds,
                                 overall_deadline, writer, drainer, sleeper)
    except BaseException as exc:
        result["result"] = "FAIL"
        result["error"] = repr(exc)
        result.setdefault("transmission_classification",
                          transmission_classification(
                              result["written"], result["length"],
                              result["tcdrain_completed"],
                              result["uart_open_completed"]))
        save_transcript(transcript, result)
        raise


def save_transcript(path, result):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=path.name + ".", suffix=".tmp",
                                     delete=False) as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, choices=tuple(FIXTURES))
    parser.add_argument("--port", default=PORT_DEFAULT)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--timeout-seconds", type=float,
                        help="maximum time for writes, tcdrain and post-drain delay")
    parser.add_argument("--validate-only", action="store_true",
                        help="verify the frozen fixture without opening a UART")
    args = parser.parse_args()

    relative, hex_hash, wire_hash, wire = load_scene(args.scene)
    if args.validate_only:
        print(f"validated scene {args.scene}: {len(wire)} bytes; "
              f"hex_sha256={hex_hash}; wire_sha256={wire_hash}")
        return
    if args.transcript is None:
        parser.error("--transcript is required unless --validate-only is used")
    if args.timeout_seconds is None or args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive unless --validate-only is used")
    transcript = args.transcript if args.transcript.is_absolute() else ROOT / args.transcript
    transcript = transcript.resolve()
    build_root = (ROOT / "build").resolve()
    if build_root not in transcript.parents:
        raise ValueError("transcript must be a new file beneath build/")
    transcript.parent.mkdir(parents=True, exist_ok=True)
    with transcript.open("x"):
        pass
    result = {"format": "SPU_GPU_T1H_SINGLE_SCENE_V1",
              "scene": args.scene, "fixture": relative,
              "hex_file_sha256": hex_hash, "wire_sha256": wire_hash,
              "length": len(wire), "port": args.port, "baud": 115200,
              "framing": "8N1", "written": 0, "write_calls": 0,
              "write_return_counts": [],
              "send_drain_timeout_seconds": args.timeout_seconds,
              "tcdrain_completed": False, "uart_open_completed": False,
              "result": "running"}
    save_transcript(transcript, result)
    fd = None
    try:
        fd = open_uart(args.port)
        result["uart_open_completed"] = True
        bounded_transport(fd, wire, result, transcript, args.timeout_seconds)
    except BaseException as exc:
        result["result"] = "FAIL"
        result["error"] = repr(exc)
        result.setdefault("transmission_classification",
                          transmission_classification(
                              result["written"], result["length"],
                              result["tcdrain_completed"],
                              result["uart_open_completed"]))
        save_transcript(transcript, result)
        raise
    finally:
        if fd is not None:
            os.close(fd)
    result["transmission_classification"] = transmission_classification(
        result["written"], result["length"], result["tcdrain_completed"],
        result["uart_open_completed"])
    save_transcript(transcript, result)
    print(f"sent scene {args.scene}: {result['written']} bytes; transcript={transcript}")


if __name__ == "__main__":
    main()
