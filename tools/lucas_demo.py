#!/usr/bin/env python3
"""lucas_demo.py — first-hour demo for the LUCAS spin (Wukong Artix-7).

Two acts, per docs/SPIN_CATALOG.md's first-hour story for LUCAS:

1. The four silicon-proven Z[phi]/L_521 sidecar ops (PSCALE, PCHIRAL,
   PMUL, PINV), driven with the exact golden vectors from
   hardware/rp2350/rp2350_lucas_j11_smoke.c (`LUCAS_J11: PASS`), checked
   against an inline exact-integer oracle rather than hardcoded answers.

2. The zero-drift side-by-side: a phi-scaling feedback loop
   (a,b) -> phi*(a + b*phi) = (b, a+b) mod 521, where each step's
   hardware result is fed back as the next step's operand. The same
   recurrence runs in exact Python integers (ground truth) and in IEEE-754
   double precision. The doubles silently lose integer exactness once the
   unreduced coefficients pass 2^53 (around step 79 -- Fibonacci growth);
   the hardware matches the exact integers bit-for-bit at every step, for
   as many steps as you care to wait for.

Wiring: RP2350 southbridge -> Wukong J11 (see AGENTS.md's J11 pin-damage
notes -- confirm the bottom-row remap before connecting). Board must be
flashed with the LUCAS spin: `bash hardware/boards/artix7/build_a7.sh
100t lucas synth/pnr/pack`, then SRAM-loaded.

Usage:
    python3 tools/lucas_demo.py --port /dev/ttyACM0 [--steps 200]

Instruction layout (docs/CURRENT_STATUS.md "Lucas Sidecar" +
hardware/rtl/core/spu13/spu13_lucas_sidecar.v):
    [63:56] opcode 0xD0-0xD3   [55:52] QR lane
    [51:42] a   [41:32] b   [31:22] c (PMUL)   [21:12] d (PMUL)
Result via the 0xAE QR commit path, component A = {b[31:0], a[31:0]}.
"""

import argparse
import sys
import time
import types

try:
    import serial
except ImportError:
    # Deferred: pyserial is only needed to talk to real hardware; the
    # encoding/oracle logic below must stay importable for the
    # hardware-free regression test on any Python. main() errors cleanly
    # if this stub is ever used to open a port.
    serial = types.ModuleType("serial")
    serial.Serial = None

sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])
from software.spu_host import SPUHostClient, SPUProtocolError

L_P = 521  # Lucas prime modulus (spu13_lucas_mac.v parameter L_P)

OP_PSCALE = 0xD0
OP_PCHIRAL = 0xD1
OP_PMUL = 0xD2
OP_PINV = 0xD3

# Post-write settle before polling the QR commit, per op. Taken from the
# proven smoke firmware's per-case settle_ms (PINV runs a Euclidean GCD
# loop and genuinely needs the headroom).
SETTLE_S = {
    OP_PSCALE: 0.02,
    OP_PCHIRAL: 0.02,
    OP_PMUL: 0.10,
    OP_PINV: 0.25,
}


def inst_lucas(op, lane, a, b, c=0, d=0):
    """Pack a Lucas sidecar instruction word."""
    def f10(v):
        return v & 0x3FF
    return (
        ((op & 0xFF) << 56)
        | ((lane & 0xF) << 52)
        | (f10(a) << 42)
        | (f10(b) << 32)
        | (f10(c) << 22)
        | (f10(d) << 12)
    )


def decode_a(commit_a):
    """Unpack QR component A = {b[31:0], a[31:0]} into (a, b)."""
    return commit_a & 0xFFFFFFFF, (commit_a >> 32) & 0xFFFFFFFF


# ── Exact-integer oracle (Z[phi]/L_521; phi^2 = phi + 1) ──────────────────

def oracle_pscale(a, b):
    """phi * (a + b*phi) = b + (a+b)*phi."""
    return b % L_P, (a + b) % L_P


def oracle_pchiral(a, b):
    """conj(a + b*phi) = (a+b) - b*phi   (phi_bar = 1 - phi)."""
    return (a + b) % L_P, (-b) % L_P


def oracle_pmul(a, b, c, d):
    """(a + b*phi)(c + d*phi) = (ac + bd) + (ad + bc + bd)*phi."""
    return (a * c + b * d) % L_P, (a * d + b * c + b * d) % L_P


def oracle_pinv(a, b):
    """(a + b*phi)^-1 mod L_521, via the norm: N = a^2 + ab - b^2."""
    norm = (a * a + a * b - b * b) % L_P
    norm_inv = pow(norm, L_P - 2, L_P)  # Fermat; L_521 is prime
    # (a + b*phi)^-1 = conj / N = ((a+b) - b*phi) / N
    return ((a + b) * norm_inv) % L_P, (-b * norm_inv) % L_P


def run_op(client, op, lane, a, b, c=0, d=0):
    word = inst_lucas(op, lane, a, b, c, d)
    client.write_chord(word)
    time.sleep(SETTLE_S[op])
    commit = client.qr_commit()
    return commit["lane"], decode_a(commit["A"])


# ── Act 1: the four silicon-proven ops ─────────────────────────────────────

def act1_proven_ops(client):
    print("Act 1: the four Z[phi]/L_521 sidecar ops (silicon-proven vectors)")
    print("-" * 72)
    ok = True
    cases = [
        ("PSCALE  phi*(3+5*phi)", OP_PSCALE, 2, (3, 5, 0, 0), oracle_pscale(3, 5)),
        ("PCHIRAL conj(3+5*phi)", OP_PCHIRAL, 12, (3, 5, 0, 0), oracle_pchiral(3, 5)),
        ("PMUL    (3+5*phi)(2+7*phi)", OP_PMUL, 3, (3, 5, 2, 7), oracle_pmul(3, 5, 2, 7)),
        ("PINV    (3+5*phi)^-1", OP_PINV, 4, (3, 5, 0, 0), oracle_pinv(3, 5)),
    ]
    for name, op, lane, args, expect in cases:
        got_lane, got = run_op(client, op, lane, *args)
        status = "ok" if (got == expect and got_lane == lane) else "MISMATCH"
        if status != "ok":
            ok = False
        print(f"  {name:<30} -> {got[0]:>3} + {got[1]:>3} phi   expected {expect[0]:>3} + {expect[1]:>3} phi   [{status}]")
    return ok


# ── Act 2: the zero-drift side-by-side ─────────────────────────────────────

def act2_drift_race(client, steps, lane=1):
    print()
    print(f"Act 2: {steps}-step phi-scaling loop -- silicon vs exact vs float64")
    print("-" * 72)
    print("  Each step: (a,b) -> phi*(a + b*phi), hardware result fed back as")
    print("  the next operand. Exact integers are ground truth. The float64")
    print("  run is the same recurrence in doubles, reduced mod 521 only for")
    print("  comparison -- watch where it silently stops being an integer fact.")
    print()

    hw_a, hw_b = 1, 0            # hardware state (fed back each step)
    exact_a, exact_b = 1, 0      # unreduced exact integers (Python bigints)
    f_a, f_b = 1.0, 0.0          # the same recurrence in IEEE-754 doubles

    hw_mismatch_step = None
    float_mismatch_step = None

    for step in range(1, steps + 1):
        got_lane, (hw_a, hw_b) = run_op(client, OP_PSCALE, lane, hw_a, hw_b)
        exact_a, exact_b = exact_b, exact_a + exact_b
        f_a, f_b = f_b, f_a + f_b

        exact_mod = (exact_a % L_P, exact_b % L_P)
        if (hw_a, hw_b) != exact_mod and hw_mismatch_step is None:
            hw_mismatch_step = step
        float_mod = (round(f_a) % L_P, round(f_b) % L_P)
        if float_mod != exact_mod and float_mismatch_step is None:
            float_mismatch_step = step
            print(f"  step {step:>6}: float64 diverged -- double now claims "
                  f"{float_mod[0]} + {float_mod[1]} phi, exact is "
                  f"{exact_mod[0]} + {exact_mod[1]} phi")

        if step in (1, 10, 50) or step % 100 == 0 or step == steps:
            hw_ok = "exact" if (hw_a, hw_b) == exact_mod else "WRONG"
            print(f"  step {step:>6}: silicon = {hw_a:>3} + {hw_b:>3} phi   [{hw_ok}]"
                  f"   (~{exact_b.bit_length()} bits unreduced)")

    print()
    if hw_mismatch_step is None:
        print(f"  silicon: bit-exact against ground truth for all {steps} steps.")
    else:
        print(f"  silicon: FIRST MISMATCH at step {hw_mismatch_step} -- investigate.")
    if float_mismatch_step is None:
        print(f"  float64: survived {steps} steps (run with --steps 100+ to see it fail).")
    else:
        print(f"  float64: lost the exact value at step {float_mismatch_step} "
              f"and never recovers.")
    return hw_mismatch_step is None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", required=True, help="e.g. /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--steps", type=int, default=200,
                        help="phi-scaling loop length (default 200; float64 "
                             "fails around step 79, silicon never does)")
    ns = parser.parse_args(argv)

    if serial.Serial is None:
        print("ERROR: pyserial is not installed (pip install pyserial).", file=sys.stderr)
        return 1

    ser = serial.Serial(ns.port, ns.baud, timeout=0.05)
    client = SPUHostClient(ser)
    try:
        client.connect()
        print("LUCAS zero-drift demo -- exact Z[phi]/L_521 arithmetic in silicon")
        print("=" * 72)
        ok1 = act1_proven_ops(client)
        ok2 = act2_drift_race(client, ns.steps)
        print("=" * 72)
        if ok1 and ok2:
            print("PASS: silicon matched exact-integer ground truth on every check.")
            return 0
        print("FAIL: see mismatches above.")
        return 1
    except SPUProtocolError as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
