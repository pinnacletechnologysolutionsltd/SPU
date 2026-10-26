#!/usr/bin/env python3
"""Source-level Candidate A Surd cycle reference; not a scheduler model."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "fixtures/spu_fabric_0/manifest.json"
PROFILES = ("isolated", "burst_synthetic", "steady_synthetic")
RTL_SHA256 = {
    "hardware/rtl/math/surd_smul_unit.v": "0cebd08aec2cd9ea6603ae655b9a15d65d9651eca958e1935137bd6deb04fdaa",
    "hardware/rtl/math/surd_normalize_unit.v": "4d43e03f3745326a3f7d26fcf7a34219c8bc0ba1a4826a568eb3c74ab82291fa",
    "hardware/rtl/math/surd_binary_gcd3.v": "e994552b50f34017b176d91303ac6c85774748d64d4014755d0979d6fcd3097c",
    "hardware/rtl/math/surd_exact_quotient.v": "2a78246d9ab13d439ee0be88b57dd58029d1d5ed0e77fcd61d1bac4837fd15cd",
}


def gcd3_cycles(a: int, b: int, denominator: int, n: int) -> tuple[int, int]:
    """Return start-to-done edge distance and maximum updates in either phase."""
    mask = (1 << n) - 1
    u, v, original_d = a & mask, b & mask, denominator & mask
    max_iter = n * n + 3 * n + 1
    state = "INIT_AB"
    edge = scale = iteration = phase_updates = max_updates = 0
    while edge < 4 * n + 20:
        edge += 1
        done = False
        if state == "INIT_AB":
            scale = iteration = phase_updates = 0
            if u == 0:
                u, v, state = v, original_d, "INIT_GD"
            elif v == 0:
                v, state = original_d, "INIT_GD"
            else:
                state = "COMMON_AB" if not (u & 1 or v & 1) else "LOOP_AB"
        elif state in ("COMMON_AB", "COMMON_GD"):
            if u & 1 or v & 1:
                state = "LOOP_AB" if state == "COMMON_AB" else "LOOP_GD"
            elif iteration == max_iter:
                raise AssertionError("GCD guard reached")
            else:
                u >>= 1
                v >>= 1
                scale += 1
                iteration += 1
                phase_updates += 1
        elif state == "LOOP_AB":
            if u == v:
                u, v = (u << scale) & mask, original_d
                scale = iteration = phase_updates = 0
                state = "INIT_GD"
            elif u == 0:
                u, v, state = v, original_d, "INIT_GD"
            elif v == 0:
                v, state = original_d, "INIT_GD"
            elif iteration == max_iter:
                raise AssertionError("GCD guard reached")
            elif not (u & 1):
                u >>= 1
                iteration += 1
                phase_updates += 1
            elif not (v & 1):
                v >>= 1
                iteration += 1
                phase_updates += 1
            elif u > v:
                u = (u - v) >> 1
                iteration += 1
                phase_updates += 1
            else:
                v = (v - u) >> 1
                iteration += 1
                phase_updates += 1
        elif state == "INIT_GD":
            scale = phase_updates = 0
            if u == 0 or original_d == 0:
                done = True
            else:
                v = original_d
                iteration = 0
                state = "COMMON_GD" if not (u & 1 or original_d & 1) else "LOOP_GD"
        elif state == "LOOP_GD":
            if u == v or u == 0 or v == 0:
                done = True
            elif iteration == max_iter:
                raise AssertionError("GCD guard reached")
            elif not (u & 1):
                u >>= 1
                iteration += 1
                phase_updates += 1
            elif not (v & 1):
                v >>= 1
                iteration += 1
                phase_updates += 1
            elif u > v:
                u = (u - v) >> 1
                iteration += 1
                phase_updates += 1
            else:
                v = (v - u) >> 1
                iteration += 1
                phase_updates += 1
        else:
            raise AssertionError(f"unknown state {state}")
        max_updates = max(max_updates, phase_updates)
        if phase_updates > 2 * n:
            raise AssertionError("bit-length descent bound violated")
        if done:
            if edge > 4 * n + 6:
                raise AssertionError("GCD exceeded the derived domain bound")
            return edge, max_updates
    raise AssertionError("GCD did not terminate within the derived bound")


def operation_latency(record: dict, width: int) -> tuple[int, int]:
    expected = record["expected"]
    a, b, d, c, e, f = record["operands"]
    if expected["invalid"]:
        if d != 0 and f != 0:
            raise AssertionError("invalid status disagrees with zero-denominator rule")
        return 0, 0
    if d == 0 or f == 0:
        raise AssertionError("zero denominator was not marked invalid")
    if not expected["request_normalization"]:
        raw_a, raw_b, raw_d = expected["raw"]
        lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
        if not (lo <= raw_a <= hi and lo <= raw_b <= hi and 0 <= raw_d < (1 << width)):
            raise AssertionError("raw-fit status disagrees with defined output width")
        return 1, 0
    raw_a, raw_b, raw_d = expected["raw"]
    if raw_d == 0:
        raise AssertionError("valid normalization case has zero raw denominator")
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    if lo <= raw_a <= hi and lo <= raw_b <= hi and raw_d < (1 << width):
        raise AssertionError("normalization request disagrees with raw-fit status")
    if raw_a == 0 and raw_b == 0:
        return 3, 0  # normalizer zero-numerator bypass plus caller return
    n = 2 * width + 2
    gcd_latency, _ = gcd3_cycles(abs(raw_a), abs(raw_b), raw_d, n)
    return gcd_latency + n + 7, gcd_latency


def main() -> None:
    for relative, expected in RTL_SHA256.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"RTL source hash mismatch: {relative}")
    manifest = json.loads(MANIFEST.read_text())
    profile_rows = {}
    trace_hashes = {}
    for profile in PROFILES:
        info = manifest["traces"][profile]
        path = MANIFEST.parent / info["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != info["sha256"]:
            raise SystemExit(f"{profile} trace hash mismatch")
        with gzip.open(path, "rt") as stream:
            profile_rows[profile] = [json.loads(line) for line in stream]
        trace_hashes[profile] = digest
    result = {"trace_sha256": trace_hashes, "widths": {}}
    for width in (32, 64):
        cases = {
            profile: [r for r in profile_rows[profile]
                      if r["client"] == f"surd_w{width}"]
            for profile in PROFILES
        }
        for profile in PROFILES:
            want = manifest["traces"][profile]["client_counts"][f"surd_w{width}"]
            if len(cases[profile]) != want:
                raise SystemExit(f"{profile} W{width} fixture count mismatch")
        signatures = {
            profile: {
                r["operation_id"]: (r["client"], r["operands"], r["expected"])
                for r in cases[profile]
            }
            for profile in PROFILES
        }
        if any(signatures[p] != signatures[PROFILES[0]] for p in PROFILES[1:]):
            raise SystemExit(f"W{width} source cases differ across profiles")
        source_cases = cases[PROFILES[0]]
        measured = [(operation_latency(r, width), r["operation_id"]) for r in source_cases]
        (latency, gcd_latency), operation_id = max(measured)
        n = 2 * width + 2
        result["widths"][str(width)] = {
            "source_case_count": len(source_cases),
            "profiles_verified": list(PROFILES),
            "normalization_count": sum(r["expected"]["request_normalization"] for r in source_cases),
            "invalid_count": sum(r["expected"]["invalid"] for r in source_cases),
            "fixture_max_latency_cycles": latency,
            "fixture_max_gcd_latency_cycles": gcd_latency,
            "fixture_max_operation_id": operation_id,
            "domain_gcd_bound_cycles": 4 * n + 6,
            "domain_smul_bound_cycles": 5 * n + 13,
            "max_iter_guard": n * n + 3 * n + 1,
            "quotient_iterations": n,
        }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
