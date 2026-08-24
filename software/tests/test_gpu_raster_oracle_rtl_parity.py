#!/usr/bin/env python3
"""test_gpu_raster_oracle_rtl_parity.py -- exhaustive bit-exact parity
between gpu_raster_oracle.py and the real RTL (spu_raster_unit.v +
spu_edge_stepper.v), over the full 640x480 target screen
(spu_video_timing.v's H_ACTIVE/V_ACTIVE), for several test triangles.

Written 2026-08-24 after an audit found spu_edge_stepper.v's edge test
had been a hardcoded stub (`inside_out = 1'b1`) and the one existing
testbench (spu_raster_tb.v) never actually exercised the outside-the-
triangle case despite its own comment claiming to -- both fixed same
day. This test is the real, exhaustive coverage check that should have
existed from the start: every pixel on the screen, compared against an
independent oracle, not two hand-picked points.

For each test triangle: generates a Verilog testbench that scans every
(x, y) in [0,640)x[0,480) in real raster order (row by row, matching
spu_gpu_top.v's actual step_x/step_y usage) and $display's every
covered pixel; the oracle independently computes the same triangle's
covered-pixel set from scratch (direct edge evaluation, not the RTL's
incremental accumulation); asserts the two sets are exactly equal.

Run:
  python3 software/tests/test_gpu_raster_oracle_rtl_parity.py

Requirements: iverilog + vvp in PATH.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software"))

from lib.gpu_raster_oracle import covered_pixels  # noqa: E402

WIDTH, HEIGHT = 640, 480

# (name, edges) -- edges is 3x (a, b, c) for "a*x + b*y + c >= 0".
# Chosen to stress cases the original vacuous testbench never touched:
# a triangle with a negative-coefficient edge, one whose bounding box
# runs off the right/bottom of the screen, and a thin sliver (few
# covered pixels, easy for an off-by-one to hide in a "looks about
# right" visual check but not in an exhaustive set-equality one).
TEST_TRIANGLES = [
    ("original_90_90_150_90_90_150",
     [(0, 1, -90), (1, 0, -90), (-1, -1, 240)]),
    # Triangle (600,400)-(900,400)-(600,700): mostly off-screen, but its
    # right-angle corner sits inside [0,640)x[0,480), so the screen's own
    # x/y bounds do the clipping (the hypotenuse x+y<=1300 never binds
    # on-screen) -- a genuine partial-visibility case, not just "empty".
    ("offscreen_partial_bottom_right",
     [(0, 1, -400), (1, 0, -600), (-1, -1, 1300)]),
    ("thin_sliver",
     [(0, 1, -200), (1, 0, -200), (-1, -3, 830)]),
]

TB_TEMPLATE = r"""
`timescale 1ns/1ps
module gpu_raster_parity_tb;
    reg clk = 0, rst_n = 0, setup = 0, step_x = 0, step_y = 0;
    wire covered;
    wire [3:0] pr, pg, pb;
    integer x, y;

    spu_raster_unit dut (
        .clk(clk), .rst_n(rst_n), .setup(setup),
        .a0({A0}), .b0({B0}), .c0({C0}),
        .a1({A1}), .b1({B1}), .c1({C1}),
        .a2({A2}), .b2({B2}), .c2({C2}),
        .step_x(step_x), .step_y(step_y), .x_span(16'sd{WIDTH}),
        .tri_r(4'hF), .tri_g(4'hF), .tri_b(4'hF),
        .covered(covered), .pixel_r(pr), .pixel_g(pg), .pixel_b(pb));

    always #10 clk = ~clk;

    initial begin
        #15 rst_n = 1;
        @(posedge clk); #1;
        setup = 1;
        @(posedge clk); #1;
        setup = 0;

        for (y = 0; y < {HEIGHT}; y = y + 1) begin
            if (y > 0) begin
                step_y = 1;
                @(posedge clk); #1;
                step_y = 0;
                @(posedge clk); #1;
            end
            if (covered) $display("COV %0d %0d", 0, y);
            for (x = 1; x < {WIDTH}; x = x + 1) begin
                step_x = 1;
                @(posedge clk); #1;
                step_x = 0;
                @(posedge clk); #1;
                if (covered) $display("COV %0d %0d", x, y);
            end
        end

        $display("SCAN DONE");
        $finish;
    end
endmodule
"""


def signed_lit(v: int, width: int) -> str:
    return f"{width}'sd{v}" if v >= 0 else f"-{width}'sd{-v}"


def gen_tb(edges) -> str:
    (a0, b0, c0), (a1, b1, c1), (a2, b2, c2) = edges
    return TB_TEMPLATE.format(
        A0=signed_lit(a0, 16), B0=signed_lit(b0, 16), C0=signed_lit(c0, 32),
        A1=signed_lit(a1, 16), B1=signed_lit(b1, 16), C1=signed_lit(c1, 32),
        A2=signed_lit(a2, 16), B2=signed_lit(b2, 16), C2=signed_lit(c2, 32),
        WIDTH=WIDTH, HEIGHT=HEIGHT,
    )


def run_rtl_scan(edges, build_dir: Path) -> set:
    tb_path = build_dir / "gpu_raster_parity_tb.v"
    tb_path.write_text(gen_tb(edges))
    vvp_path = build_dir / "gpu_raster_parity_tb.vvp"
    cc = subprocess.run(
        ["iverilog", "-g2012", "-o", str(vvp_path), str(tb_path),
         str(REPO / "hardware/rtl/gpu/spu_raster_unit.v"),
         str(REPO / "hardware/rtl/gpu/spu_edge_stepper.v")],
        capture_output=True, text=True,
    )
    if cc.returncode != 0:
        raise RuntimeError(f"iverilog compile failed:\n{cc.stdout}\n{cc.stderr}")
    rr = subprocess.run(["vvp", str(vvp_path)], capture_output=True, text=True)
    if "SCAN DONE" not in rr.stdout:
        raise RuntimeError(f"RTL scan did not complete:\n{rr.stdout}\n{rr.stderr}")
    covered = set()
    for line in rr.stdout.splitlines():
        if line.startswith("COV "):
            _, xs, ys = line.split()
            covered.add((int(xs), int(ys)))
    return covered


def main() -> int:
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)

    total_fail = 0
    for name, edges in TEST_TRIANGLES:
        oracle_set = covered_pixels(edges, WIDTH, HEIGHT)
        rtl_set = run_rtl_scan(edges, build_dir)

        missing_in_rtl = oracle_set - rtl_set
        extra_in_rtl = rtl_set - oracle_set

        if missing_in_rtl or extra_in_rtl:
            total_fail += 1
            print(f"FAIL: {name} -- oracle={len(oracle_set)} rtl={len(rtl_set)} "
                  f"missing_in_rtl={len(missing_in_rtl)} extra_in_rtl={len(extra_in_rtl)}")
            for pt in sorted(missing_in_rtl)[:5]:
                print(f"    missing in RTL (oracle says covered): {pt}")
            for pt in sorted(extra_in_rtl)[:5]:
                print(f"    extra in RTL (oracle says NOT covered): {pt}")
        else:
            print(f"PASS: {name} -- {len(oracle_set)}/{WIDTH*HEIGHT} pixels, "
                  f"exact set match against RTL")

    if total_fail:
        print(f"\nFAILED: {total_fail}/{len(TEST_TRIANGLES)} triangles mismatched")
        return 1
    print(f"\n{len(TEST_TRIANGLES)} triangles, exact pixel-set parity "
          f"(oracle vs RTL, full {WIDTH}x{HEIGHT} screen)")
    print("ALL GPU RASTER PARITY CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
