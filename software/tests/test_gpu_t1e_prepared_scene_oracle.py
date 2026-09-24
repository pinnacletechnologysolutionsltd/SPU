#!/usr/bin/env python3
"""Q2 qualification of the frozen prepared-scene oracle through spu_gpu_top.

This is a focused T1e test. It injects the unchanged 64-byte T1d wire scene
through spu_gpu_top's PREPARED_SCENE byte interface, then samples the real VGA
consumer at the six frozen coordinates from q1_fixture_oracle_proposal.md.

It deliberately does not modify RTL, the fixture, or board artifacts. The
generated Verilog testbench is held in a temporary directory.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "gpu_t1d_scene_wire_64b.bin"

RTL_FILES = [
    "hardware/rtl/gpu/spu_gpu_top.v",
    "hardware/rtl/gpu/spu_video_timing.v",
    "hardware/rtl/gpu/spu_scene_loader.v",
    "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v",
    "hardware/rtl/gpu/spu_prepared_scene_control.v",
    "hardware/rtl/gpu/spu_dual_raster.v",
    "hardware/rtl/gpu/spu_raster_unit.v",
    "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_depth_dispatch4.v",
    "hardware/rtl/gpu/spu_prepared_scalar_attribute4.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
    "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v",
    "hardware/rtl/hal/hal_vga.v",
    "hardware/rtl/hal/hal_hdmi.v",
    "hardware/rtl/hal/hal_hdmi_tmds.v",
    "hardware/rtl/hal/hal_hdmi_serdes_a7.v",
]


TB_TEMPLATE = r'''
`timescale 1ns/1ps

module t1e_prepared_scene_tb;
    localparam [503:0] SCENE = 504'h{scene_hex};

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg [7:0] scene_rx_byte = 8'h00;
    reg scene_rx_valid = 1'b0;
    wire [3:0] vga_r, vga_g, vga_b;
    wire vga_hsync, vga_vsync;

    spu_gpu_top #(
        .DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1)
    ) dut (
        .clk_pixel(clk), .clk_tmds(clk), .rst_n(rst_n),
        .tri0_setup(1'b0),
        .tri0_a0(16'sd0), .tri0_b0(16'sd0), .tri0_c0(32'sd0),
        .tri0_a1(16'sd0), .tri0_b1(16'sd0), .tri0_c1(32'sd0),
        .tri0_a2(16'sd0), .tri0_b2(16'sd0), .tri0_c2(32'sd0),
        .tri0_r(4'd0), .tri0_g(4'd0), .tri0_b(4'd0),
        .tri0_z0(16'd0), .tri0_z1(16'd0), .tri0_z2(16'd0),
        .tri1_setup(1'b0),
        .tri1_a0(16'sd0), .tri1_b0(16'sd0), .tri1_c0(32'sd0),
        .tri1_a1(16'sd0), .tri1_b1(16'sd0), .tri1_c1(32'sd0),
        .tri1_a2(16'sd0), .tri1_b2(16'sd0), .tri1_c2(32'sd0),
        .tri1_r(4'd0), .tri1_g(4'd0), .tri1_b(4'd0),
        .tri1_z0(16'd0), .tri1_z1(16'd0), .tri1_z2(16'd0),
        .scene_rx_byte(scene_rx_byte), .scene_rx_valid(scene_rx_valid),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync),
        .tmds_clk_p(), .tmds_clk_n(), .tmds_d_p(), .tmds_d_n()
    );

    always #1 clk = ~clk;

    integer failures = 0;
    integer seen_mask = 0;
    integer x_ref, y_ref;
    integer guard_cycles = 0;

    task send_byte(input [7:0] value);
        begin
            @(negedge clk);
            scene_rx_byte = value;
            scene_rx_valid = 1'b1;
            @(negedge clk);
            scene_rx_valid = 1'b0;
            scene_rx_byte = 8'h00;
        end
    endtask

    task check_pixel(
        input integer px, input integer py, input integer bit_no,
        input [3:0] expected_r, input [3:0] expected_g,
        input [3:0] expected_b, input [8*32-1:0] label
    );
        begin
            seen_mask = seen_mask | (1 << bit_no);
            if ({{vga_r, vga_g, vga_b}} !==
                {{expected_r, expected_g, expected_b}}) begin
                failures = failures + 1;
                $display("FAIL: (%0d,%0d) %0s expected RGB=%0d,%0d,%0d got=%0d,%0d,%0d",
                    px, py, label, expected_r, expected_g, expected_b,
                    vga_r, vga_g, vga_b);
            end else begin
                $display("ORACLE: (%0d,%0d) %0s RGB=%0d,%0d,%0d",
                    px, py, label, vga_r, vga_g, vga_b);
            end
        end
    endtask

    task sample_if_target;
        begin
            if (dut.active_d) begin
                if (x_ref == 10 && y_ref == 10 && !(seen_mask & (1 << 0)))
                    check_pixel(10, 10, 0, 4'd0, 4'd0, 4'd0, "background");
                if (x_ref == 100 && y_ref == 300 && !(seen_mask & (1 << 1)))
                    check_pixel(100, 300, 1, 4'd15, 4'd0, 4'd0, "unit0_only");
                if (x_ref == 540 && y_ref == 300 && !(seen_mask & (1 << 2)))
                    check_pixel(540, 300, 2, 4'd0, 4'd15, 4'd0, "unit1_only");
                if (x_ref == 200 && y_ref == 100 && !(seen_mask & (1 << 3)))
                    check_pixel(200, 100, 3, 4'd15, 4'd0, 4'd0, "unit0_nearer");
                if (x_ref == 400 && y_ref == 100 && !(seen_mask & (1 << 4)))
                    check_pixel(400, 100, 4, 4'd0, 4'd15, 4'd0, "unit1_nearer");
                if (x_ref == 320 && y_ref == 100 && !(seen_mask & (1 << 5)))
                    check_pixel(320, 100, 5, 4'd15, 4'd0, 4'd0, "equal_depth_unit0");
            end
        end
    endtask

    integer i;
    initial begin
        repeat (5) @(negedge clk);
        rst_n = 1'b1;

        send_byte(8'hA5);
        for (i = 0; i < 63; i = i + 1)
            send_byte(SCENE[i*8 +: 8]);

        // The qualified scene activation occurs only at a frame boundary.
        // Confirm the raw scene bank first, then observe a complete later
        // frame so setup and the existing one-cycle VGA alignment are settled.
        wait (dut.active_scene === SCENE);
        wait (dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0);
        @(posedge clk);
        while (dut.u_timing.y == 10'd0 && dut.u_timing.x == 10'd0)
            @(posedge clk);
        while (!(dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0))
            @(posedge clk);

        while (seen_mask != 63 && guard_cycles <= 430000) begin
            x_ref = dut.u_timing.x;
            y_ref = dut.u_timing.y;
            @(posedge clk);
            #1;
            sample_if_target();
            guard_cycles = guard_cycles + 1;
        end

        if (seen_mask != 63) begin
            $display("FAIL: target oracle did not complete; seen_mask=%0d", seen_mask);
            failures = failures + 1;
        end
        begin
            if (dut.active_scene !== SCENE) begin
                $display("FAIL: active scene changed during capture");
                failures = failures + 1;
            end
            if (failures == 0)
                $display("PASS: T1e-Q2 prepared-scene top-level oracle");
            else
                $display("FAIL: T1e-Q2 failures=%0d", failures);
            $finish;
        end
    end
endmodule
'''


def main() -> int:
    wire = FIXTURE.read_bytes()
    if len(wire) != 64 or wire[0] != 0xA5:
        raise AssertionError("frozen fixture must be 64 bytes beginning with A5")
    scene = int.from_bytes(wire[1:], "little")
    scene_hex = f"{scene:0126x}"

    with tempfile.TemporaryDirectory(prefix="spu_t1e_q2_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1e_prepared_scene_tb.v"
        vvp = temp / "t1e_prepared_scene_tb.vvp"
        tb.write_text(TB_TEMPLATE.format(scene_hex=scene_hex))
        compile_cmd = [
            "iverilog", "-g2012", "-s", "t1e_prepared_scene_tb",
            "-o", str(vvp), str(tb),
            *[str(ROOT / item) for item in RTL_FILES],
        ]
        compiled = subprocess.run(
            compile_cmd, cwd=ROOT, text=True, capture_output=True,
            check=False,
        )
        if compiled.returncode != 0:
            print(compiled.stdout, end="")
            print(compiled.stderr, end="", file=sys.stderr)
            return compiled.returncode

        result = subprocess.run(
            ["vvp", str(vvp)], cwd=ROOT, text=True,
            capture_output=True, check=False, timeout=55,
        )
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
