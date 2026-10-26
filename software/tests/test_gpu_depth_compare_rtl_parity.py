#!/usr/bin/env python3
"""test_gpu_depth_compare_rtl_parity.py -- exhaustive bit-exact parity
between an independent Python re-implementation of spu_depth_compare.v's
depth-aware pixel selection and the real RTL.

Exhaustively covers every (cov0, cov1) combination x a representative
set of depth relationships (0 vs 0, positive vs positive, negative vs
negative, negative vs positive, equal -- the tie case, and near the
56-bit signed extremes) x distinct colors per unit, so a mismatch in
either operand's sign handling or the tie-break policy would be caught,
not just the common case.

Run:
  python3 software/tests/test_gpu_depth_compare_rtl_parity.py

Requirements: iverilog + vvp in PATH.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RTL_FILES = ["hardware/rtl/gpu/spu_depth_compare.v"]

MAX56 = (1 << 55) - 1
MIN56 = -(1 << 55)

DEPTH_PAIRS = [
    (0, 0), (100, 200), (200, 100), (-100, -200), (-200, -100),
    (-50, 50), (50, -50), (12345, 12345),  # tie
    (MAX56, MIN56), (MIN56, MAX56), (MAX56, MAX56), (MIN56, MIN56),
    (0, MAX56), (MIN56, 0),
]
COV_COMBOS = [(0, 0), (0, 1), (1, 0), (1, 1)]


def signed_lit(v: int, width: int) -> str:
    return f"{width}'sd{v}" if v >= 0 else f"-{width}'sd{-v}"


def expected(cov0, cov1, d0, d1, c0, c1):
    unit0_wins = cov0 and (not cov1 or d0 <= d1)
    unit1_wins = cov1 and not unit0_wins
    if unit0_wins:
        return c0
    if unit1_wins:
        return c1
    return (0, 0, 0)


TB_TEMPLATE = r"""
`timescale 1ns/1ps
module depth_compare_tb;
    reg cov0, cov1;
    reg signed [55:0] depth0, depth1;
    reg [3:0] r0, g0, b0, r1, g1, b1;
    wire [3:0] pixel_r, pixel_g, pixel_b;

    spu_depth_compare u_dut (
        .cov0(cov0), .cov1(cov1), .depth0(depth0), .depth1(depth1),
        .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
        .pixel_r(pixel_r), .pixel_g(pixel_g), .pixel_b(pixel_b)
    );

    integer i;
    initial begin
{VECTORS}
        #10;
        $finish;
    end
endmodule
"""

VEC_TEMPLATE = (
    "        cov0={cov0}; cov1={cov1}; depth0={d0}; depth1={d1}; "
    "r0=4'h{c0r:x}; g0=4'h{c0g:x}; b0=4'h{c0b:x}; "
    "r1=4'h{c1r:x}; g1=4'h{c1g:x}; b1=4'h{c1b:x}; #1; "
    '$display("VEC %0d %0d %0d %0d", pixel_r, pixel_g, pixel_b, {idx});'
)


def build_vectors():
    vecs = []
    color_pairs = [((1, 2, 3), (4, 5, 6)), ((15, 0, 8), (0, 15, 7))]
    idx = 0
    for cov0, cov1 in COV_COMBOS:
        for d0, d1 in DEPTH_PAIRS:
            for c0, c1 in color_pairs:
                vecs.append((idx, cov0, cov1, d0, d1, c0, c1))
                idx += 1
    return vecs


def gen_tb(vecs):
    lines = []
    for idx, cov0, cov1, d0, d1, c0, c1 in vecs:
        lines.append(VEC_TEMPLATE.format(
            cov0=cov0, cov1=cov1, d0=signed_lit(d0, 56), d1=signed_lit(d1, 56),
            c0r=c0[0], c0g=c0[1], c0b=c0[2], c1r=c1[0], c1g=c1[1], c1b=c1[2],
            idx=idx,
        ))
    return TB_TEMPLATE.format(VECTORS="\n".join(lines))


def main() -> int:
    vecs = build_vectors()
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)
    tb_path = build_dir / "depth_compare_tb.v"
    tb_path.write_text(gen_tb(vecs))
    vvp_path = build_dir / "depth_compare_tb.vvp"
    subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path)]
        + [str(REPO / f) for f in RTL_FILES],
        check=True, cwd=REPO,
    )
    result = subprocess.run(["vvp", str(vvp_path)], check=True,
                             capture_output=True, text=True, cwd=REPO)
    got = {}
    for line in result.stdout.splitlines():
        if line.startswith("VEC "):
            parts = line.split()
            r, g, b, idx = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
            got[idx] = (r, g, b)

    mismatches = 0
    for idx, cov0, cov1, d0, d1, c0, c1 in vecs:
        exp = expected(cov0, cov1, d0, d1, c0, c1)
        if got.get(idx) != exp:
            mismatches += 1
            if mismatches <= 10:
                print(f"  MISMATCH vec {idx}: cov=({cov0},{cov1}) d=({d0},{d1}) "
                      f"expected {exp} got {got.get(idx)}")

    print(f"spu_depth_compare.v RTL parity: {len(vecs)} vectors, {mismatches} mismatches")
    if mismatches:
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
