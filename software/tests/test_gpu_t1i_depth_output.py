#!/usr/bin/env python3
"""Cycle-level output-path isolation checks for T1i diagnostic modes."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software" / "tests"))
from test_gpu_t1i_uv import RTL_FILES  # noqa: E402

SCENE_PATH = ROOT / "fixtures/gpu_t1i_scene_a_wire_175b.hex"
SCENE_SHA256 = "8077acb3efbb92756fdee4c137500417e32f6f3664784c3b21f150c398d0dae9"
SCENE = bytes.fromhex(SCENE_PATH.read_text().strip())
if len(SCENE) != 175 or SCENE[0] != 0xA5 or hashlib.sha256(SCENE).hexdigest() != SCENE_SHA256:
    raise SystemExit("FAIL: T1i Scene A fixture length or frozen hash mismatch")

TB = r"""
`timescale 1ns/1ps
module t1i_depth_output_tb;
    parameter integer MODE=0;
    localparam integer H_ACTIVE=80,H_FP=2,H_SYNC=2,H_BP=2;
    localparam integer V_ACTIVE=100,V_FP=1,V_SYNC=1,V_BP=1;
    localparam integer HTOTAL=H_ACTIVE+H_FP+H_SYNC+H_BP;
    localparam integer VTOTAL=V_ACTIVE+V_FP+V_SYNC+V_BP;
    localparam [1391:0] SCENE_A=1392'h@@SCENE@@;
    reg clk=0,rst_n=0,rx_valid=0,check_enable=0;
    reg [7:0] rx_byte=0;
    integer errors=0,cycles=0,coverage_samples=0,winner_samples=0;
    integer bytes_sent=0;
    reg [3:0] winner_ids=0;
    reg [11:0] pre_palette=0;
    reg [1:0] pre_id=0;
    reg pre_valid=0,pre_hsync=0,pre_vsync=0,pre_active=0;
    wire [3:0] vr,vg,vb;
    wire vhs,vvs;

    spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1),.T1I_UV_SCENE(1),.T1I_DEPTH_DIAG(MODE),
        .H_ACTIVE(H_ACTIVE),.H_FP(H_FP),.H_SYNC(H_SYNC),.H_BP(H_BP),
        .V_ACTIVE(V_ACTIVE),.V_FP(V_FP),.V_SYNC(V_SYNC),.V_BP(V_BP)) dut (
        .clk_pixel(clk),.clk_tmds(clk),.rst_n(rst_n),
        .tri0_setup(1'b0),.tri0_a0(16'sd0),.tri0_b0(16'sd0),.tri0_c0(32'sd0),
        .tri0_a1(16'sd0),.tri0_b1(16'sd0),.tri0_c1(32'sd0),
        .tri0_a2(16'sd0),.tri0_b2(16'sd0),.tri0_c2(32'sd0),
        .tri0_r(4'd0),.tri0_g(4'd0),.tri0_b(4'd0),.tri0_z0(16'd0),.tri0_z1(16'd0),.tri0_z2(16'd0),
        .tri1_setup(1'b0),.tri1_a0(16'sd0),.tri1_b0(16'sd0),.tri1_c0(32'sd0),
        .tri1_a1(16'sd0),.tri1_b1(16'sd0),.tri1_c1(32'sd0),
        .tri1_a2(16'sd0),.tri1_b2(16'sd0),.tri1_c2(32'sd0),
        .tri1_r(4'd0),.tri1_g(4'd0),.tri1_b(4'd0),.tri1_z0(16'd0),.tri1_z1(16'd0),.tri1_z2(16'd0),
        .scene_rx_byte(rx_byte),.scene_rx_valid(rx_valid),
        .vga_r(vr),.vga_g(vg),.vga_b(vb),.vga_hsync(vhs),.vga_vsync(vvs),
        .tmds_clk_p(),.tmds_clk_n(),.tmds_d_p(),.tmds_d_n());

    always #1 clk=~clk;

    function [11:0] palette(input valid,input [1:0] id);
        begin
            palette={
                {4{valid && (~^id)}},
                {4{valid && id[0]}},
                {4{valid && id[1] && !id[0]}}
            };
        end
    endfunction

    task send_byte(input [7:0] value);
        begin
            @(negedge clk);rx_byte=value;rx_valid=1;
            @(negedge clk);rx_byte=0;rx_valid=0;
        end
    endtask

    // This scoreboard samples the combinational inputs before the active edge
    // and checks what the mode-3 output registers captured after that edge.
    always @(negedge clk) if(rst_n) begin
        pre_palette={dut.winner_diag_r,dut.winner_diag_g,dut.winner_diag_b};
        pre_valid=dut.raster_primitive_valid;
        pre_id=dut.raster_primitive_id;
        pre_hsync=dut.hsync_d;pre_vsync=dut.vsync_d;pre_active=dut.active_d;
    end

    always @(posedge clk) if(rst_n) begin
        cycles=cycles+1;
        #0.1;
        if(check_enable) begin
            if(MODE==0) begin
                if({dut.display_r,dut.display_g,dut.display_b} !== {dut.rast_r,dut.rast_g,dut.rast_b}) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL mode0: normal RGB changed");
                end
            end else if(MODE==1) begin
                if({dut.display_r,dut.display_g,dut.display_b} !==
                   {12{dut.any_armed_coverage}}) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL mode1: coverage-only white/black mismatch");
                end
            end else if(MODE==2) begin
                if({dut.display_r,dut.display_g,dut.display_b} !==
                   palette(dut.raster_primitive_valid,dut.raster_primitive_id)) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL mode2: combinational winner palette mismatch");
                end
            end else begin
                if(dut.t1i_depth_valid_q !== pre_valid ||
                   dut.t1i_depth_id_q !== pre_id ||
                   {dut.t1i_depth_r_q,dut.t1i_depth_g_q,dut.t1i_depth_b_q} !== pre_palette ||
                   dut.t1i_depth_hsync_q !== pre_hsync ||
                   dut.t1i_depth_vsync_q !== pre_vsync ||
                   dut.t1i_depth_active_q !== pre_active ||
                   vhs !== dut.t1i_depth_hsync_q || vvs !== dut.t1i_depth_vsync_q ||
                   dut.display_active !== dut.t1i_depth_active_q) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL mode3: registered winner/RGB/sync/active is not one cycle aligned");
                end
                if({dut.display_r,dut.display_g,dut.display_b} !==
                   {dut.t1i_depth_r_q,dut.t1i_depth_g_q,dut.t1i_depth_b_q}) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL mode3: registered RGB output differs from registered result");
                end
            end
            if(dut.active_d) begin
                coverage_samples=coverage_samples+1;
                if(dut.raster_primitive_valid) begin
                    winner_samples=winner_samples+1;
                    winner_ids[dut.raster_primitive_id]=1'b1;
                end
                if(MODE==2 && !dut.raster_primitive_valid &&
                   {dut.display_r,dut.display_g,dut.display_b} !== 12'd0) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL: invalid winner emitted colour");
                end
                if(MODE==3 && !dut.t1i_depth_valid_q &&
                   {dut.display_r,dut.display_g,dut.display_b} !== 12'd0) begin
                    errors=errors+1;
                    if(errors<8)$display("FAIL: registered invalid winner emitted colour");
                end
            end
        end
    end

    initial begin
        repeat(4)@(negedge clk);rst_n=1;repeat(2)@(negedge clk);
        send_byte(8'hA5);
        for(bytes_sent=0;bytes_sent<174;bytes_sent=bytes_sent+1)
            send_byte(SCENE_A[bytes_sent*8+:8]);
        wait(dut.activate_scene);
        @(posedge clk);#0.1;check_enable=1;
        repeat(HTOTAL*VTOTAL*2)@(posedge clk);
        check_enable=0;
        if(coverage_samples<8000 || winner_samples==0) begin
            errors=errors+1;
            $display("FAIL: insufficient active/covered samples active=%0d covered=%0d",coverage_samples,winner_samples);
        end
        if((MODE==2 || MODE==3) && winner_ids!==4'b1111) begin
            errors=errors+1;
            $display("FAIL: Scene A did not exercise all winner IDs; mask=%b",winner_ids);
        end
        if(errors==0)
            $display("PASS: T1i depth output mode=%0d active=%0d covered=%0d winner_mask=%b",MODE,coverage_samples,winner_samples,winner_ids);
        else $display("FAIL: T1i depth output mode=%0d errors=%0d",MODE,errors);
        $finish;
    end
    initial begin #200000000;$display("FAIL: depth output test timeout");$finish;end
endmodule
"""


def main() -> int:
    scene = int.from_bytes(SCENE[1:], "little")
    tb_text = TB.replace("@@SCENE@@", f"{scene:0348x}")
    files = [str(ROOT / path) for path in RTL_FILES]
    with tempfile.TemporaryDirectory(prefix="spu_t1i_depth_output_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1i_depth_output_tb.v"
        tb.write_text(tb_text)
        invalid_tb = temp / "invalid_profile_tb.v"
        invalid_tb.write_text(r'''module invalid_profile_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1I_UV_SCENE(0),.T1I_DEPTH_DIAG(1)) dut();
    endmodule
''')
        invalid = subprocess.run([
            "iverilog", "-g2012", "-s", "invalid_profile_tb", "-o",
            str(temp / "invalid_profile.vvp"), str(invalid_tb), *files,
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        if invalid.returncode == 0 or "T1I_depth_diag_requires_uv_scene" not in invalid.stderr:
            print("FAIL: depth diagnostic without T1i prepared scene did not fail elaboration")
            print(invalid.stderr)
            return 1
        for mode in range(4):
            out = temp / f"mode_{mode}.vvp"
            compiled = subprocess.run([
                "iverilog", "-g2012", "-s", "t1i_depth_output_tb", "-P",
                f"t1i_depth_output_tb.MODE={mode}", "-o", str(out), str(tb), *files,
            ], cwd=ROOT, text=True, capture_output=True, check=False)
            if compiled.returncode:
                print(compiled.stderr)
                return 1
            result = subprocess.run(["vvp", str(out)], cwd=ROOT, text=True,
                                    capture_output=True, check=False, timeout=60)
            marker = f"PASS: T1i depth output mode={mode} "
            if result.returncode or marker not in result.stdout:
                print(result.stdout[-3000:])
                print(result.stderr)
                return 1
    print("PASS: T1i coverage-only, combinational winner, registered winner and default RGB modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
