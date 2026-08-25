#!/usr/bin/env python3
"""test_gpu_depth_math_rtl_parity.py -- bit-exact parity between
gpu_depth_v2_oracle.py's depth_interp_setup() (dot products -> D=c0+c1+c2
-> reciprocal -> final scale, all in one function) and the real RTL
(spu_depth_math.v + spu_reciprocal_core.v + spu_shared_mult35.v),
for the representative triangles already characterized, plus a couple
of hand-picked sign-combination cases (the oracle's triangles don't
happen to exercise every sign combination of Sa/Sb/Sc/D, and the sign
handling -- extracted and reapplied around the magnitude-only shared
multiplier -- is exactly the kind of thing worth testing beyond the
"happy path" set).

Run:
  python3 software/tests/test_gpu_depth_math_rtl_parity.py

Requirements: iverilog + vvp in PATH.
"""
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))

from gpu_depth_v2_oracle import depth_interp_setup, triangle_edges  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
]

TEST_CASES = [
    ("small, screen-corner", (10, 10), (600, 30), (300, 460), 0, 65535, 32768),
    ("thin sliver", (10, 10), (630, 12), (320, 470), 1000, 60000, 30000),
    ("near-degenerate", (0, 0), (639, 1), (320, 479), 0, 65535, 40000),
    # Hand-picked to flip winding (negates D's sign relative to the
    # cases above) and to push z-values toward extremes, stressing the
    # sign-extraction/reapplication path around the shared multiplier.
    ("flipped winding", (300, 460), (600, 30), (10, 10), 0, 65535, 32768),
    ("all-max depth", (50, 50), (500, 60), (200, 400), 65535, 65535, 65535),
]


def signed_lit(v: int, width: int) -> str:
    return f"{width}'sd{v}" if v >= 0 else f"-{width}'sd{-v}"


TB_TEMPLATE = r"""
`timescale 1ns/1ps
module depth_math_tb;
    reg clk = 0, rst_n = 0, start = 0;
    reg signed [15:0] a0={A0}, b0={B0}, a1={A1}, b1={B1}, a2={A2}, b2={B2};
    reg signed [31:0] c0={C0}, c1={C1}, c2={C2};
    reg [15:0] z0={Z0}, z1={Z1}, z2={Z2};
    wire signed [55:0] A_z, B_z, C_z;
    wire [6:0] frac_bits;
    wire done;

    spu_depth_math u_dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .a0(a0), .b0(b0), .a1(a1), .b1(b1), .a2(a2), .b2(b2),
        .c0(c0), .c1(c1), .c2(c2), .z0(z0), .z1(z1), .z2(z2),
        .A_z(A_z), .B_z(B_z), .C_z(C_z), .frac_bits(frac_bits), .done(done)
    );

    always #5 clk = ~clk;

    initial begin
        rst_n = 0;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk);

        start = 1;
        @(negedge clk);
        start = 0;
        while (!done) @(negedge clk);
        $display("RESULT %0d %0d %0d %0d", A_z, B_z, C_z, frac_bits);
        $finish;
    end
endmodule
"""


def gen_tb(edges, z):
    e0, e1, e2 = edges
    (a0, b0, c0), (a1, b1, c1), (a2, b2, c2) = e0, e1, e2
    z0, z1, z2 = z
    return TB_TEMPLATE.format(
        A0=signed_lit(a0, 16), B0=signed_lit(b0, 16), C0=signed_lit(c0, 32),
        A1=signed_lit(a1, 16), B1=signed_lit(b1, 16), C1=signed_lit(c1, 32),
        A2=signed_lit(a2, 16), B2=signed_lit(b2, 16), C2=signed_lit(c2, 32),
        Z0=z0, Z1=z1, Z2=z2,
    )


def run_rtl(tb_src, build_dir, name):
    tb_path = build_dir / f"depth_math_tb_{name}.v"
    tb_path.write_text(tb_src)
    vvp_path = build_dir / f"depth_math_tb_{name}.vvp"
    subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path)]
        + [str(REPO / f) for f in RTL_FILES],
        check=True, cwd=REPO,
    )
    result = subprocess.run(["vvp", str(vvp_path)], check=True,
                             capture_output=True, text=True, cwd=REPO)
    for line in result.stdout.splitlines():
        if line.startswith("RESULT "):
            parts = line.split()
            return tuple(int(p) for p in parts[1:])
    raise RuntimeError(f"no RESULT line in output:\n{result.stdout}")


def random_cases(n=25, seed=20260825):
    """Random legitimate screen-space triangles + depths, the same
    distribution used to empirically bound |Sc| at 35 bits over 200k
    samples (see the session's investigation of the [32:0] truncation
    bug) -- a much better stress set than a handful of hand-picked
    triangles, which already missed two real width bugs in this module."""
    rng = random.Random(seed)
    cases = []
    i = 0
    while len(cases) < n:
        v0 = (rng.randint(0, 639), rng.randint(0, 479))
        v1 = (rng.randint(0, 639), rng.randint(0, 479))
        v2 = (rng.randint(0, 639), rng.randint(0, 479))
        try:
            triangle_edges(v0, v1, v2)
        except AssertionError:
            i += 1
            continue  # degenerate (zero-area), skip
        z0, z1, z2 = (rng.randint(0, 65535) for _ in range(3))
        cases.append((f"random_{i}", v0, v1, v2, z0, z1, z2))
        i += 1
    return cases


def main() -> int:
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)

    mismatches = 0
    for name, v0, v1, v2, z0, z1, z2 in TEST_CASES + random_cases():
        e0, e1, e2, D = triangle_edges(v0, v1, v2)
        A_z, B_z, C_z, frac_bits = depth_interp_setup(v0, v1, v2, z0, z1, z2)
        expected = (A_z, B_z, C_z, frac_bits)

        tb_src = gen_tb((e0, e1, e2), (z0, z1, z2))
        got = run_rtl(tb_src, build_dir, name.replace(" ", "_").replace(",", ""))

        status = "OK" if got == expected else "MISMATCH"
        print(f"{name}: expected={expected} got={got} [{status}]")
        if got != expected:
            mismatches += 1

    if mismatches:
        print(f"FAIL: {mismatches}/{len(TEST_CASES)} mismatches")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
