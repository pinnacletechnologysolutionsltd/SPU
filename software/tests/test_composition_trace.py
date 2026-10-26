#!/usr/bin/env python3
"""test_composition_trace.py — oracle-backed composition trace.

The second precondition in docs/SERVICE_COMPOSITION_POLICY.md §5, which shared
datapaths are deferred behind. Hardware-free.

It is a *trace*, not merely a unit test: it produces a recorded sequence hitting
all three outcomes, and checks the two properties the policy actually rests on.

  1. All three outcomes appear. A policy that only ever emits `accept` is
     untested, however green the run looks.
  2. BMU evidence survives composition byte-for-byte, and is *identical* to
     what the classifier emits when composition is not applied at all. This is
     the check that rule 3.1 holds rather than being asserted.

Run: python3 software/tests/test_composition_trace.py
"""

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))

from lib.composition_policy import (  # noqa: E402
    CompositionError,
    Outcome,
    Verdict,
    compose,
    phslk_verdict,
)
from spu_host.som1 import SOM1Result, encode_som1_frame, parse_som1_frame  # noqa: E402

FLAG_VALID = 0x01
FLAG_BUSY = 0x02
FLAG_SECOND = 0x04
FLAG_AMBIGUOUS = 0x08
FLAG_MAP_VALID = 0x10

checks = 0
failures = []


def check(cond, what):
    global checks
    checks += 1
    if not cond:
        failures.append(what)


def frame(flags=FLAG_VALID | FLAG_SECOND | FLAG_MAP_VALID, error=0, gen=1,
          winner=3, runner_up=7, label=2, best=0x0000000200000001,
          second=0x0000000900000004):
    """A SOM1 frame. Defaults are a clean, unambiguous, valid classification."""
    return encode_som1_frame(SOM1Result(
        version=1, flags=flags, error=error,
        map_generation=11, result_generation=gen,
        winner=winner, runner_up=runner_up, label=label,
        best_q=best, second_q=second,
        confidence_gap=second - best,
    ))


# --- the trace ------------------------------------------------------------
# Each step: a described condition, the frame, and the algebra verdict.
STEPS = [
    ("clean decision, algebra concurs",
     frame(gen=1), Verdict.CONCUR, Outcome.ACCEPT),
    ("clean decision, algebra dissents -- BMU must survive intact",
     frame(gen=2), Verdict.DISSENT, Outcome.HOLD),
    ("classifier reports ambiguous -- algebra cannot break the tie",
     frame(flags=FLAG_VALID | FLAG_SECOND | FLAG_MAP_VALID | FLAG_AMBIGUOUS, gen=3),
     Verdict.CONCUR, Outcome.ESCALATE),
    ("result not valid",
     frame(flags=FLAG_MAP_VALID, gen=4), Verdict.CONCUR, Outcome.ESCALATE),
    ("classifier error code set",
     frame(error=5, gen=5), Verdict.CONCUR, Outcome.ESCALATE),
    ("map not valid",
     frame(flags=FLAG_VALID | FLAG_SECOND, gen=6), Verdict.CONCUR, Outcome.ESCALATE),
    ("algebra service produced no verdict",
     frame(gen=7), Verdict.UNAVAILABLE, Outcome.HOLD),
    ("clean decision, algebra concurs again",
     frame(gen=8), Verdict.CONCUR, Outcome.ACCEPT),
]

trace = []
for desc, raw, verdict, expected in STEPS:
    outcome, forwarded, reason = compose(raw, verdict)
    check(outcome is expected,
          "%s: expected %s got %s" % (desc, expected.value, outcome.value))
    # Rule 3.1 -- identity, not equality: the caller forwards the very bytes
    # it was handed, so no re-encoded lookalike can slip through.
    check(forwarded is raw, "%s: forwarded frame is not the original object" % desc)
    check(forwarded == raw, "%s: forwarded frame bytes differ" % desc)
    trace.append({
        "condition": desc,
        "som1_frame_hex": raw.hex(),
        "algebra_verdict": verdict.value,
        "outcome": outcome.value,
        "reason": reason,
    })

# 1. All three outcomes must appear, or the policy is untested.
seen = {step["outcome"] for step in trace}
check(seen == {"accept", "hold", "escalate"},
      "trace does not exercise all three outcomes: %s" % sorted(seen))

# 2. Composed frames are byte-identical to uncomposed classifier output.
for desc, raw, verdict, _ in STEPS:
    _, forwarded, _ = compose(raw, verdict)
    check(forwarded == raw,
          "%s: composed frame differs from uncomposed classifier output" % desc)

# 3. The negative case in full: on dissent, every field of the BMU decision
#    survives -- not just the byte string, but the parsed evidence.
raw = frame(gen=42, winner=5, runner_up=9, label=1)
before = parse_som1_frame(raw)
outcome, forwarded, _ = compose(raw, Verdict.DISSENT)
after = parse_som1_frame(forwarded)
check(outcome is Outcome.HOLD, "dissent did not produce hold")
for field in ("winner", "runner_up", "label", "best_q", "second_q",
              "confidence_gap", "result_generation", "flags", "error"):
    check(getattr(before, field) == getattr(after, field),
          "dissent altered SOM1 field %s" % field)

# 4. PHSLK verdicts by exact cross multiplication, zero tolerance.
check(phslk_verdict(3, 4, 6, 8) is Verdict.CONCUR, "3/4 vs 6/8 should concur")
check(phslk_verdict(3, 4, 5, 8) is Verdict.DISSENT, "3/4 vs 5/8 should dissent")
check(phslk_verdict(1, 0, 1, 1) is Verdict.UNAVAILABLE,
      "zero denominator must be unavailable, not a dissent")
check(phslk_verdict(1, 1, 1, 0) is Verdict.UNAVAILABLE,
      "zero denominator must be unavailable, not a dissent")

# 5. A verdict must be a Verdict. A bare string is the likely mistake and it
#    must fail loudly rather than compare unequal and silently hold.
try:
    compose(frame(), "concur")
    check(False, "a bare string verdict was accepted")
except CompositionError:
    check(True, "bare string verdict rejected")

# --- exhaustive golden vectors for RTL parity ----------------------------
# Case agreement is not equivalence. Enumerate the entire meaningful input
# space and let hardware/tests/spu13/spu13_composition_policy_tb.v check every
# point, so the RTL cannot drift from this oracle in a corner nobody wrote a
# case for. Flag bits 5-7 are reserved and rejected by the encoder, so the
# space is 32 flag patterns x a few error codes x every verdict.
REASON_CODE = {
    "algebra verdict concurs": 0,
    "algebra verdict dissents": 1,
    "algebra verdict unavailable": 2,
    "som1 result not valid": 3,
    "som1 map not valid": 5,
    "som1 classifier busy": 6,
    "som1 reported ambiguous": 7,
}
VERDICT_CODE = {Verdict.CONCUR: 0, Verdict.DISSENT: 1, Verdict.UNAVAILABLE: 2}
OUTCOME_CODE = {Outcome.ACCEPT: 0, Outcome.HOLD: 1, Outcome.ESCALATE: 2}

golden = []
for flags in range(0x20):            # bits 0-4; 5-7 reserved
    for err in (0, 1, 5, 255):
        for v in (Verdict.CONCUR, Verdict.DISSENT, Verdict.UNAVAILABLE):
            raw = frame(flags=flags, error=err, gen=1)
            outcome, _, reason = compose(raw, v)
            code = 4 if reason.startswith("som1 error code") else REASON_CODE[reason]
            word = (flags << 15) | (err << 7) | (VERDICT_CODE[v] << 5) \
                   | (OUTCOME_CODE[outcome] << 3) | code
            golden.append("%06x" % word)

gold_path = REPO / "hardware" / "tests" / "spu13" / "composition_policy_golden.mem"
gold_path.write_text("\n".join(golden) + "\n")
check(len(golden) == 0x20 * 4 * 3, "golden vector count wrong: %d" % len(golden))
check(len({g for g in golden}) > 1, "golden vectors are degenerate")

# --- emit the trace artifact ---------------------------------------------
out = REPO / "build" / "composition_trace"
out.mkdir(parents=True, exist_ok=True)
(out / "composition_trace_v1.json").write_text(
    json.dumps({"policy": "docs/SERVICE_COMPOSITION_POLICY.md",
                "steps": trace}, indent=2) + "\n")

print("composition trace: %d checks, %d failed" % (checks, len(failures)))
for f in failures:
    print("  FAIL", f)
print("  outcomes exercised:", ", ".join(sorted(seen)))
print("  trace written:", (out / "composition_trace_v1.json").relative_to(REPO))
print("  golden vectors:", len(golden), "->", gold_path.relative_to(REPO))
print("PASS" if not failures else "FAIL")
sys.exit(1 if failures else 0)
