#!/usr/bin/env python3
"""test_gpu_attr_stepper_rtl_parity.py -- bit-exact parity between
gpu_depth_v2_oracle.py's simulate_depth_raster() (the per-pixel
incremental accumulation model) and the real RTL (spu_attr_stepper.v),
for the representative triangles the depth-v2 contract already
characterized.

Feeds spu_attr_stepper.v the same A_z/B_z/C_z/frac_bits the oracle's
depth_interp_setup() computes (this test is scoped to the accumulator
alone, not spu_depth_setup.v's FSM -- that gets its own integration
test once it exists), scans the triangle's bounding box in real
step_x/step_y raster order, and compares every covered pixel's
interpolated depth exactly.

Run:
  python3 software/tests/test_gpu_attr_stepper_rtl_parity.py

Requirements: iverilog + vvp in PATH.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))

from gpu_depth_v2_oracle import depth_interp_setup, triangle_edges  # noqa: E402

RTL_FILES = ["hardware/rtl/gpu/spu_attr_stepper.v"]


def signed_lit(v: int, width: int = 56) -> str:
    """Sized signed Verilog literal -- plain decimal literals default to
    32-bit in some contexts, which would silently truncate the ~42-45
    bit A_z/B_z/C_z values this test feeds in."""
    return f"{width}'sd{v}" if v >= 0 else f"-{width}'sd{-v}"

TEST_CASES = [
    ("small, screen-corner", (10, 10), (600, 30), (300, 460), 0, 65535, 32768),
    ("thin sliver", (10, 10), (630, 12), (320, 470), 1000, 60000, 30000),
    ("near-degenerate", (0, 0), (639, 1), (320, 479), 0, 65535, 40000),
]

TB_TEMPLATE = r"""
`timescale 1ns/1ps
module attr_stepper_tb;
    reg clk = 0, rst_n = 0, setup = 0, step_x = 0, step_y = 0;
    reg signed [55:0] a_coef = 0, b_coef = 0, c_coef = 0;
    reg [6:0] frac_bits = 0;
    wire signed [55:0] value_out;

    spu_attr_stepper u_dut (
        .clk(clk), .rst_n(rst_n), .setup(setup),
        .a_coef(a_coef), .b_coef(b_coef), .c_coef(c_coef),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits),
        .value_out(value_out)
    );

    always #5 clk = ~clk;

    integer x, y;

    initial begin
        rst_n = 0;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk);

        a_coef = {A_Z};
        b_coef = {B_Z};
        c_coef = {C_Z};
        frac_bits = {FRAC_BITS};
        setup = 1;
        @(negedge clk);
        setup = 0;

        for (y = {Y_MIN}; y <= {Y_MAX}; y = y + 1) begin
            if (y > {Y_MIN}) begin
                step_y = 1;
                @(negedge clk);
                step_y = 0;
            end
            for (x = {X_MIN}; x <= {X_MAX}; x = x + 1) begin
                if (x > {X_MIN}) begin
                    step_x = 1;
                    @(negedge clk);
                    step_x = 0;
                end
                $display("PX %0d %0d %0d", x, y, value_out);
            end
        end
        $finish;
    end
endmodule
"""


def gen_tb(a_z, b_z, c_z, frac_bits, x_min, x_max, y_min, y_max):
    return TB_TEMPLATE.format(
        A_Z=a_z, B_Z=b_z, C_Z=c_z, FRAC_BITS=frac_bits,
        X_MIN=x_min, X_MAX=x_max, Y_MIN=y_min, Y_MAX=y_max,
    )


def run_rtl(tb_src, build_dir, name):
    tb_path = build_dir / f"attr_stepper_tb_{name}.v"
    tb_path.write_text(tb_src)
    vvp_path = build_dir / f"attr_stepper_tb_{name}.vvp"
    subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path)]
        + [str(REPO / f) for f in RTL_FILES],
        check=True, cwd=REPO,
    )
    result = subprocess.run(["vvp", str(vvp_path)], check=True,
                             capture_output=True, text=True, cwd=REPO)
    got = {}
    for line in result.stdout.splitlines():
        if line.startswith("PX "):
            _, x, y, v = line.split()
            got[(int(x), int(y))] = int(v)
    return got


def main() -> int:
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)

    total_mismatches = 0
    for name, v0, v1, v2, z0, z1, z2 in TEST_CASES:
        A_z, B_z, C_z, frac_bits = depth_interp_setup(v0, v1, v2, z0, z1, z2)
        e0, e1, e2, D = triangle_edges(v0, v1, v2)
        xs = [v0[0], v1[0], v2[0]]
        ys = [v0[1], v1[1], v2[1]]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # spu_attr_stepper.v's `setup` seeds the accumulator directly with
        # c_coef and steps relative to that point (same convention as
        # spu_edge_stepper.v). This scan starts at (x_min, y_min), not the
        # formula's origin, so the seed must be the affine value AT
        # (x_min, y_min), not the raw C_z (the origin-relative constant).
        c_seed = C_z + A_z * x_min + B_z * y_min
        tb_src = gen_tb(signed_lit(A_z), signed_lit(B_z), signed_lit(c_seed),
                         frac_bits, x_min, x_max, y_min, y_max)
        got = run_rtl(tb_src, build_dir, name.replace(" ", "_").replace(",", ""))

        def inside(x, y):
            def f(e):
                a, b, c = e
                return a * x + b * y + c
            vals = [f(e0), f(e1), f(e2)]
            return all(v >= 0 for v in vals) or all(v <= 0 for v in vals)

        mismatches = 0
        checked = 0
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                if not inside(x, y):
                    continue
                checked += 1
                # Must match what the RTL actually computes: seeded with
                # c_seed (the affine value AT (x_min, y_min)), then
                # stepped by relative offsets -- NOT raw C_z with a
                # relative offset, which double-applies the (x_min, y_min)
                # shift (a bug caught here: an earlier version of this
                # reference used C_z instead of c_seed and mismatched on
                # every single pixel).
                acc = c_seed + A_z * (x - x_min) + B_z * (y - y_min)
                expected = acc >> frac_bits if acc >= 0 else -((-acc) >> frac_bits)
                rtl_val = got.get((x, y))
                if rtl_val is None or rtl_val != expected:
                    mismatches += 1
                    if mismatches <= 5:
                        print(f"  MISMATCH {name} ({x},{y}): expected {expected}, got {rtl_val}")

        print(f"{name}: {checked} covered pixels checked, {mismatches} mismatches")
        total_mismatches += mismatches

    if total_mismatches:
        print(f"FAIL: {total_mismatches} total mismatches")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
