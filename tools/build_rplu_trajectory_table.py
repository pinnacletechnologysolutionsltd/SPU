#!/usr/bin/env python3
"""
build_rplu_trajectory_table.py — RPLU Trajectory Correction Table Generator

Simulates rational curve trajectories, measures fixed-point truncation drift,
and builds a correction lookup table for the RPLU flash image.

The table maps (quadrance_error, axis_id) → correction_vector, where:
  - quadrance_error = Q(commanded − actual)  — rotation-invariant scalar
  - axis_id         = which manifold axis (0–12)
  - correction      = the pre-computed undo vector per bin

Error model (v1.0):
  Fixed-point Q12 truncation — the SPU stores surd coefficients as
  (int16 P, int16 Q) × 2^−12.  Multiplication of two Q12 values
  produces Q24, which is rounded back to Q12.  This introduces
  ±0.5 LSB error per multiply.  Over a Pell arc of N steps with
  9 multiplies per step, worst-case error ≈ N × 4.5 LSB.

Usage:
    python3 tools/build_rplu_trajectory_table.py                    # default arc
    python3 tools/build_rplu_trajectory_table.py --arc-steps 12     # 12-step Pell arc
    python3 tools/build_rplu_trajectory_table.py --output build/    # custom output dir

CC0 1.0 Universal.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from spu_vm import RationalSurd, QuadrayVector

RS = RationalSurd

# ── Q12 fixed-point model ───────────────────────────────────────────────

Q12_SCALE = 4096  # 2^12

def q12_truncate(value: int) -> int:
    """Truncate a Q24 product back to Q12 with rounding.
    This is where fixed-point error enters: value/4096 with round-to-nearest."""
    return (value + Q12_SCALE // 2) // Q12_SCALE

def q12_multiply(a: RationalSurd, b: RationalSurd) -> RationalSurd:
    """
    Multiply two surds already in Q12 fixed-point.
    Inputs: a, b with coefficients already × 4096.
    Output: product in Q12 (coefficients × 4096), with truncation error.
    """
    # Full precision products (Q24)
    ac = a.a * b.a
    bd = a.b * b.b
    ad = a.a * b.b
    bc = a.b * b.a

    # Truncate back to Q12
    p = q12_truncate(ac) + 3 * q12_truncate(bd)
    q = q12_truncate(ad) + q12_truncate(bc)

    return RationalSurd(p, q)


def surd_to_q12(s: RationalSurd) -> RationalSurd:
    """Convert a RationalSurd to Q12 representation (scale by 4096)."""
    return RationalSurd(s.a * Q12_SCALE, s.b * Q12_SCALE)

def surd_from_q12(s: RationalSurd) -> RationalSurd:
    """Convert from Q12 back to integer (divide by 4096, round)."""
    return RationalSurd(
        (s.a + Q12_SCALE // 2) // Q12_SCALE,
        (s.b + Q12_SCALE // 2) // Q12_SCALE,
    )


# ── Trajectory simulator ────────────────────────────────────────────────

def simulate_circulant_chain(base: QuadrayVector, joints: list,
                              use_q12: bool = True) -> list:
    """
    Simulate a circulant-based kinematic chain trajectory.
    Each joint applies a fractional F,G,H circulant rotation.
    Commanded = ideal Q(√3) math.  Actual = Q12-truncated after each multiply.

    Fractional coefficients (like F=2/3) are where Q12 error enters:
    the representation of 2/3 in Q12 is floor(2×4096/3) = 2730 instead
    of 2730.67, losing 0.33 LSB per coefficient per step.
    """
    trajectory = []
    current_cmd = QuadrayVector(base.a, base.b, base.c, base.d)
    current_act = QuadrayVector(
        surd_to_q12(base.a), surd_to_q12(base.b),
        surd_to_q12(base.c), surd_to_q12(base.d),
    )
    trajectory.append((current_cmd, current_act))

    for F, G, H in joints:
        # Commanded: exact circulant
        b_cmd = F * current_cmd.b + H * current_cmd.c + G * current_cmd.d
        c_cmd = G * current_cmd.b + F * current_cmd.c + H * current_cmd.d
        d_cmd = H * current_cmd.b + G * current_cmd.c + F * current_cmd.d
        current_cmd = QuadrayVector(current_cmd.a, b_cmd, c_cmd, d_cmd)

        if use_q12:
            # Actual: Q12 circulant with truncation at each multiply.
            # F12, G12, H12 are already Q12-scaled by surd_to_q12.
            F12 = surd_to_q12(F)
            G12 = surd_to_q12(G)
            H12 = surd_to_q12(H)

            b_act = (q12_multiply(F12, current_act.b) +
                     q12_multiply(H12, current_act.c) +
                     q12_multiply(G12, current_act.d))
            c_act = (q12_multiply(G12, current_act.b) +
                     q12_multiply(F12, current_act.c) +
                     q12_multiply(H12, current_act.d))
            d_act = (q12_multiply(H12, current_act.b) +
                     q12_multiply(G12, current_act.c) +
                     q12_multiply(F12, current_act.d))
            current_act = QuadrayVector(current_act.a, b_act, c_act, d_act)
        else:
            current_act = QuadrayVector(
                current_cmd.a, current_cmd.b,
                current_cmd.c, current_cmd.d,
            )

        trajectory.append((current_cmd, current_act))

    return trajectory


# ── Error measurement ───────────────────────────────────────────────────

def measure_error(commanded: QuadrayVector, actual: QuadrayVector) -> dict:
    """Compute error quadrance and per-component error for RPLU binning."""
    error = QuadrayVector(
        commanded.a - actual.a,
        commanded.b - actual.b,
        commanded.c - actual.c,
        commanded.d - actual.d,
    )
    q_err = error.quadrance()  # rotation-invariant scalar

    return {
        "quadrance": q_err,
        "a_err": (error.a.a, error.a.b),
        "b_err": (error.b.a, error.b.b),
        "c_err": (error.c.a, error.c.b),
        "d_err": (error.d.a, error.d.b),
    }


# ── RPLU bin assignment ─────────────────────────────────────────────────

def quadrance_to_bin(q: RationalSurd, max_q: int, num_bins: int) -> int:
    """
    Map a quadrance error to an RPLU bin index.
    Uses the rational part (a-coefficient) as the primary key.
    For surd errors with b≠0, we'd need the full comparison.
    v1.0: use a.norm() = a²−3b² as the scalar key (always an integer).
    """
    norm = q.a * q.a - 3 * q.b * q.b  # Pell-style norm, always integer
    if norm < 0:
        norm = -norm  # quadrance error is always non-negative after abs
    bin_width = max(1, max_q // num_bins)
    bin_idx = min(norm // bin_width, num_bins - 1)
    return bin_idx


# ── Correction table builder ────────────────────────────────────────────

def build_correction_table(trajectory: list, num_bins: int = 256) -> dict:
    """
    Build an RPLU correction table from trajectory error data.
    For each bin, stores the average correction vector (negated error).
    """
    # Initialize accumulators per bin
    bins = {}
    for i in range(num_bins):
        bins[i] = {
            "count": 0,
            "sum_a": [0, 0], "sum_b": [0, 0],
            "sum_c": [0, 0], "sum_d": [0, 0],
        }

    # Find max quadrance for bin scaling
    max_q = 1
    for cmd, act in trajectory:
        err = measure_error(cmd, act)
        n = err["quadrance"].a * err["quadrance"].a - 3 * err["quadrance"].b * err["quadrance"].b
        n = abs(n)
        if n > max_q:
            max_q = n

    # Accumulate errors per bin
    for cmd, act in trajectory:
        err = measure_error(cmd, act)
        bin_idx = quadrance_to_bin(err["quadrance"], max_q, num_bins)
        bins[bin_idx]["count"] += 1
        for comp, key in [("sum_a", "a_err"), ("sum_b", "b_err"),
                          ("sum_c", "c_err"), ("sum_d", "d_err")]:
            bins[bin_idx][comp][0] += err[key][0]
            bins[bin_idx][comp][1] += err[key][1]

    # Compute average correction per bin (negate the error)
    table = {}
    for bin_idx, data in bins.items():
        if data["count"] == 0:
            table[bin_idx] = None  # unused bin
            continue
        n = data["count"]
        # Correction = -average_error (rounded to integer)
        table[bin_idx] = {
            "corr_a": (-data["sum_a"][0] // n, -data["sum_a"][1] // n),
            "corr_b": (-data["sum_b"][0] // n, -data["sum_b"][1] // n),
            "corr_c": (-data["sum_c"][0] // n, -data["sum_c"][1] // n),
            "corr_d": (-data["sum_d"][0] // n, -data["sum_d"][1] // n),
            "count": n,
        }

    return {
        "num_bins": num_bins,
        "max_quadrance": max_q,
        "bin_width": max(1, max_q // num_bins),
        "table": table,
    }


# ── RPLU hex word output (compatible with existing flash loader) ────────

def emit_rplu_hex(table_data: dict, output_path: Path):
    """
    Write the correction table as a hex word file compatible with
    the RPLU flash loader (tools/build_tang25k_j4_rplu_flash.py).
    Format: one 32-bit hex word per line (address:data pairs).
    """
    lines = []
    lines.append(f"# RPLU Trajectory Correction Table")
    lines.append(f"# bins={table_data['num_bins']} "
                 f"max_q={table_data['max_quadrance']} "
                 f"width={table_data['bin_width']}")
    lines.append("")

    for bin_idx in sorted(table_data["table"].keys()):
        entry = table_data["table"][bin_idx]
        if entry is None:
            continue
        # Encode: [addr:16][a_p:4][a_q:4][b_p:4][b_q:4]...
        # For v1.0, emit as JSON for readability; hex format TBD
        # with existing flash builder integration.
        pass

    # For now, output JSON summary
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(table_data, f, indent=2, default=str)

    print(f"Correction table written to {output_path}")
    print(f"  Bins: {table_data['num_bins']}")
    print(f"  Max quadrance error: {table_data['max_quadrance']}")
    print(f"  Bin width: {table_data['bin_width']}")
    filled = sum(1 for v in table_data["table"].values() if v is not None)
    print(f"  Filled bins: {filled}/{table_data['num_bins']}")
    total_errors = sum(
        v["count"] for v in table_data["table"].values() if v is not None
    )
    print(f"  Total error samples: {total_errors}")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="RPLU Trajectory Correction Table Generator"
    )
    ap.add_argument("--num-bins", type=int, default=256,
                    help="Number of RPLU correction bins (default: 256)")
    ap.add_argument("--max-error", type=int, default=4096,
                    help="Max quadrance error in Q12 LSB (default: 4096 = 1.0)")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "build" / "rplu_trajectory" / "correction_table.json",
                    help="Output path for correction table")
    args = ap.parse_args()

    # ── Build analytic correction table ──────────────────────────────────
    # For v1.0: each bin maps quadrance error → correction = -error.
    # The correction is the identity in error space: undo the observed error.
    # When real sensor data arrives, this table gets updated from telemetry.
    #
    # Table structure:
    #   num_bins × 4 components × 2 coefficients (a,b per surd) = 8 ints/entry
    #   Each coefficient in Q12 fixed-point, range ±max_error.

    num_bins = args.num_bins
    max_err = args.max_error
    bin_width = max(1, max_err // num_bins)

    print(f"Building analytic correction table: {num_bins} bins, "
          f"max_error={max_err} LSB, bin_width={bin_width}")

    table = {}
    for bin_idx in range(num_bins):
        # Bin center error magnitude (quadrance)
        bin_center = bin_idx * bin_width + bin_width // 2

        # Correction = -bin_center (negate the error).
        # For a proper 4D correction, we'd distribute across ABCD based on
        # the error direction. For v1.0: uniform distribution.
        # Each component gets 1/4 of the correction magnitude.
        corr_mag = -bin_center // 4

        table[bin_idx] = {
            "error_quadrance": bin_center,
            "corr_a": (corr_mag, 0),
            "corr_b": (corr_mag, 0),
            "corr_c": (corr_mag, 0),
            "corr_d": (corr_mag, 0),
        }

    # ── Emit ─────────────────────────────────────────────────────────────
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    table_data = {
        "format": "rplu_trajectory_correction_v1",
        "num_bins": num_bins,
        "max_error_q12": max_err,
        "bin_width_q12": bin_width,
        "entry_size_bits": 128,  # 4 surds × 32 bits (int16 P, int16 Q)
        "total_size_bytes": num_bins * 16,
        "description": (
            "Analytic correction table: maps quadrance error → -error. "
            "Replace with telemetry-derived corrections when sensor data "
            "is available."
        ),
        "table": table,
    }

    with open(output_path, "w") as f:
        json.dump(table_data, f, indent=2)

    # Also emit hex word format for flash loader integration
    hex_path = output_path.with_suffix(".hex")
    with open(hex_path, "w") as f:
        f.write(f"# RPLU Trajectory Correction Table v1.0\n")
        f.write(f"# bins={num_bins} max_err_q12={max_err} "
                f"bin_width={bin_width}\n")
        for bin_idx in sorted(table.keys()):
            e = table[bin_idx]
            # Encode: addr:[16] corr_a_p:[16] corr_a_q:[16] ... 
            # For now: human-readable hex
            f.write(f"@{bin_idx:04X} "
                    f"{e['corr_a'][0] & 0xFFFF:04X}{e['corr_a'][1] & 0xFFFF:04X} "
                    f"{e['corr_b'][0] & 0xFFFF:04X}{e['corr_b'][1] & 0xFFFF:04X} "
                    f"{e['corr_c'][0] & 0xFFFF:04X}{e['corr_c'][1] & 0xFFFF:04X} "
                    f"{e['corr_d'][0] & 0xFFFF:04X}{e['corr_d'][1] & 0xFFFF:04X}\n")

    print(f"Correction table written to {output_path}")
    print(f"Hex words written to {hex_path}")
    print(f"  Bins: {num_bins}")
    print(f"  Max error: {max_err} Q12 LSB (≈ {max_err/Q12_SCALE:.3f} in Q(√3))")
    print(f"  Bin width: {bin_width} LSB")
    print(f"  Entry size: 16 bytes (4 surds × int16 pair)")
    print(f"  Total size: {num_bins * 16} bytes")
    print(f"  Fits in BRAM: {'YES' if num_bins * 16 <= 2048 else 'NO'}"
          f" ({num_bins * 16}/2048 bytes)")


if __name__ == "__main__":
    main()
