#!/usr/bin/env python3
"""Run the frozen fold-0 Tang parity/latency physical acceptance gate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from rp2040_flash_pmod import PosixSerial
from software.lib.rational_som import RationalSurd
from software.lib.spu4_som_probe_client import encode_query
from software.lib.spu4_som_probe_parser import parse_line

FREEZE_SHA256 = "6dcbb8e73597e0172531eca15baf3c2d666827e056c1eede45e59ab019188de6"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", required=True)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--freeze", type=Path,
                    default=ROOT / "docs/bench_captures/2026-09-08_spu4_ina226_freeze.json")
    ns = ap.parse_args()
    if ns.output.exists():
        raise ValueError("refusing to overwrite acceptance evidence")
    encoded = ns.freeze.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != FREEZE_SHA256:
        raise ValueError("frozen benchmark fixture hash changed: STOP")
    cases = json.loads(encoded)["folds"][0]["cases"]
    if len(cases) != 24:
        raise ValueError("fold 0 is not the frozen 24-case set: STOP")

    results = []
    failure = None
    uart = PosixSerial(ns.port, 115200, timeout=0.25)
    try:
        uart.reset_input_buffer()
        for index, case in enumerate(cases):
            features = [RationalSurd(v, 0) for v in case["features"]]
            uart.write(encode_query(features))
            uart.flush()
            deadline = time.monotonic() + 5.0
            response = None
            raw_lines = []
            while time.monotonic() < deadline:
                raw = uart.readline()
                if not raw:
                    continue
                raw_lines.append(raw.hex())
                parsed = parse_line(raw.decode("ascii", "replace").lstrip("\0"))
                if parsed is not None and parsed.status_char in ("D", "F"):
                    response = parsed
                    break
            result = {"case": index, "features": case["features"],
                      "expected_node": case["best"],
                      "expected_distance": case["distance"],
                      "raw_lines_hex": raw_lines}
            if response is None:
                failure = f"case {index}: no terminal response"
            else:
                result.update(status_char=response.status_char,
                              node=response.best_node,
                              distance=response.best_quadrance,
                              status=response.status,
                              latency_cycles=response.latency,
                              id=response.id)
                if response.status_char != "D":
                    failure = f"case {index}: invalid response {response.status_char}"
                elif (response.best_node, response.best_quadrance) != (
                        case["best"], case["distance"]):
                    failure = f"case {index}: classifier parity mismatch"
                elif response.latency != 6:
                    failure = f"case {index}: latency {response.latency}, expected fresh 6"
            results.append(result)
            if failure:
                break
    finally:
        uart.close()

    record = {
        "format": "SPU4_INA226_BENCH25_COMPLETION_ARM_ACCEPTANCE_V1",
        "freeze_sha256": FREEZE_SHA256,
        "port": ns.port,
        "baud": 115200,
        "cases_required": 24,
        "cases_completed": len(results),
        "results": results,
        "failure": failure,
        "result": "PASS" if failure is None and len(results) == 24 else "STOP",
    }
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    with ns.output.open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    if failure:
        print(f"STOP: {failure}")
        return 1
    print("PASS: 24/24 exact parity, 0 invalid, every L=006")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
