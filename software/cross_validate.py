#!/usr/bin/env python3
"""
cross_validate.py — Cross-validate spu_vm.py against the C++ Q(√3) reference.

Runs 5 canonical test programs through both:
  1. Python — using spu_vm.py (RationalSurd, QuadrayVector) directly
  2. C++ — compiling + running software/common/tests/spu_cross_ref.cpp

Compares register state at each SNAP boundary.
Any divergence = spec bug in either the emulator or the C++ layer headers.

Output: PASS / FAIL with full diff on any mismatch.

Usage:
    python3 software/cross_validate.py
    python3 software/cross_validate.py --verbose

CC0 1.0 Universal.
"""

import sys
import os
import subprocess
import tempfile
import argparse

# ---------------------------------------------------------------------------
# Resolve repo root so we can find headers + the C++ source
# ---------------------------------------------------------------------------
HERE      = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
CPP_SRC   = os.path.join(REPO_ROOT, "software", "common", "tests", "spu_cross_ref.cpp")
INC_DIR   = os.path.join(REPO_ROOT, "software", "common", "include")

sys.path.insert(0, HERE)
from spu_vm import RationalSurd, QuadrayVector

# ---------------------------------------------------------------------------
# Parse C++ reference output
# ---------------------------------------------------------------------------

def parse_cpp_output(text: str) -> dict[str, dict]:
    """
    Parse the spu_cross_ref output into a dict:
      { label: { "R0": (p,q), "QR0": (ap,aq,bp,bq,cp,cq,dp,dq), ... } }
    """
    snaps = {}
    current_label = None
    current_regs  = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "SPU_CROSS_REF_BEGIN" or line == "SPU_CROSS_REF_END":
            continue
        if line.startswith("SNAP "):
            parts = line.split(";", 1)
            current_label = parts[1].strip() if len(parts) > 1 else parts[0].split()[1]
            current_regs  = {}
        elif line == "END_SNAP":
            snaps[current_label] = current_regs
            current_label = None
        elif line.startswith("R") and current_label:
            parts = line.split()
            current_regs[parts[0]] = (int(parts[1]), int(parts[2]))
        elif line.startswith("QR") and current_label:
            parts = line.split()
            key   = parts[0]
            vals  = tuple(int(x) for x in parts[1:])
            current_regs[key] = vals
    return snaps


# ---------------------------------------------------------------------------
# Python reference programs — mirror spu_cross_ref.cpp exactly
# ---------------------------------------------------------------------------

def python_prog_scalar_arith() -> dict:
    regs = [RationalSurd(0, 0)] * 4
    regs[0] = RationalSurd(2, 0)
    regs[1] = RationalSurd(0, 1)
    regs[2] = regs[0] + regs[1]
    regs[3] = regs[0] * regs[1]
    return {f"R{i}": (regs[i].a, regs[i].b) for i in range(4)}


def python_prog_quadray_load() -> dict:
    def qr_add(a: QuadrayVector, b: QuadrayVector) -> QuadrayVector:
        return (a + b).normalize()

    qr0 = QuadrayVector(RationalSurd(1), RationalSurd(0),
                        RationalSurd(0), RationalSurd(0))
    qr1 = QuadrayVector(RationalSurd(1), RationalSurd(1),
                        RationalSurd(0), RationalSurd(0)).normalize()
    qr2 = qr_add(qr0, qr1)

    out = {"R0": (0, 0)}
    for i, q in enumerate([qr0, qr1, qr2]):
        out[f"QR{i}"] = (q.a.a, q.a.b, q.b.a, q.b.b,
                         q.c.a, q.c.b, q.d.a, q.d.b)
    return out


def python_prog_pell_rotate() -> dict:
    qr0 = QuadrayVector(RationalSurd(1), RationalSurd(0),
                        RationalSurd(0), RationalSurd(0))
    qr1 = qr0.rotate().normalize()
    out = {"R0": (0, 0)}
    for i, q in enumerate([qr0, qr1]):
        out[f"QR{i}"] = (q.a.a, q.a.b, q.b.a, q.b.b,
                         q.c.a, q.c.b, q.d.a, q.d.b)
    return out


def python_prog_quadrance_spread() -> dict:
    qr0 = QuadrayVector(RationalSurd(1), RationalSurd(0),
                        RationalSurd(0), RationalSurd(0))
    qr1 = QuadrayVector(RationalSurd(0), RationalSurd(1),
                        RationalSurd(0), RationalSurd(0))
    q0  = qr0.quadrance()
    q1  = qr1.quadrance()
    s   = qr0.spread(qr1)  # returns RationalSurd (numerator/denominator packed)
    # spread() in Python returns a single RationalSurd where .a=numerator .b=denom
    # (see spu_vm.py SPREAD opcode: stores num in R[r1], den in R[r1+1])
    # But quadrance() also returns a RationalSurd — confirm shapes
    out = {
        "R0": (q0.a, q0.b),
        "R1": (q1.a, q1.b),
    }
    # spread returns (numerator RationalSurd, denominator RationalSurd) in Python
    if isinstance(s, tuple):
        out["R2"] = (s[0].a, s[0].b)
        out["R3"] = (s[1].a, s[1].b)
    else:
        out["R2"] = (s.a, s.b)
        out["R3"] = (0, 0)
    for i, q in enumerate([qr0, qr1]):
        out[f"QR{i}"] = (q.a.a, q.a.b, q.b.a, q.b.b,
                         q.c.a, q.c.b, q.d.a, q.d.b)
    return out


def python_prog_pell_chain() -> dict:
    regs = [RationalSurd(0, 0)] * 5
    regs[0] = RationalSurd(1, 0)
    for i in range(1, 5):
        p, q = regs[i-1].a, regs[i-1].b
        regs[i] = RationalSurd(2*p + 3*q, p + 2*q)
    return {f"R{i}": (regs[i].a, regs[i].b) for i in range(5)}


PYTHON_PROGRAMS = {
    "scalar_arith":      python_prog_scalar_arith,
    "quadray_load":      python_prog_quadray_load,
    "pell_rotate":       python_prog_pell_rotate,
    "quadrance_spread":  python_prog_quadrance_spread,
    "pell_chain":        python_prog_pell_chain,
}


# ---------------------------------------------------------------------------
# Build + run C++ reference
# ---------------------------------------------------------------------------

def run_cpp_reference() -> str:
    """Compile spu_cross_ref.cpp and return its stdout."""
    with tempfile.NamedTemporaryFile(suffix="", delete=False) as tmp:
        bin_path = tmp.name

    try:
        result = subprocess.run(
            ["g++", "-std=c++17", f"-I{INC_DIR}", "-o", bin_path, CPP_SRC],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("ERROR: C++ compilation failed:")
            print(result.stderr)
            sys.exit(1)

        result2 = subprocess.run([bin_path], capture_output=True, text=True)
        if result2.returncode != 0:
            print("ERROR: C++ reference runner failed:")
            print(result2.stderr)
            sys.exit(1)

        return result2.stdout
    finally:
        try:
            os.unlink(bin_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------

def fmt_val(v) -> str:
    if isinstance(v, tuple) and len(v) == 2:
        return f"({v[0]}, {v[1]})"
    if isinstance(v, tuple) and len(v) == 8:
        return (f"[({v[0]}+{v[1]}√3), ({v[2]}+{v[3]}√3), "
                f"({v[4]}+{v[5]}√3), ({v[6]}+{v[7]}√3)]")
    return str(v)


def compare(py_snaps: dict, cpp_snaps: dict, verbose: bool) -> bool:
    all_pass = True
    labels = list(PYTHON_PROGRAMS.keys())

    for label in labels:
        py  = py_snaps.get(label, {})
        cpp = cpp_snaps.get(label, {})

        if not cpp:
            print(f"  FAIL [{label}]: C++ produced no output for this snap")
            all_pass = False
            continue

        all_keys = sorted(set(list(py.keys()) + list(cpp.keys())))
        snap_ok  = True

        for key in all_keys:
            pv = py.get(key)
            cv = cpp.get(key)
            if pv != cv:
                if snap_ok:
                    print(f"\n  FAIL [{label}]:")
                snap_ok  = False
                all_pass = False
                print(f"    {key:6s}  Python={fmt_val(pv)}  C++={fmt_val(cv)}")
            elif verbose:
                print(f"  ok   [{label}] {key:6s} = {fmt_val(pv)}")

        if snap_ok and not verbose:
            print(f"  ok   [{label}]")

    return all_pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SPU-13 cross-validator: spu_vm.py vs C++ Q(√3) reference"
    )
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show all register comparisons, not just failures')
    args = parser.parse_args()

    print("── SPU-13 Cross-Validation ───────────────────────────────────")
    print(f"   Python  : spu_vm.py (RationalSurd, QuadrayVector)")
    print(f"   C++ ref : {os.path.relpath(CPP_SRC, REPO_ROOT)}")
    print()

    # Run C++
    cpp_out   = run_cpp_reference()
    cpp_snaps = parse_cpp_output(cpp_out)

    # Run Python
    py_snaps = {}
    for label, fn in PYTHON_PROGRAMS.items():
        py_snaps[label] = fn()

    # Inspect spread() return type once and warn if unexpected
    _s = QuadrayVector(RationalSurd(1), RationalSurd(0),
                       RationalSurd(0), RationalSurd(0)).spread(
         QuadrayVector(RationalSurd(0), RationalSurd(1),
                       RationalSurd(0), RationalSurd(0)))
    if not isinstance(_s, tuple):
        print("NOTE: spread() returns a single RationalSurd in this build "
              "(num/denom not split). quadrance_spread R2/R3 comparison adjusted.")
    print()

    # Compare
    passed = compare(py_snaps, cpp_snaps, args.verbose)

    print()
    print("=" * 50)
    n = len(PYTHON_PROGRAMS)
    if passed:
        print(f"cross_validate.py: {n}/{n} snaps matched")
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL — register divergence detected (see above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
