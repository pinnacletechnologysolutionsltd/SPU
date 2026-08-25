#!/usr/bin/env python3
"""test_gpu_depth_compare_integration.py -- end-to-end integration test:
spu_dual_raster + spu_depth_dispatch + two spu_attr_stepper +
spu_depth_compare wired together exactly as a real consumer would, on
two DELIBERATELY OVERLAPPING triangles where unit 1 is nearer (smaller
depth) than unit 0 in the overlap region.

This is the test that actually distinguishes correct depth-based
selection from the old fixed-priority behavior (unit 0 always wins
when covered): if spu_depth_compare's wiring were wrong -- e.g. depth0/
depth1 swapped, or the comparison inverted -- this test would still
show *a* plausible-looking image (some pixels one color, some another),
just the wrong one. Only a real independent-oracle pixel-by-pixel check
against the exact expected winner catches that. Testing the standalone
module in isolation (test_gpu_depth_compare_rtl_parity.py) already
proved its truth table; this proves the truth table is being fed the
right signals in a real assembly.

Run:
  python3 software/tests/test_gpu_depth_compare_integration.py

Requirements: iverilog + vvp in PATH.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))

from gpu_depth_v2_oracle import triangle_edges  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_dual_raster.v",
    "hardware/rtl/gpu/spu_raster_unit.v",
    "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
    "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v",
]

# Unit 0: large, "far" (z=50000). Unit 1: overlapping, "near" (z=10000).
# Smaller depth wins (nearer), so unit 1 should show through wherever
# both cover the same pixel, despite spu_dual_raster's fixed-priority
# pixel_r/g/b (unused here) always favoring unit 0.
V0_0, V1_0, V2_0 = (50, 50), (400, 60), (200, 300)
Z_0 = (50000, 50000, 50000)
V0_1, V1_1, V2_1 = (150, 100), (450, 150), (300, 400)
Z_1 = (10000, 10000, 10000)

TRI_R0, TRI_G0, TRI_B0 = 1, 2, 3     # unit 0's flat color
TRI_R1, TRI_G1, TRI_B1 = 15, 0, 8    # unit 1's flat color

SCAN_W, SCAN_H = 260, 180


def signed_lit(v: int, width: int) -> str:
    return f"{width}'sd{v}" if v >= 0 else f"-{width}'sd{-v}"


TB_TEMPLATE = r"""
`timescale 1ns/1ps
module depth_compare_integration_tb;
    reg clk = 0, rst_n = 0;
    reg setup0 = 0, setup1 = 0, depth_setup0 = 0, depth_setup1 = 0;
    reg attr_setup0 = 0, attr_setup1 = 0;
    reg step_x = 0, step_y = 0;

    wire cov0, cov1;
    wire [3:0] r0, g0, b0, r1, g1, b1;
    wire [3:0] dummy_pixel_r, dummy_pixel_g, dummy_pixel_b;

    spu_dual_raster u_rast (
        .clk(clk), .rst_n(rst_n),
        .setup0(setup0),
        .a0_0({A0_0}), .b0_0({B0_0}), .c0_0({C0_0}),
        .a1_0({A1_0}), .b1_0({B1_0}), .c1_0({C1_0}),
        .a2_0({A2_0}), .b2_0({B2_0}), .c2_0({C2_0}),
        .tri_r0(4'd{TRI_R0}), .tri_g0(4'd{TRI_G0}), .tri_b0(4'd{TRI_B0}),
        .setup1(setup1),
        .a0_1({A0_1}), .b0_1({B0_1}), .c0_1({C0_1}),
        .a1_1({A1_1}), .b1_1({B1_1}), .c1_1({C1_1}),
        .a2_1({A2_1}), .b2_1({B2_1}), .c2_1({C2_1}),
        .tri_r1(4'd{TRI_R1}), .tri_g1(4'd{TRI_G1}), .tri_b1(4'd{TRI_B1}),
        .step_x(step_x), .step_y(step_y), .x_span(16'sd640),
        .pixel_r(dummy_pixel_r), .pixel_g(dummy_pixel_g), .pixel_b(dummy_pixel_b),
        .cov0_out(cov0), .cov1_out(cov1),
        .r0_out(r0), .g0_out(g0), .b0_out(b0),
        .r1_out(r1), .g1_out(g1), .b1_out(b1)
    );

    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire [6:0] frac_bits0, frac_bits1;
    wire ready0, ready1;

    spu_depth_dispatch u_dispatch (
        .clk(clk), .rst_n(rst_n),
        .depth_setup0(depth_setup0), .depth_setup1(depth_setup1),
        .a0_0({A0_0}), .b0_0({B0_0}), .a1_0({A1_0}), .b1_0({B1_0}), .a2_0({A2_0}), .b2_0({B2_0}),
        .c0_0({C0_0}), .c1_0({C1_0}), .c2_0({C2_0}),
        .z0_0(16'd{Z0_0}), .z1_0(16'd{Z1_0}), .z2_0(16'd{Z2_0}),
        .a0_1({A0_1}), .b0_1({B0_1}), .a1_1({A1_1}), .b1_1({B1_1}), .a2_1({A2_1}), .b2_1({B2_1}),
        .c0_1({C0_1}), .c1_1({C1_1}), .c2_1({C2_1}),
        .z0_1(16'd{Z0_1}), .z1_1(16'd{Z1_1}), .z2_1(16'd{Z2_1}),
        .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
        .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1)
    );

    wire signed [55:0] depth0, depth1;
    spu_attr_stepper u_attr0 (
        .clk(clk), .rst_n(rst_n), .setup(attr_setup0),
        .a_coef(A_z0), .b_coef(B_z0), .c_coef(C_z0),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits0),
        .value_out(depth0)
    );
    spu_attr_stepper u_attr1 (
        .clk(clk), .rst_n(rst_n), .setup(attr_setup1),
        .a_coef(A_z1), .b_coef(B_z1), .c_coef(C_z1),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits1),
        .value_out(depth1)
    );

    wire [3:0] pixel_r, pixel_g, pixel_b;
    spu_depth_compare u_compare (
        .cov0(cov0), .cov1(cov1), .depth0(depth0), .depth1(depth1),
        .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
        .pixel_r(pixel_r), .pixel_g(pixel_g), .pixel_b(pixel_b)
    );

    always #5 clk = ~clk;

    integer x, y;
    reg seen_ready0 = 0, seen_ready1 = 0;
    always @(posedge clk) begin
        if (ready0) seen_ready0 <= 1'b1;
        if (ready1) seen_ready1 <= 1'b1;
    end

    initial begin
        rst_n = 0;
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk);

        setup0 = 1; setup1 = 1; depth_setup0 = 1; depth_setup1 = 1;
        @(negedge clk);
        setup0 = 0; setup1 = 0; depth_setup0 = 0; depth_setup1 = 0;

        // spu_depth_dispatch serializes the two units (shared FSM/multiplier,
        // see spu_strategy/contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md
        // §8) -- ready0 and ready1 pulse on DIFFERENT cycles, never together.
        while (!(seen_ready0 && seen_ready1)) @(negedge clk);
        @(negedge clk);

        attr_setup0 = 1; attr_setup1 = 1;
        @(negedge clk);
        attr_setup0 = 0; attr_setup1 = 0;

        for (y = 0; y < {SCAN_H}; y = y + 1) begin
            if (y > 0) begin
                step_y = 1;
                @(negedge clk);
                step_y = 0;
            end
            for (x = 0; x < {SCAN_W}; x = x + 1) begin
                if (x > 0) begin
                    step_x = 1;
                    @(negedge clk);
                    step_x = 0;
                end
                $display("PX %0d %0d %0d %0d %0d", x, y, pixel_r, pixel_g, pixel_b);
            end
        end
        $finish;
    end
endmodule
"""


def gen_tb(e0, e1):
    (a0_0, b0_0, c0_0), (a1_0, b1_0, c1_0), (a2_0, b2_0, c2_0) = e0
    (a0_1, b0_1, c0_1), (a1_1, b1_1, c1_1), (a2_1, b2_1, c2_1) = e1
    return TB_TEMPLATE.format(
        A0_0=signed_lit(a0_0, 16), B0_0=signed_lit(b0_0, 16), C0_0=signed_lit(c0_0, 32),
        A1_0=signed_lit(a1_0, 16), B1_0=signed_lit(b1_0, 16), C1_0=signed_lit(c1_0, 32),
        A2_0=signed_lit(a2_0, 16), B2_0=signed_lit(b2_0, 16), C2_0=signed_lit(c2_0, 32),
        A0_1=signed_lit(a0_1, 16), B0_1=signed_lit(b0_1, 16), C0_1=signed_lit(c0_1, 32),
        A1_1=signed_lit(a1_1, 16), B1_1=signed_lit(b1_1, 16), C1_1=signed_lit(c1_1, 32),
        A2_1=signed_lit(a2_1, 16), B2_1=signed_lit(b2_1, 16), C2_1=signed_lit(c2_1, 32),
        TRI_R0=TRI_R0, TRI_G0=TRI_G0, TRI_B0=TRI_B0,
        TRI_R1=TRI_R1, TRI_G1=TRI_G1, TRI_B1=TRI_B1,
        Z0_0=Z_0[0], Z1_0=Z_0[1], Z2_0=Z_0[2],
        Z0_1=Z_1[0], Z1_1=Z_1[1], Z2_1=Z_1[2],
        SCAN_W=SCAN_W, SCAN_H=SCAN_H,
    )


def inside(edges, x, y):
    def f(e):
        a, b, c = e
        return a * x + b * y + c
    vals = [f(e) for e in edges]
    return all(v >= 0 for v in vals) or all(v <= 0 for v in vals)


def main() -> int:
    e0 = triangle_edges(V0_0, V1_0, V2_0)[:3]
    e1 = triangle_edges(V0_1, V1_1, V2_1)[:3]

    tb_src = gen_tb(e0, e1)
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)
    tb_path = build_dir / "depth_compare_integration_tb.v"
    tb_path.write_text(tb_src)
    vvp_path = build_dir / "depth_compare_integration_tb.vvp"
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
            _, x, y, r, g, b = line.split()
            got[(int(x), int(y))] = (int(r), int(g), int(b))

    mismatches = 0
    checked = 0
    overlap_checked = 0
    overlap_unit1_wins = 0
    for y in range(SCAN_H):
        for x in range(SCAN_W):
            c0 = inside(e0, x, y)
            c1 = inside(e1, x, y)
            if c0 and c1:
                # depth0 (50000-ish) > depth1 (10000-ish) always for these
                # flat, uniform-depth triangles -- unit 1 (nearer) must win.
                expected = (TRI_R1, TRI_G1, TRI_B1)
                overlap_checked += 1
            elif c0:
                expected = (TRI_R0, TRI_G0, TRI_B0)
            elif c1:
                expected = (TRI_R1, TRI_G1, TRI_B1)
            else:
                expected = (0, 0, 0)
            checked += 1
            rtl = got.get((x, y))
            if rtl != expected:
                mismatches += 1
                if mismatches <= 10:
                    print(f"  MISMATCH ({x},{y}): cov=({c0},{c1}) expected {expected} got {rtl}")
            elif c0 and c1 and rtl == (TRI_R1, TRI_G1, TRI_B1):
                overlap_unit1_wins += 1

    print(f"{checked} pixels checked, {overlap_checked} in the overlap region, "
          f"{overlap_unit1_wins} correctly won by the nearer unit 1, "
          f"{mismatches} mismatches")
    if mismatches:
        return 1
    if overlap_checked == 0:
        print("FAIL: no overlap pixels were exercised -- test doesn't "
              "actually distinguish depth-based selection from fixed priority")
        return 1
    if overlap_unit1_wins != overlap_checked:
        print("FAIL: not every overlap pixel was won by the nearer unit")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
