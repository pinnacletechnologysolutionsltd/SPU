"""Bounded arithmetic, schedule and proposed handshake qualification; no RTL claim."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))
from lib.a31_field import a31_mul, a31_tower_inv
from lib.jet_ring import jet_mul
from lib.jet_ring_N import jet_mul_N
from sparse_jet_model import count, execute, result_tag, schedule, validate, validate_tag, windows
from sparse_jet_protocol import Protocol, check_trace
from sparse_jet_protocol_controls import drive, run_controls
from sparse_jet_reference import P, ZERO, dense, multiply, pairs


def rejects(fn, error=ValueError):
    try:
        fn()
    except error:
        return
    raise AssertionError("negative control did not reject")


def check_count(actual, expected):
    assert actual == expected, "multiply count mismatch"



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.report and args.report.exists():
        raise FileExistsError(args.report)
    rng, arithmetic, protocols, negatives = random.Random(130410), 0, 0, 0
    basis = [tuple(int(i == j) for i in range(4)) for j in range(4)]
    for a in basis + [(P - 1,) * 4, ZERO]:
        for b in basis + [(P - 1,) * 4, ZERO]:
            assert a31_mul(a, b) == multiply(a, b)
            arithmetic += 1
    s = pow(15, (P + 1) // 4, P)
    u, v = (s, 0, 0, 1), (s, 0, 0, P - 1)
    assert u != ZERO and v != ZERO and multiply(u, v) == ZERO
    assert a31_tower_inv(u)[1] and a31_tower_inv(v)[1]
    for n in (2, 4):
        for at in windows(n):
            for bt in windows(n):
                def values(tag):
                    return tuple(tuple(rng.randrange(P) for _ in range(4)) if tag[0] <= i <= tag[1] else ZERO for i in range(n + 1))
                a, b = values(at), values(bt)
                assert schedule(n, at, bt) == pairs(n, at, bt)
                assert count(n, at, bt) == len(pairs(n, at, bt))
                for mul in (True, False):
                    got, tag, flag = execute(n, a, b, at, bt, mul)
                    want = dense(a, b) if mul else tuple(tuple((x + y) % P for x, y in zip(c, d)) for c, d in zip(a, b))
                    assert got == want and flag is False
                    if mul:
                        nonempty = at != (n + 1, 0) and bt != (n + 1, 0) and at[0] + bt[0] <= n
                        expected_tag = (at[0] + bt[0], min(n, at[1] + bt[1])) if nonempty else (n + 1, 0)
                        assert jet_mul_N(a, b, n) == want
                        if n == 2:
                            assert jet_mul(a, b) == want
                    else:
                        occupied = [i for t in (at, bt) for i in range(t[0], t[1] + 1)]
                        expected_tag = (min(occupied), max(occupied)) if occupied else (n + 1, 0)
                    assert tag == expected_tag
                    validate(n, got, tag)
                    for latency in (1, 3, 5):
                        drive(n, (a, b, at, bt, mul), latency)
                        protocols += 1
                    arithmetic += 1
        # Nonunits and cancellation are valid, and cannot sharpen dense tags.
        a, b = (u,) + (ZERO,) * n, (v,) + (ZERO,) * n
        assert execute(n, a, b, (0, n), (0, n)) == ((ZERO,) * (n + 1), (0, n), False)
        assert count(n, (0, n), (0, n)) == (n + 1) * (n + 2) // 2
        zero = (ZERO,) * (n + 1)
        zero_trace = drive(n, (zero, zero, (0, n), (0, n), True), 1)
        assert len([e for e in zero_trace if e["issue"]]) == count(n, (0, n), (0, n))
        protocols += 1
        rejects(lambda: check_count(sum(e["issue"] is not None for e in zero_trace), 0), AssertionError)
        negatives += 1
        assert execute(n, a, tuple(tuple(-x % P for x in row) for row in a), (0, n), (0, n), False)[0] == (ZERO,) * (n + 1)
        request = (a, b, (0, n), (0, n), True)
        for state in ("ISSUE", "WAIT", "RETIRE"):
            drive(n, request, 3, state)
            protocols += 1
        trace = drive(n, request, 3)
        for change in ("early_busy", "duplicate_done", "missing_issue", "bad_result"):
            bad = copy.deepcopy(trace)
            if change == "early_busy": bad[1]["busy"] = False
            elif change == "duplicate_done": bad.append(copy.deepcopy(bad[-1]))
            elif change == "missing_issue": next(e for e in bad if e["issue"] is not None)["issue"] = None
            else: bad[-1]["result"] = (ZERO,) * (n + 1); bad[-1]["tag"] = (n + 1, 0)
            rejects(lambda: check_trace(bad, pairs(n, (0, n), (0, n)), dense(a, b), (0, n)), AssertionError)
            negatives += 1
        model = Protocol(n)
        model.tick(start=request)
        model.tick()
        for _ in range(100):
            assert model.tick()["busy"]  # No response: never claim completion.
        for tag in ((-1, 0), (0, n + 1), (n, 0), (n + 2, 0), (True, 0)):
            rejects(lambda: validate_tag(n, tag)); negatives += 1
        rejects(lambda: validate(n, a, (n + 1, 0))); negatives += 1
        rejects(lambda: validate(n, ((P, 0, 0, 0),) + (ZERO,) * n, (0, n))); negatives += 1
    assert count(4, (1, 4), (1, 4)) == 6 and count(4, (0, 0), (1, 4)) == 4
    assert (15 + 1).bit_length() == 5 and 16 + 16 < 1 << 6
    protocol_controls = run_controls()
    report = {"status": "FOCUSED_PASS", "orders": [2, 4], "window_pairs": 305,
              "arithmetic_cases": arithmetic, "protocol_traces": protocols, "negative_controls": negatives,
              "protocol_boundary_controls": protocol_controls,
              "tag_width_boundary": "N15 requires 5-bit tags, 6-bit sum",
              "classification": {"software": "matching tested contract", "sparse_RTL": "unsupported/not implemented",
                                 "dense_RTL_completion": "conflicting existing busy gap; unchanged",
                                 "fabric_reset": "requires shared cancellation/drain; no stale-response guarantee in new WAIT"},
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(Path(__file__).parent.glob("*sparse_jet*.py"))}}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
