#!/usr/bin/env python3
"""Run reproducible Wukong RPLU2PADE bench campaigns.

Every bitstream phase uses the attribution-safe sequence:

    load FPGA bitstream -> N * (reboot RP2350 -> wait for CDC -> capture one run)

The canonical bitstream is measured at both ends.  A failure in either
control phase voids the entire campaign.  Results are checkpointed as JSON
after every run and keyed by the loaded bitstream's SHA-256 digest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    import serial
except ImportError:  # pragma: no cover - exercised only on an unprepared bench
    serial = None


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL = REPO / "build/spu_a7_100t_RPLU2PADE.bit"
DEFAULT_OUTPUT_ROOT = REPO / "build/pade_campaigns"
DEFAULT_PORT = Path(
    "/dev/serial/by-id/usb-Raspberry_Pi_Pico_CB81353DCE678119-if00"
)
# This bench's DirtyJTAG. Reset before every load by DEFAULT, because the
# adapter stalls under sustained use: a campaign is ~110 back-to-back bitstream
# loads, and openFPGALoader then fails with "usb bulk write failed -9"
# (LIBUSB_ERROR_PIPE, a stalled endpoint) and "Fail to get version". That voided
# three campaign attempts on 2026-08-04/05 while the adapter itself stayed
# healthy -- `--detect` returned the A7-100T IDCODE cleanly throughout, and a
# `usbreset` cleared it every time.
#
# Cost is ~0.5 s per load, under a minute across a full campaign. Set
# --dirtyjtag-usb-id '' to disable.
DEFAULT_DIRTYJTAG_USB_ID = "1209:c0ca"
MIN_RUNS = 10
EXPECTED_CASES = [
    "two_over_one",
    "two_over_two",
    "five_over_two",
    "seven_over_three",
    "wide_constants",
]
VERDICT_RE = re.compile(r"^RPLU2PADE_J11:\s+(PASS|FAIL)\s*$")
CASE_BEGIN_RE = re.compile(
    r"^case=(\S+)\s+numerator=(\d+)\s+denominator=(\d+)\s+expected=(\d+)\s*$"
)
CASE_END_RE = re.compile(r"^case=(\S+)\s+(PASS|FAIL)\s*$")
QR_RE = re.compile(
    r"^result qr valid=(\d+) lane=(\d+) "
    r"A=0x([0-9A-Fa-f]{16}) B=0x([0-9A-Fa-f]{16}) "
    r"C=0x([0-9A-Fa-f]{16}) D=0x([0-9A-Fa-f]{16})\s*$"
)


class CampaignError(RuntimeError):
    """A bench operation or capture was not trustworthy."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_command(command: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        rendered = " ".join(command)
        raise CampaignError(
            f"command failed ({completed.returncode}): {rendered}\n{completed.stdout}"
        )
    return completed


def load_bitstream(path: Path, loader: str, jtag_hz: int) -> str:
    completed = run_command(
        [loader, "-c", "dirtyJtag", "--freq", str(jtag_hz), str(path)],
        timeout=180.0,
    )
    return completed.stdout


def reboot_rp2350(picotool: str) -> str:
    return run_command([picotool, "reboot", "-f"], timeout=20.0).stdout


def reset_dirtyjtag(usbreset: str, usb_id: str, settle: float) -> str:
    output = run_command([usbreset, usb_id], timeout=20.0).stdout
    time.sleep(settle)
    return output


def wait_for_port(port: Path, timeout: float) -> Path:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port.exists():
            return port.resolve()
        time.sleep(0.25)
    raise CampaignError(f"CDC port {port} did not appear within {timeout:.1f}s")


def parse_capture(text: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    verdicts: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = CASE_BEGIN_RE.match(line)
        if match:
            current = {
                "name": match.group(1),
                "numerator": int(match.group(2)),
                "denominator": int(match.group(3)),
                "expected": int(match.group(4)),
            }
            cases.append(current)
            continue

        match = QR_RE.match(line)
        if match and current is not None:
            current["result"] = {
                "valid": int(match.group(1)),
                "lane": int(match.group(2)),
                "A": f"0x{match.group(3).upper()}",
                "B": f"0x{match.group(4).upper()}",
                "C": f"0x{match.group(5).upper()}",
                "D": f"0x{match.group(6).upper()}",
            }
            continue

        match = CASE_END_RE.match(line)
        if match:
            named = next((case for case in reversed(cases) if case["name"] == match.group(1)), None)
            if named is not None:
                named["verdict"] = match.group(2)
            continue

        match = VERDICT_RE.match(line)
        if match:
            verdicts.append(match.group(1))

    if len(verdicts) != 1:
        raise CampaignError(
            f"capture contains {len(verdicts)} final verdicts; expected exactly one"
        )
    names = [case["name"] for case in cases]
    if names != EXPECTED_CASES:
        raise CampaignError(
            f"capture case sequence is {names!r}; expected {EXPECTED_CASES!r}"
        )
    incomplete = [
        case["name"]
        for case in cases
        if "result" not in case or "verdict" not in case
    ]
    if incomplete:
        raise CampaignError(f"incomplete case records: {', '.join(incomplete)}")

    failing = [case for case in cases if case["verdict"] != "PASS"]
    derived_verdict = "FAIL" if failing else "PASS"
    if verdicts[0] != derived_verdict:
        raise CampaignError(
            f"final verdict {verdicts[0]} disagrees with case verdicts ({derived_verdict})"
        )
    return {
        "verdict": verdicts[0],
        "cases": cases,
        "failing_cases": failing,
    }


def capture_one(port: Path, baud: int, timeout: float, log_path: Path) -> dict[str, Any]:
    if serial is None:
        raise CampaignError(
            "pyserial is required; activate .venv or install requirements.txt"
        )

    deadline = time.monotonic() + timeout
    lines: list[str] = []
    with serial.Serial(str(port), baud, timeout=1) as stream:
        while time.monotonic() < deadline:
            raw = stream.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", "replace")
            lines.append(line)
            sys.stdout.write(line)
            sys.stdout.flush()
            if VERDICT_RE.match(line.strip()):
                break

    text = "".join(lines)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(text, encoding="utf-8")
    parsed = parse_capture(text)
    parsed["capture_log"] = str(log_path.relative_to(REPO))
    return parsed


def identify(path: Path) -> tuple[Path, str]:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise CampaignError(f"not a regular file: {resolved}")
    return resolved, sha256_file(resolved)


def add_artifact(summary: dict[str, Any], path: Path, digest: str) -> None:
    record = summary["bitstreams"].setdefault(
        digest,
        {
            "sha256": digest,
            "paths": [],
            "executions": [],
            "attempts": 0,
            "runs": 0,
            "passes": 0,
            "failures": 0,
            "errors": 0,
            "pass_rate": None,
        },
    )
    rendered = str(path)
    if rendered not in record["paths"]:
        record["paths"].append(rendered)


def checkpoint(summary_path: Path, summary: dict[str, Any]) -> None:
    for artifact in summary["bitstreams"].values():
        executions = artifact["executions"]
        measurements = [
            run for run in executions if run.get("verdict") in {"PASS", "FAIL"}
        ]
        artifact["attempts"] = len(executions)
        artifact["runs"] = len(measurements)
        artifact["passes"] = sum(run.get("verdict") == "PASS" for run in executions)
        artifact["failures"] = sum(run.get("verdict") == "FAIL" for run in executions)
        artifact["errors"] = sum(run.get("verdict") == "ERROR" for run in executions)
        artifact["pass_rate"] = (
            artifact["passes"] / artifact["runs"] if artifact["runs"] else None
        )
    summary["updated_utc"] = utc_now()
    atomic_json(summary_path, summary)


def execute_run(
    *,
    path: Path,
    digest: str,
    role: str,
    ordinal: int,
    args: argparse.Namespace,
    campaign_dir: Path,
) -> dict[str, Any]:
    print(f"\n=== {role} run {ordinal}/{args.runs}")
    print(f"artifact: {path}")
    print(f"sha256:   {digest}")
    started = utc_now()

    # The phase loaded this SHA before entering the run loop.  Rebooting here
    # makes the firmware emit a fresh run against that already-loaded image.
    reboot_output = reboot_rp2350(args.picotool)
    if reboot_output.strip():
        print(reboot_output.rstrip())
    time.sleep(args.reboot_settle)
    resolved_port = wait_for_port(args.port, args.reenumerate_timeout)
    print(f"CDC:      {args.port} -> {resolved_port}")

    safe_role = re.sub(r"[^A-Za-z0-9_.-]", "_", role)
    log_path = campaign_dir / "logs" / f"{safe_role}_r{ordinal:02d}_{digest[:16]}.log"
    parsed = capture_one(resolved_port, args.baud, args.capture_timeout, log_path)
    parsed.update(
        {
            "role": role,
            "ordinal": ordinal,
            "started_utc": started,
            "finished_utc": utc_now(),
            "loaded_path": str(path),
            "sha256": digest,
        }
    )
    if parsed["failing_cases"]:
        print("failing words:")
        for case in parsed["failing_cases"]:
            result = case["result"]
            print(
                f"  {case['name']}: A={result['A']} B={result['B']} "
                f"C={result['C']} D={result['D']}"
            )
    return parsed


def run_phase(
    *,
    path: Path,
    digest: str,
    role: str,
    summary: dict[str, Any],
    summary_path: Path,
    campaign_dir: Path,
    args: argparse.Namespace,
) -> bool:
    print(f"\n=== {role} load")
    print(f"artifact: {path}")
    print(f"sha256:   {digest}")
    try:
        if args.dirtyjtag_usb_id:
            reset_output = reset_dirtyjtag(
                args.usbreset, args.dirtyjtag_usb_id, args.jtag_reset_settle
            )
            print(reset_output.rstrip())
        load_bitstream(path, args.loader, args.jtag_hz)
    except Exception as error:
        execution = {
            "role": role,
            "ordinal": 0,
            "stage": "load_bitstream",
            "started_utc": utc_now(),
            "finished_utc": utc_now(),
            "loaded_path": str(path),
            "sha256": digest,
            "verdict": "ERROR",
            "error": str(error),
            "cases": [],
            "failing_cases": [],
        }
        summary["bitstreams"][digest]["executions"].append(execution)
        checkpoint(summary_path, summary)
        raise CampaignError(f"{role} load: {error}") from error
    print("FPGA load: OK")

    all_pass = True
    for ordinal in range(1, args.runs + 1):
        try:
            execution = execute_run(
                path=path,
                digest=digest,
                role=role,
                ordinal=ordinal,
                args=args,
                campaign_dir=campaign_dir,
            )
        except Exception as error:
            execution = {
                "role": role,
                "ordinal": ordinal,
                "started_utc": utc_now(),
                "finished_utc": utc_now(),
                "loaded_path": str(path),
                "sha256": digest,
                "verdict": "ERROR",
                "error": str(error),
                "cases": [],
                "failing_cases": [],
            }
            print(f"ERROR: {error}", file=sys.stderr)
            summary["bitstreams"][digest]["executions"].append(execution)
            checkpoint(summary_path, summary)
            raise CampaignError(f"{role} run {ordinal}: {error}") from error
        summary["bitstreams"][digest]["executions"].append(execution)
        all_pass = all_pass and execution["verdict"] == "PASS"
        checkpoint(summary_path, summary)
    return all_pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bitstreams", nargs="+", type=Path, help="candidate .bit files")
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("-n", "--runs", type=int, default=10, help="runs per phase (minimum 10)")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--port", type=Path, default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--capture-timeout", type=float, default=45.0)
    parser.add_argument("--reboot-settle", type=float, default=1.0)
    parser.add_argument("--reenumerate-timeout", type=float, default=20.0)
    parser.add_argument("--jtag-hz", type=int, default=1_000_000)
    parser.add_argument("--loader", default="openFPGALoader")
    parser.add_argument("--picotool", default="picotool")
    parser.add_argument(
        "--dirtyjtag-usb-id",
        default=DEFAULT_DIRTYJTAG_USB_ID,
        help=(
            "usbreset VID:PID to reset before each bitstream load "
            f"(default {DEFAULT_DIRTYJTAG_USB_ID}); pass '' to disable. "
            "On by default because the adapter stalls under sustained load "
            "and silently voids campaigns"
        ),
    )
    parser.add_argument("--usbreset", default="usbreset")
    parser.add_argument("--jtag-reset-settle", type=float, default=0.5)
    args = parser.parse_args(argv)
    if args.runs < MIN_RUNS:
        parser.error(f"--runs must be at least {MIN_RUNS}; a single run is not a result")
    if args.baud <= 0 or args.jtag_hz <= 0:
        parser.error("--baud and --jtag-hz must be positive")
    if args.reboot_settle < 0 or args.reenumerate_timeout <= 0:
        parser.error("reboot settle must be nonnegative and re-enumeration timeout positive")
    if args.jtag_reset_settle < 0:
        parser.error("JTAG reset settle must be nonnegative")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    canonical_path, canonical_sha = identify(args.canonical)
    candidates = [identify(path) for path in args.bitstreams]
    if any(digest == canonical_sha for _, digest in candidates):
        raise CampaignError(
            "canonical bitstream must not also be listed as a candidate; controls are automatic"
        )

    campaign_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    campaign_dir = args.output_root.expanduser().resolve() / campaign_id
    summary_path = campaign_dir / "summary.json"
    summary: dict[str, Any] = {
        "schema": "spu.pade-bench-campaign.v1",
        "campaign_id": campaign_id,
        "started_utc": utc_now(),
        "updated_utc": utc_now(),
        "runs_per_phase": args.runs,
        "dirtyjtag_usb_id": args.dirtyjtag_usb_id,
        "sequence": [
            "load_bitstream_once_per_phase",
            "for_each_run: reboot_rp2350",
            "for_each_run: capture",
        ],
        "canonical_sha256": canonical_sha,
        "status": "running",
        "valid": None,
        "void_reason": None,
        "bitstreams": {},
    }
    add_artifact(summary, canonical_path, canonical_sha)
    for path, digest in candidates:
        add_artifact(summary, path, digest)
    checkpoint(summary_path, summary)
    print(f"summary: {summary_path}")

    try:
        start_ok = run_phase(
            path=canonical_path,
            digest=canonical_sha,
            role="control-start",
            summary=summary,
            summary_path=summary_path,
            campaign_dir=campaign_dir,
            args=args,
        )
        if not start_ok:
            summary["status"] = "void"
            summary["valid"] = False
            summary["void_reason"] = "canonical start control did not pass every run"
            checkpoint(summary_path, summary)
            print(f"CAMPAIGN VOID: {summary['void_reason']}", file=sys.stderr)
            return 2

        for index, (path, digest) in enumerate(candidates, start=1):
            run_phase(
                path=path,
                digest=digest,
                role=f"candidate-{index:02d}-{path.stem}",
                summary=summary,
                summary_path=summary_path,
                campaign_dir=campaign_dir,
                args=args,
            )

        end_ok = run_phase(
            path=canonical_path,
            digest=canonical_sha,
            role="control-end",
            summary=summary,
            summary_path=summary_path,
            campaign_dir=campaign_dir,
            args=args,
        )
    except Exception as error:
        summary["status"] = "void"
        summary["valid"] = False
        summary["void_reason"] = f"infrastructure error: {error}"
        checkpoint(summary_path, summary)
        print(f"CAMPAIGN VOID: {summary['void_reason']}", file=sys.stderr)
        return 2
    summary["status"] = "complete" if end_ok else "void"
    summary["valid"] = end_ok
    if not end_ok:
        summary["void_reason"] = "canonical end control did not pass every run"
    checkpoint(summary_path, summary)

    print("\nPass rates:")
    for digest, artifact in summary["bitstreams"].items():
        if artifact["runs"]:
            print(
                f"  {digest}: {artifact['passes']}/{artifact['runs']} "
                f"({artifact['pass_rate']:.1%}); errors={artifact['errors']}"
            )
        else:
            print(f"  {digest}: unmeasured; errors={artifact['errors']}")
    if not end_ok:
        print(f"CAMPAIGN VOID: {summary['void_reason']}", file=sys.stderr)
        return 2
    print(f"CAMPAIGN VALID: {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CampaignError, FileNotFoundError, subprocess.TimeoutExpired) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
