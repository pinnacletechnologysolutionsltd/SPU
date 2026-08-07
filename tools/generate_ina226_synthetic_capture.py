#!/usr/bin/env python3
"""Generate a complete synthetic 30-session INA226 capture set.

Purpose: exercise the whole ingestion chain — seal, verify, run, replay
byte-comparison — without a bench, so a regression in the pipeline is caught
before it wastes physical capture time. It is also the only end-to-end test of
the v2 stall exemption: the generated `current_limited_stall` sessions carry a
collapsed rail that **every** v1 contract row would have rejected.

The profiles mirror the real bench measured 2026-08-06 (see
`docs/INA226_SESSION_HANDOFF.md`):

    normal          ~98 mA,  bus ~3005 mV   checked window
    elevated_load  ~241 mA,  bus ~2915 mV   checked window
    stall          ~307 mA,  bus ~1490 mV   EXEMPT under v2, fails v1

Usage — writes only inside its own output directory, never the real manifest:

    D=build/ina226_synth_v2
    python3 tools/generate_ina226_synthetic_capture.py --out $D/captures
    python3 tools/ina226_capture_pipeline.py init $D/manifest.json \
        --nominal-bus-mv 3000 --probe synthetic_v2_fixture \
        --actuator-model synthetic-v2-fixture \
        --actuator-continuous-ma 320 --supply-limit-ma 320
    python3 tools/ina226_capture_pipeline.py seal   $D/manifest.json
    python3 tools/ina226_capture_pipeline.py verify $D/manifest.json
    python3 tools/ina226_capture_pipeline.py run    $D/manifest.json --output $D/out_a

Expected on the frozen seed: verify reports 30 sessions / 120 windows, the run
reports `som_balanced=100.00% replay_eligible=True`, and two runs to different
directories produce a byte-identical result JSON.

Note that every model scores 100% on this fixture and the superiority gate
therefore reports False — a plain threshold ties the SOM. That is the correct
behaviour on separable data, not a defect, and it is what the physical capture
should be expected to reproduce.

Synthetic data proves the machinery, never the science: the samples are drawn
from the class profiles, so of course they separate.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

CLASSES = ("normal", "elevated_load", "current_limited_stall")

# class -> (mean current mA, current jitter mA, bus mV, bus jitter mV)
PROFILE = {
    "normal": (98.3, 11.0, 3005, 12),
    "elevated_load": (240.8, 20.0, 2915, 20),
    "current_limited_stall": (307.4, 1.0, 1490, 12),
}

ROWS = 145  # a 1.4 s capture at 100 Hz, matching the real bench procedure
HEADER = "host_iso,probe,phase,t_ms,bus_mV,shunt_uV,current_uA"


def expected_class_order(block: int) -> tuple[str, ...]:
    """Block b uses the class order rotated left by b mod 3 (contract `task`)."""
    shift = block % 3
    return CLASSES[shift:] + CLASSES[:shift]


def session_rows(class_name: str, block: int, probe: str,
                 rng: random.Random) -> list[str]:
    mean_mA, jitter_mA, bus_mV, bus_jitter = PROFILE[class_name]
    lines = [HEADER]
    t_ms = 1000 + block * 100_000
    for index in range(ROWS):
        # The logger derives both current and shunt columns from one raw count,
        # and the validator checks they agree, so derive them the same way.
        raw = int((mean_mA + rng.uniform(-jitter_mA, jitter_mA)) * 1000) // 25
        current_uA = raw * 25
        shunt_uV = raw * 5 // 2
        bus = bus_mV + rng.randint(-bus_jitter, bus_jitter)
        t_ms += rng.choice((9, 10, 10, 10, 11))  # inside the 8..12 ms gate
        iso = "2026-08-07T%02d:%02d:%02d.%03d" % (
            9 + block // 4, (block * 7 + index) % 60, index % 60,
            (index * 7) % 1000)
        lines.append(
            f"{iso},{probe},{class_name},{t_ms},{bus},{shunt_uV},{current_uA}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="output captures/ directory")
    parser.add_argument("--probe", default="synthetic_v2_fixture",
                        help="must match the manifest probe exactly")
    parser.add_argument("--seed", type=int, default=20260807,
                        help="frozen by default so the result hash is stable")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    written = 0
    for block in range(10):
        for class_name in expected_class_order(block):
            target = out / f"b{block:02d}-{class_name}.csv"
            target.write_text(
                "\n".join(session_rows(class_name, block, args.probe, rng)) + "\n",
                encoding="ascii",
            )
            written += 1
    print(f"wrote {written} synthetic sessions to {out}")


if __name__ == "__main__":
    main()
