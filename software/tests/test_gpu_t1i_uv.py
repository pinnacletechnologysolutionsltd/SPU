#!/usr/bin/env python3
"""T1i independent U/V interpolation and atomic-scene simulation oracle."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software" / "lib"))
from gpu_depth_v2_oracle import full_reciprocal  # noqa: E402

RTL_FILES = [
    "hardware/rtl/gpu/spu_gpu_top.v", "hardware/rtl/gpu/spu_video_timing.v",
    "hardware/rtl/gpu/spu_scene_loader.v", "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v",
    "hardware/rtl/gpu/spu_prepared_scene_control.v",
    "hardware/rtl/gpu/spu_prepared_scene_control4.v",
    "hardware/rtl/gpu/spu_dual_raster.v", "hardware/rtl/gpu/spu_quad_raster.v",
    "hardware/rtl/gpu/spu_raster_unit.v", "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_depth_dispatch.v", "hardware/rtl/gpu/spu_depth_dispatch4.v",
    "hardware/rtl/gpu/spu_prepared_scalar_attribute4.v",
    "hardware/rtl/gpu/spu_material_op_select4.v",
    "hardware/rtl/gpu/spu_material_predicate_select4.v",
    "hardware/rtl/gpu/spu_pixel_output_register.v",
    "hardware/rtl/gpu/spu_depth_math.v", "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v", "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v", "hardware/rtl/gpu/spu_depth_compare4.v",
    "hardware/rtl/hal/hal_vga.v", "hardware/rtl/hal/hal_hdmi.v",
    "hardware/rtl/hal/hal_hdmi_tmds.v", "hardware/rtl/hal/hal_hdmi_serdes_a7.v",
]

TB = r"""
`timescale 1ns/1ps
module t1i_uv_tb;
    parameter integer DIAG=0;
    parameter integer REG_UV=0;
    parameter integer OUT_REG=0;
    parameter integer PROC=0;
    parameter integer GRID=0;
    parameter integer VIS_DIAG=0;
    parameter integer T1L_MAT=0;
    parameter integer T1L_PIPE=0;
    parameter integer T1M_ALU=0;
    parameter integer T1M_OP=0;
    parameter integer T1N=0;
    parameter integer T1O=0;
    parameter integer T1P=0;
    parameter [7:0] T1N_OP_A=8'h00, T1N_OP_B=8'h01, T1N_OP_C=8'h02;
    parameter [31:0] T1O_OPS_A=32'h02030405;
    parameter [31:0] T1O_OPS_B=32'h03040500;
    parameter [31:0] T1O_OPS_C=32'h04050001;
    parameter [31:0] T1P_OPS_A=32'h02020202, T1P_OPS_B=32'h02020202,
                     T1P_OPS_C=32'h02020202;
    parameter [31:0] T1P_SEL_A=32'hcccccccc, T1P_SEL_B=32'hd9aa8e89,
                     T1P_SEL_C=32'hf88ed8bd;
    parameter integer H_ACTIVE=80, H_FP=2, H_SYNC=2, H_BP=2;
    parameter integer V_ACTIVE=100, V_FP=1, V_SYNC=1, V_BP=1;
    parameter integer CHECK_W=H_ACTIVE, CHECK_H=V_ACTIVE;
    localparam integer HTOTAL=H_ACTIVE+H_FP+H_SYNC+H_BP;
    localparam integer SCENE_WIDTH=1392+8*T1N+32*T1O+64*T1P;
    localparam [SCENE_WIDTH-1:0] SCENE_A=T1P ?
        {T1P_SEL_A,T1P_OPS_A,1392'h@@SCENE_A@@} : T1O ?
        {T1O_OPS_A,1392'h@@SCENE_A@@} : {T1N_OP_A,1392'h@@SCENE_A@@};
    localparam [SCENE_WIDTH-1:0] SCENE_B=T1P ?
        {T1P_SEL_B,T1P_OPS_B,1392'h@@SCENE_B@@} : T1O ?
        {T1O_OPS_B,1392'h@@SCENE_B@@} : {T1N_OP_B,1392'h@@SCENE_B@@};
    localparam [SCENE_WIDTH-1:0] SCENE_C=T1P ?
        {T1P_SEL_C,T1P_OPS_C,1392'h@@SCENE_C@@} : T1O ?
        {T1O_OPS_C,1392'h@@SCENE_C@@} : {T1N_OP_C,1392'h@@SCENE_C@@};
    localparam [SCENE_WIDTH-1:0] SCENE_BAD={8'h06,1392'h@@SCENE_A@@};
    reg clk=0,rst_n=0,rx_valid=0;
    reg [7:0] rx_byte=0;
    integer failures=0,pixels=0,cycles=0,x,y,j,k;
    integer class_counts[0:3];
    integer changed_b=0,changed_c=0,return_mismatches=0;
    reg [7:0] expected_t1n_op=8'd0;
    reg [31:0] expected_t1o_ops=32'd0;
    reg [31:0] expected_t1p_selectors=32'd0;
    reg expected_t1n_generation=1'b0;
    reg [1:0] pattern_a[0:H_ACTIVE*V_ACTIVE-1];
    wire [3:0] vr,vg,vb;
    wire [223:0] active_u_a={dut.u_t1i_u.active_A_attr3,dut.u_t1i_u.active_A_attr2,
        dut.u_t1i_u.active_A_attr1,dut.u_t1i_u.active_A_attr0};
    wire [223:0] active_v_a={dut.u_t1i_v.active_A_attr3,dut.u_t1i_v.active_A_attr2,
        dut.u_t1i_v.active_A_attr1,dut.u_t1i_v.active_A_attr0};
    wire [223:0] active_u_b={dut.u_t1i_u.active_B_attr3,dut.u_t1i_u.active_B_attr2,
        dut.u_t1i_u.active_B_attr1,dut.u_t1i_u.active_B_attr0};
    wire [223:0] active_v_b={dut.u_t1i_v.active_B_attr3,dut.u_t1i_v.active_B_attr2,
        dut.u_t1i_v.active_B_attr1,dut.u_t1i_v.active_B_attr0};
    wire [223:0] active_u_c={dut.u_t1i_u.active_C_attr3,dut.u_t1i_u.active_C_attr2,
        dut.u_t1i_u.active_C_attr1,dut.u_t1i_u.active_C_attr0};
    wire [223:0] active_v_c={dut.u_t1i_v.active_C_attr3,dut.u_t1i_v.active_C_attr2,
        dut.u_t1i_v.active_C_attr1,dut.u_t1i_v.active_C_attr0};
    wire [27:0] active_u_frac={dut.u_t1i_u.active_frac_attr3,dut.u_t1i_u.active_frac_attr2,
        dut.u_t1i_u.active_frac_attr1,dut.u_t1i_u.active_frac_attr0};
    wire [27:0] active_v_frac={dut.u_t1i_v.active_frac_attr3,dut.u_t1i_v.active_frac_attr2,
        dut.u_t1i_v.active_frac_attr1,dut.u_t1i_v.active_frac_attr0};
    wire [1343:0] active_uv_coefficients={active_u_a,active_u_b,active_u_c,
        active_v_a,active_v_b,active_v_c};
    wire [55:0] active_uv_frac={active_u_frac,active_v_frac};
    wire [1343:0] candidate_uv_coefficients={
        dut.u_t1i_u.candidate_A_attr3,dut.u_t1i_u.candidate_A_attr2,
        dut.u_t1i_u.candidate_A_attr1,dut.u_t1i_u.candidate_A_attr0,
        dut.u_t1i_u.candidate_B_attr3,dut.u_t1i_u.candidate_B_attr2,
        dut.u_t1i_u.candidate_B_attr1,dut.u_t1i_u.candidate_B_attr0,
        dut.u_t1i_u.candidate_C_attr3,dut.u_t1i_u.candidate_C_attr2,
        dut.u_t1i_u.candidate_C_attr1,dut.u_t1i_u.candidate_C_attr0,
        dut.u_t1i_v.candidate_A_attr3,dut.u_t1i_v.candidate_A_attr2,
        dut.u_t1i_v.candidate_A_attr1,dut.u_t1i_v.candidate_A_attr0,
        dut.u_t1i_v.candidate_B_attr3,dut.u_t1i_v.candidate_B_attr2,
        dut.u_t1i_v.candidate_B_attr1,dut.u_t1i_v.candidate_B_attr0,
        dut.u_t1i_v.candidate_C_attr3,dut.u_t1i_v.candidate_C_attr2,
        dut.u_t1i_v.candidate_C_attr1,dut.u_t1i_v.candidate_C_attr0};
    wire [55:0] candidate_uv_frac={
        dut.u_t1i_u.candidate_frac_attr3,dut.u_t1i_u.candidate_frac_attr2,
        dut.u_t1i_u.candidate_frac_attr1,dut.u_t1i_u.candidate_frac_attr0,
        dut.u_t1i_v.candidate_frac_attr3,dut.u_t1i_v.candidate_frac_attr2,
        dut.u_t1i_v.candidate_frac_attr1,dut.u_t1i_v.candidate_frac_attr0};
    wire [1343:0] uv_reanchor={
        dut.u_t1i_u.u_scalar0.a_r,dut.u_t1i_u.u_scalar0.b_r,dut.u_t1i_u.u_scalar0.acc,
        dut.u_t1i_u.u_scalar1.a_r,dut.u_t1i_u.u_scalar1.b_r,dut.u_t1i_u.u_scalar1.acc,
        dut.u_t1i_u.u_scalar2.a_r,dut.u_t1i_u.u_scalar2.b_r,dut.u_t1i_u.u_scalar2.acc,
        dut.u_t1i_u.u_scalar3.a_r,dut.u_t1i_u.u_scalar3.b_r,dut.u_t1i_u.u_scalar3.acc,
        dut.u_t1i_v.u_scalar0.a_r,dut.u_t1i_v.u_scalar0.b_r,dut.u_t1i_v.u_scalar0.acc,
        dut.u_t1i_v.u_scalar1.a_r,dut.u_t1i_v.u_scalar1.b_r,dut.u_t1i_v.u_scalar1.acc,
        dut.u_t1i_v.u_scalar2.a_r,dut.u_t1i_v.u_scalar2.b_r,dut.u_t1i_v.u_scalar2.acc,
        dut.u_t1i_v.u_scalar3.a_r,dut.u_t1i_v.u_scalar3.b_r,dut.u_t1i_v.u_scalar3.acc};
    reg [1343:0] first_a_uv_coefficients;
    reg [55:0] first_a_uv_frac;
    reg [1343:0] first_a_uv_reanchor;
    reg first_a_seen=0;
    spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1),.T1I_UV_SCENE(1),.T1I_UV_DIAG(DIAG),
        .T1I_UV_REG_DIAG(REG_UV),
        .T1J_PROC_SHADE(PROC || VIS_DIAG),
        .T1J_CHECKER_VIS_DIAG(VIS_DIAG),
        .T1K_GRID_SHADE(GRID),
        .T1L_MATERIAL_OP(T1L_MAT),
        .T1L_PIPELINE_PARTITION(T1L_PIPE),
        .T1M_FRAGMENT_ALU(T1M_ALU),
        .T1M_ALU_OP(T1M_OP),
        .T1N_RUNTIME_MATERIAL(T1N),
        .T1O_PER_PRIMITIVE_MATERIAL(T1O),
        .T1P_PER_PRIMITIVE_PREDICATES(T1P),
        .GPU_POST_WINNER_REG(OUT_REG),
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
        .vga_r(vr),.vga_g(vg),.vga_b(vb),.vga_hsync(),.vga_vsync(),
        .tmds_clk_p(),.tmds_clk_n(),.tmds_d_p(),.tmds_d_n());
    wire signed [55:0] t1j_selected_u_q, t1j_selected_v_q;
    wire t1j_selected_uv_valid_q;
    generate
        if (PROC || GRID || VIS_DIAG || T1L_MAT!=0 || T1M_ALU || T1N || T1O || T1P) begin: t1j_test_hierarchical_taps
            assign t1j_selected_u_q=dut.t1j_registered_uv_shader.selected_u_q;
            assign t1j_selected_v_q=dut.t1j_registered_uv_shader.selected_v_q;
            assign t1j_selected_uv_valid_q=dut.t1j_registered_uv_shader.selected_uv_valid_q;
        end else begin: no_t1j_test_hierarchical_taps
            assign t1j_selected_u_q=56'sd0;
            assign t1j_selected_v_q=56'sd0;
            assign t1j_selected_uv_valid_q=1'b0;
        end
    endgenerate
    always #1 clk=~clk;
    always @(posedge clk) if(rst_n) cycles=cycles+1;
    function integer frame_phase;
        begin frame_phase=dut.u_timing.y*HTOTAL+dut.u_timing.x; end
    endfunction
    task send_byte(input [7:0] value);
        begin @(negedge clk);rx_byte=value;rx_valid=1;
            @(negedge clk);rx_byte=0;rx_valid=0; end
    endtask
    task scan_frame(input integer sid);
        integer phase,index,color_class,sample_x;
        reg [1:0] observed_class;
        reg [1:0] expected_lane;
        reg [55:0] expected_u,expected_v;
        reg expected_valid,expected_lane_valid;
        reg expected_hsync,expected_vsync,expected_active;
        reg expected_display_hsync,expected_display_vsync,expected_display_active;
        reg [3:0] expected_rgb_r,expected_rgb_g,expected_rgb_b;
        begin
            for(y=0;y<V_ACTIVE;y=y+1)
              for(x=0;x<((PROC || GRID || VIS_DIAG || T1L_MAT!=0 || T1M_ALU || T1N || T1O || T1P) ? H_ACTIVE+1+T1L_PIPE : H_ACTIVE);x=x+1) begin
                while(frame_phase()!=y*HTOTAL+x) @(negedge clk);
                sample_x=(PROC || GRID || VIS_DIAG || T1L_MAT!=0 || T1M_ALU || T1N || T1O || T1P) ? x-1-T1L_PIPE : x;
                expected_u=dut.fragment_u;expected_v=dut.fragment_v;
                expected_valid=dut.fragment_u_valid&&dut.fragment_v_valid;
                expected_lane_valid=dut.raster_primitive_valid;
                expected_lane=dut.raster_primitive_id;
                expected_hsync=dut.hsync_d;expected_vsync=dut.vsync_d;
                expected_active=dut.active_d;
                if(T1L_PIPE) begin
                    expected_u=dut.partition_selected_u;
                    expected_v=dut.partition_selected_v;
                    expected_valid=dut.partition_winner_valid;
                    expected_lane_valid=dut.partition_winner_valid;
                    expected_lane=dut.partition_winner_id;
                    expected_hsync=dut.partition_hsync_q;
                    expected_vsync=dut.partition_vsync_q;
                    expected_active=dut.partition_active_q;
                end
                expected_display_hsync=dut.display_hsync;
                expected_display_vsync=dut.display_vsync;
                expected_display_active=dut.display_active;
                expected_rgb_r=dut.display_r;expected_rgb_g=dut.display_g;
                expected_rgb_b=dut.display_b;
                @(posedge clk); #0.1;
                if(!(PROC || GRID || VIS_DIAG || T1L_MAT!=0 || T1M_ALU || T1N || T1O || T1P) || x>T1L_PIPE) pixels=pixels+1;
                if(OUT_REG && (dut.video_r!==expected_rgb_r || dut.video_g!==expected_rgb_g ||
                    dut.video_b!==expected_rgb_b || dut.video_hsync!==expected_display_hsync ||
                    dut.video_vsync!==expected_display_vsync || dut.video_active!==expected_display_active)) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: post-winner registered RGB/sync/active alignment mismatch xy=(%0d,%0d)",x,y);
                end else if(!OUT_REG && (dut.video_r!==dut.display_r || dut.video_g!==dut.display_g ||
                    dut.video_b!==dut.display_b || dut.video_hsync!==dut.display_hsync ||
                    dut.video_vsync!==dut.display_vsync || dut.video_active!==dut.display_active)) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: disabled post-winner register changed output tuple");
                end
                if(REG_UV && (dut.t1i_uv_u_q!==expected_u || dut.t1i_uv_v_q!==expected_v ||
                    dut.t1i_uv_valid_q!==expected_valid ||
                    dut.display_r!=={4{expected_valid&&expected_u[14]}} ||
                    dut.display_g!=={4{expected_valid&&expected_v[14]}} ||
                    dut.display_b!==4'b0000 || dut.display_hsync!==expected_hsync ||
                    dut.display_vsync!==expected_vsync || dut.display_active!==expected_active)) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: registered U/V or VGA control alignment mismatch xy=(%0d,%0d) uv=%h/%h exp=%h/%h valid=%b/%b rgb=%h%h%h exp=%b%b sync=%b%b active=%b",
                        x,y,dut.t1i_uv_u_q,dut.t1i_uv_v_q,expected_u,expected_v,
                        dut.t1i_uv_valid_q,expected_valid,dut.display_r,dut.display_g,dut.display_b,
                        expected_valid&&expected_u[14],expected_valid&&expected_v[14],
                        dut.display_hsync,dut.display_vsync,dut.display_active);
                end
                if(dut.active_scene !== (sid==0||sid==3 ? SCENE_A : sid==1 ? SCENE_B : SCENE_C)) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: active scene changed within first post-activation frame");
                end
                if(!(PROC || GRID || VIS_DIAG || T1L_MAT!=0 || T1M_ALU || T1N || T1O || T1P) && x<CHECK_W && y<CHECK_H)
                    $display("PIX %0d %0d %0d %0d %0d %0d %0d",sid,x,y,
                        dut.fragment_u_valid,dut.raster_primitive_id,dut.fragment_u,
                        dut.fragment_v);
                if(dut.fragment_u_valid!==dut.fragment_v_valid) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: U/V validity differs");
                end
                if(PROC) begin
                    observed_class={1'b0,expected_lane_valid && expected_valid &&
                        (expected_u[12] ^ expected_v[12])};
                    if(t1j_selected_u_q!==expected_u ||
                       t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==
                           (expected_lane_valid && expected_valid) ||
                       dut.display_r!=={4{observed_class[0]}} ||
                       dut.display_g!=={4{observed_class[0]}} ||
                       dut.display_b!=={4{observed_class[0]}} ||
                       dut.display_hsync!==expected_hsync ||
                       dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1j UV register/checker/control alignment mismatch xy=(%0d,%0d) rgb=%h%h%h valid=%b u=%h v=%h",
                            x,y,dut.display_r,dut.display_g,dut.display_b,expected_valid,expected_u,expected_v);
                    end
                    if(x>0) $display("T1JPIX %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid,expected_lane,dut.display_r,dut.display_g,dut.display_b);
                    if(x>0) begin
                        if(expected_valid)
                            class_counts[observed_class[0]]=class_counts[observed_class[0]]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(GRID) begin
                    observed_class={1'b0,expected_lane_valid && expected_valid &&
                        ((expected_u[11:0] < 12'd1024) || (expected_v[11:0] < 12'd1024))};
                    if(t1j_selected_u_q!==expected_u ||
                       t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==
                           (expected_lane_valid && expected_valid) ||
                       dut.display_r!=={4{observed_class[0]}} ||
                       dut.display_g!=={4{observed_class[0]}} ||
                       dut.display_b!=={4{observed_class[0]}} ||
                       dut.display_hsync!==expected_hsync ||
                       dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1k UV register/grid/control alignment mismatch xy=(%0d,%0d) rgb=%h%h%h valid=%b u=%h v=%h",
                            sample_x,y,dut.display_r,dut.display_g,dut.display_b,expected_valid,expected_u,expected_v);
                    end
                    if(x>0) $display("T1KPIX %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid,expected_lane,dut.display_r,dut.display_g,dut.display_b);
                    if(x>0) begin
                        if(expected_valid)
                            class_counts[observed_class[0]]=class_counts[observed_class[0]]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(T1L_MAT!=0) begin
                    case(T1L_MAT)
                        1: observed_class={1'b0,expected_lane_valid && expected_valid &&
                            (expected_u[12] ^ expected_v[12])};
                        2: observed_class={1'b0,expected_lane_valid && expected_valid &&
                            ((expected_u[11:10] == 2'b00) ||
                             (expected_v[11:10] == 2'b00))};
                        3: observed_class={1'b0,expected_lane_valid && expected_valid && expected_u[12]};
                        4: observed_class={1'b0,expected_lane_valid && expected_valid && expected_v[12]};
                        default: observed_class=2'b00;
                    endcase
                    if(t1j_selected_u_q!==expected_u ||
                       t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==
                           (expected_lane_valid && expected_valid) ||
                       dut.display_r!=={4{observed_class[0]}} ||
                       dut.display_g!=={4{observed_class[0]}} ||
                       dut.display_b!=={4{observed_class[0]}} ||
                       dut.display_hsync!==expected_hsync ||
                       dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1l material/control alignment mismatch op=%0d xy=(%0d,%0d)",T1L_MAT,sample_x,y);
                    end
                    if(x>T1L_PIPE) $display("T1LPIX %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid,expected_lane,dut.display_r);
                    if(x>T1L_PIPE) begin
                        if(expected_lane_valid && expected_valid)
                            class_counts[observed_class[0]]=class_counts[observed_class[0]]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(T1P) begin
                    reg [7:0] expected_op,expected_selector;
                    reg material_result,pred_u,pred_v;
                    expected_op=expected_t1o_ops[expected_lane*8+:8];
                    expected_selector=expected_t1p_selectors[expected_lane*8+:8];
                    pred_u=expected_u[expected_selector[3:0]];
                    pred_v=expected_v[expected_selector[7:4]];
                    material_result=0;
                    case(expected_op)
                        8'h00: material_result=pred_u;
                        8'h01: material_result=pred_v;
                        8'h02: material_result=pred_u^pred_v;
                        8'h03: material_result=pred_u&pred_v;
                        8'h04: material_result=pred_u|pred_v;
                        8'h05: material_result=~pred_u;
                    endcase
                    observed_class=expected_lane_valid && expected_valid ?
                        (material_result ? 2'b10 : 2'b01) : 2'b00;
                    if(t1j_selected_u_q!==expected_u || t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==(expected_lane_valid && expected_valid) ||
                       dut.active_material_ops!==expected_t1o_ops ||
                       dut.active_predicate_selectors!==expected_t1p_selectors ||
                       dut.active_scene_generation!==expected_t1n_generation ||
                       dut.t1o_selected_material_op_q!==expected_op ||
                       dut.t1p_selected_selector_q!==expected_selector ||
                       dut.t1n_selected_generation_q!==expected_t1n_generation ||
                       dut.display_r!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_g!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_b!==(expected_lane_valid && expected_valid && !material_result ? 4'hF : 4'h0) ||
                       dut.display_hsync!==expected_hsync || dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1p opcode/selector/U/V/generation/control alignment sid=%0d xy=(%0d,%0d) lane=%0d op=%h/%h sel=%h/%h",sid,sample_x,y,expected_lane,dut.t1o_selected_material_op_q,expected_op,dut.t1p_selected_selector_q,expected_selector);
                    end
                    if(x>T1L_PIPE) $display("T1PPIX %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid && expected_valid,expected_lane,
                        dut.display_r,dut.display_g,dut.display_b,
                        dut.t1o_selected_material_op_q,dut.t1p_selected_selector_q,
                        dut.t1n_selected_generation_q,dut.display_hsync,dut.display_vsync,dut.display_active);
                    if(x>T1L_PIPE) begin
                        if(expected_lane_valid && expected_valid)
                            class_counts[material_result]=class_counts[material_result]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(T1O) begin
                    reg [7:0] expected_t1o_op;
                    reg material_result;
                    case(expected_lane)
                        2'd0: expected_t1o_op=expected_t1o_ops[7:0];
                        2'd1: expected_t1o_op=expected_t1o_ops[15:8];
                        2'd2: expected_t1o_op=expected_t1o_ops[23:16];
                        default: expected_t1o_op=expected_t1o_ops[31:24];
                    endcase
                    material_result=0;
                    case(expected_t1o_op)
                        8'h00: material_result=expected_u[12];
                        8'h01: material_result=expected_v[12];
                        8'h02: material_result=expected_u[12]^expected_v[12];
                        8'h03: material_result=expected_u[12]&expected_v[12];
                        8'h04: material_result=expected_u[12]|expected_v[12];
                        8'h05: material_result=~expected_u[12];
                        default: material_result=1'b0;
                    endcase
                    observed_class=expected_lane_valid && expected_valid ?
                        (material_result ? 2'b10 : 2'b01) : 2'b00;
                    if(t1j_selected_u_q!==expected_u || t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==(expected_lane_valid && expected_valid) ||
                       dut.active_material_ops!==expected_t1o_ops ||
                       dut.active_scene_generation!==expected_t1n_generation ||
                       dut.t1o_selected_material_op_q!==expected_t1o_op ||
                       dut.t1n_selected_generation_q!==expected_t1n_generation ||
                       dut.display_r!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_g!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_b!==(expected_lane_valid && expected_valid && !material_result ? 4'hF : 4'h0) ||
                       dut.display_hsync!==expected_hsync || dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1o opcode/U/V/generation/control alignment mismatch sid=%0d xy=(%0d,%0d) lane=%0d op=%h/%h gen=%b/%b",sid,sample_x,y,expected_lane,dut.t1o_selected_material_op_q,expected_t1o_op,dut.t1n_selected_generation_q,expected_t1n_generation);
                    end
                    if(x>T1L_PIPE) $display("T1OPIX %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid && expected_valid,expected_lane,
                        dut.display_r,dut.display_g,dut.display_b,dut.t1o_selected_material_op_q,
                        dut.t1n_selected_generation_q,dut.display_hsync,dut.display_vsync,
                        dut.display_active);
                    if(x>T1L_PIPE) begin
                        if(expected_lane_valid && expected_valid)
                            class_counts[material_result]=class_counts[material_result]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(T1N) begin
                    reg material_result;
                    material_result=0;
                    case(expected_t1n_op)
                        8'h00: material_result=expected_u[12];
                        8'h01: material_result=expected_v[12];
                        8'h02: material_result=expected_u[12]^expected_v[12];
                        8'h03: material_result=expected_u[12]&expected_v[12];
                        8'h04: material_result=expected_u[12]|expected_v[12];
                        8'h05: material_result=~expected_u[12];
                        default: material_result=1'b0;
                    endcase
                    observed_class=expected_lane_valid && expected_valid ?
                        (material_result ? 2'b10 : 2'b01) : 2'b00;
                    if(t1j_selected_u_q!==expected_u || t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==(expected_lane_valid && expected_valid) ||
                       dut.active_material_op!==expected_t1n_op ||
                       dut.active_scene_generation!==expected_t1n_generation ||
                       dut.t1n_selected_material_op_q!==expected_t1n_op ||
                       dut.t1n_selected_generation_q!==expected_t1n_generation ||
                       dut.display_r!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_g!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_b!==(expected_lane_valid && expected_valid && !material_result ? 4'hF : 4'h0) ||
                       dut.display_hsync!==expected_hsync || dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1n opcode/U/V/generation/control alignment mismatch sid=%0d xy=(%0d,%0d) op=%h gen=%b/%b",sid,sample_x,y,dut.t1n_selected_material_op_q,dut.t1n_selected_generation_q,expected_t1n_generation);
                    end
                    if(x>T1L_PIPE) $display("T1NPIX %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid && expected_valid,expected_lane,
                        dut.display_r,dut.display_g,dut.display_b,dut.t1n_selected_material_op_q,
                        dut.t1n_selected_generation_q);
                    if(x>T1L_PIPE) begin
                        if(expected_lane_valid && expected_valid)
                            class_counts[material_result]=class_counts[material_result]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(T1M_ALU) begin
                    reg material_result;
                    material_result=0;
                    case(T1M_OP)
                        0: material_result=expected_u[12];
                        1: material_result=expected_v[12];
                        2: material_result=expected_u[12]^expected_v[12];
                        3: material_result=expected_u[12]&expected_v[12];
                        4: material_result=expected_u[12]|expected_v[12];
                        5: material_result=~expected_u[12];
                    endcase
                    observed_class=expected_lane_valid && expected_valid ?
                        (material_result ? 2'b10 : 2'b01) : 2'b00;
                    if(t1j_selected_u_q!==expected_u || t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==(expected_lane_valid && expected_valid) ||
                       dut.display_r!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_g!==(expected_lane_valid && expected_valid && material_result ? 4'hF : 4'h0) ||
                       dut.display_b!==(expected_lane_valid && expected_valid && !material_result ? 4'hF : 4'h0) ||
                       dut.display_hsync!==expected_hsync || dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1m ALU/control alignment mismatch op=%0d xy=(%0d,%0d) rgb=%h%h%h",T1M_OP,sample_x,y,dut.display_r,dut.display_g,dut.display_b);
                    end
                    if(x>T1L_PIPE) $display("T1MPIX %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid && expected_valid,expected_lane,
                        dut.display_r,dut.display_g,dut.display_b);
                    if(x>T1L_PIPE) begin
                        if(expected_lane_valid && expected_valid)
                            class_counts[material_result]=class_counts[material_result]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]=observed_class;
                        else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                        else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                        else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                    end
                end else if(VIS_DIAG) begin
                    observed_class={1'b0,expected_lane_valid && expected_valid &&
                        (expected_u[12] ^ expected_v[12])};
                    if(t1j_selected_u_q!==expected_u ||
                       t1j_selected_v_q!==expected_v ||
                       t1j_selected_uv_valid_q!==
                           (expected_lane_valid && expected_valid) ||
                       dut.display_r!=={4{observed_class[0]}} ||
                       dut.display_g!=={4{observed_class[0]}} ||
                       dut.display_b!=={4{expected_lane_valid && expected_valid}} ||
                       dut.display_hsync!==expected_hsync ||
                       dut.display_vsync!==expected_vsync ||
                       dut.display_active!==expected_active) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: T1j checker visibility mapping/alignment mismatch xy=(%0d,%0d) rgb=%h%h%h valid=%b u=%h v=%h",
                            sample_x,y,dut.display_r,dut.display_g,dut.display_b,expected_valid,expected_u,expected_v);
                    end
                    if(x>0) $display("T1JVPIX %0d %0d %0d %0d %0d %0d %0d %0d",sid,sample_x,y,
                        expected_lane_valid,expected_lane,dut.display_r,dut.display_g,dut.display_b);
                    if(x>0) begin
                        if(expected_valid)
                            class_counts[observed_class[0]+(expected_lane_valid ? 1 : 0)]=
                                class_counts[observed_class[0]+(expected_lane_valid ? 1 : 0)]+1;
                        else class_counts[0]=class_counts[0]+1;
                        index=y*H_ACTIVE+sample_x;
                        if(sid==0) pattern_a[index]={observed_class[0],expected_lane_valid && expected_valid};
                        else if(sid==1 && pattern_a[index]!=={observed_class[0],expected_lane_valid && expected_valid}) changed_b=changed_b+1;
                        else if(sid==2 && pattern_a[index]!=={observed_class[0],expected_lane_valid && expected_valid}) changed_c=changed_c+1;
                        else if(sid==3 && pattern_a[index]!=={observed_class[0],expected_lane_valid && expected_valid}) return_mismatches=return_mismatches+1;
                    end
                end else if(DIAG) begin
                    observed_class={dut.display_g[3],dut.display_r[3]};
                    if(!REG_UV && (dut.display_b!==4'b0000 ||
                       dut.display_r!=={4{dut.fragment_u_valid && dut.fragment_v_valid && dut.fragment_u[14]}} ||
                       dut.display_g!=={4{dut.fragment_u_valid && dut.fragment_v_valid && dut.fragment_v[14]}})) begin
                        failures=failures+1;
                        if(failures<8)$display("FAIL: diagnostic RGB mapping or invalid gating mismatch xy=(%0d,%0d) rgb=%h%h%h frag=%b/%b u=%h v=%h",
                            x,y,dut.display_r,dut.display_g,dut.display_b,dut.fragment_u_valid,
                            dut.fragment_v_valid,dut.fragment_u,dut.fragment_v);
                    end
                    if(dut.raster_primitive_valid && dut.fragment_u_valid && dut.fragment_v_valid) begin
                        color_class=observed_class[0]+(2*observed_class[1]);
                        class_counts[color_class]=class_counts[color_class]+1;
                    end
                    index=y*H_ACTIVE+x;
                    if(sid==0) pattern_a[index]=observed_class;
                    else if(sid==1 && observed_class!==pattern_a[index]) changed_b=changed_b+1;
                    else if(sid==2 && observed_class!==pattern_a[index]) changed_c=changed_c+1;
                    else if(sid==3 && observed_class!==pattern_a[index]) return_mismatches=return_mismatches+1;
                end else if(dut.display_r!==dut.rast_r || dut.display_g!==dut.rast_g ||
                            dut.display_b!==dut.rast_b) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: diagnostic-off RGB differs from normal raster RGB");
                end
            end
        end
    endtask
    task send_scene(input [SCENE_WIDTH-1:0] scene,input integer sid);
        reg [SCENE_WIDTH-1:0] old_scene;
        reg [1343:0] old_uv_coefficients;
        reg [55:0] old_uv_frac;
        reg [7:0] old_material_op;
        reg [31:0] old_material_ops;
        reg [31:0] old_predicate_selectors;
        reg [7:0] old_selected_material_op;
        reg old_scene_generation;
        reg old_selected_generation;
        begin
            old_scene=dut.active_scene;old_uv_coefficients=active_uv_coefficients;
            old_uv_frac=active_uv_frac;
            old_material_op=dut.active_material_op;
            old_material_ops=dut.active_material_ops;
            old_predicate_selectors=dut.active_predicate_selectors;
            old_selected_material_op=dut.t1n_selected_material_op_q;
            old_scene_generation=dut.active_scene_generation;
            old_selected_generation=dut.t1n_selected_generation_q;
            if(T1P) begin
                expected_t1o_ops=scene[1392+:32];
                expected_t1p_selectors=scene[1424+:32];
                expected_t1n_generation=~expected_t1n_generation;
            end else if(T1O) begin
                expected_t1o_ops=scene[1392+:32];
                expected_t1n_generation=~expected_t1n_generation;
            end else if(T1N) begin
                expected_t1n_op=scene[1392+:8];
                expected_t1n_generation=~expected_t1n_generation;
            end
            send_byte(8'hA5);
            for(j=0;j<174+T1N+4*T1O+8*T1P;j=j+1) begin
                send_byte(scene[j*8+:8]);
                if(dut.active_scene!==old_scene||active_uv_coefficients!==old_uv_coefficients||
                    active_uv_frac!==old_uv_frac || dut.active_material_op!==old_material_op ||
                    dut.active_material_ops!==old_material_ops ||
                    dut.active_predicate_selectors!==old_predicate_selectors ||
                    dut.active_scene_generation!==old_scene_generation ||
                    (!T1O && dut.t1n_selected_material_op_q!==old_selected_material_op) ||
                    dut.t1n_selected_generation_q!==old_selected_generation ||
                    (T1N && j<174 && dut.scene_commit_pending) ||
                    (T1O && j<177 && dut.scene_commit_pending) ||
                    (T1P && j<181 && dut.scene_commit_pending)) begin
                    failures=failures+1;
                    if(failures<8)$display("FAIL: candidate UV state leaked during receipt");
                end
            end
            while(!dut.activate_scene) @(negedge clk);
            if(!dut.prepared_generation_matches||
                dut.prepared_ready3!==1'b1||dut.prepared_ready2!==1'b1||
                dut.prepared_ready1!==1'b1||dut.prepared_ready0!==1'b1) begin
                failures=failures+1;$display("FAIL: U/V readiness did not join scene preparation joined=%b/%b ready=%b gen=%b act=%b",
                    dut.u_t1i_u.joined_ready,dut.u_t1i_v.joined_ready,
                    {dut.prepared_ready3,dut.prepared_ready2,dut.prepared_ready1,dut.prepared_ready0},
                    dut.prepared_generation_matches,dut.activate_scene);
            end
            @(posedge clk);#0.1;
            if(dut.active_scene!==scene||dut.scene_commit_pending||
                (T1N && (dut.active_material_op!==expected_t1n_op ||
                         dut.active_scene_generation!==expected_t1n_generation)) ||
                (T1P && (dut.active_material_ops!==expected_t1o_ops ||
                         dut.active_predicate_selectors!==expected_t1p_selectors ||
                         dut.active_scene_generation!==expected_t1n_generation)) ||
                (T1O && (dut.active_material_ops!==expected_t1o_ops ||
                         dut.active_scene_generation!==expected_t1n_generation)) ||
                {dut.active_A_z3,dut.active_A_z2,dut.active_A_z1,dut.active_A_z0} !==
                    {dut.A_z3,dut.A_z2,dut.A_z1,dut.A_z0}||
                {dut.active_B_z3,dut.active_B_z2,dut.active_B_z1,dut.active_B_z0} !==
                    {dut.B_z3,dut.B_z2,dut.B_z1,dut.B_z0}||
                {dut.active_C_z3,dut.active_C_z2,dut.active_C_z1,dut.active_C_z0} !==
                    {dut.C_z3,dut.C_z2,dut.C_z1,dut.C_z0}||
                {dut.active_frac_bits3,dut.active_frac_bits2,dut.active_frac_bits1,dut.active_frac_bits0} !==
                    {dut.frac_bits3,dut.frac_bits2,dut.frac_bits1,dut.frac_bits0}||
                active_u_a!=={dut.u_t1i_u.candidate_A_attr3,dut.u_t1i_u.candidate_A_attr2,
                    dut.u_t1i_u.candidate_A_attr1,dut.u_t1i_u.candidate_A_attr0}||
                active_v_a!=={dut.u_t1i_v.candidate_A_attr3,dut.u_t1i_v.candidate_A_attr2,
                    dut.u_t1i_v.candidate_A_attr1,dut.u_t1i_v.candidate_A_attr0}||
                active_u_frac!=={dut.u_t1i_u.candidate_frac_attr3,dut.u_t1i_u.candidate_frac_attr2,
                    dut.u_t1i_u.candidate_frac_attr1,dut.u_t1i_u.candidate_frac_attr0}||
                active_v_frac!=={dut.u_t1i_v.candidate_frac_attr3,dut.u_t1i_v.candidate_frac_attr2,
                    dut.u_t1i_v.candidate_frac_attr1,dut.u_t1i_v.candidate_frac_attr0}) begin
                failures=failures+1;$display("FAIL: geometry/depth/U/V generation did not activate atomically sid=%0d",sid);
            end
            if (active_uv_coefficients!==candidate_uv_coefficients ||
                active_uv_frac!==candidate_uv_frac ||
                {dut.u_t1i_u.u_scalar0.a_r,dut.u_t1i_u.u_scalar0.b_r,dut.u_t1i_u.u_scalar0.acc} !==
                    {dut.u_t1i_u.candidate_A_attr0,dut.u_t1i_u.candidate_B_attr0,dut.u_t1i_u.candidate_C_attr0} ||
                {dut.u_t1i_u.u_scalar1.a_r,dut.u_t1i_u.u_scalar1.b_r,dut.u_t1i_u.u_scalar1.acc} !==
                    {dut.u_t1i_u.candidate_A_attr1,dut.u_t1i_u.candidate_B_attr1,dut.u_t1i_u.candidate_C_attr1} ||
                {dut.u_t1i_u.u_scalar2.a_r,dut.u_t1i_u.u_scalar2.b_r,dut.u_t1i_u.u_scalar2.acc} !==
                    {dut.u_t1i_u.candidate_A_attr2,dut.u_t1i_u.candidate_B_attr2,dut.u_t1i_u.candidate_C_attr2} ||
                {dut.u_t1i_u.u_scalar3.a_r,dut.u_t1i_u.u_scalar3.b_r,dut.u_t1i_u.u_scalar3.acc} !==
                    {dut.u_t1i_u.candidate_A_attr3,dut.u_t1i_u.candidate_B_attr3,dut.u_t1i_u.candidate_C_attr3} ||
                {dut.u_t1i_v.u_scalar0.a_r,dut.u_t1i_v.u_scalar0.b_r,dut.u_t1i_v.u_scalar0.acc} !==
                    {dut.u_t1i_v.candidate_A_attr0,dut.u_t1i_v.candidate_B_attr0,dut.u_t1i_v.candidate_C_attr0} ||
                {dut.u_t1i_v.u_scalar1.a_r,dut.u_t1i_v.u_scalar1.b_r,dut.u_t1i_v.u_scalar1.acc} !==
                    {dut.u_t1i_v.candidate_A_attr1,dut.u_t1i_v.candidate_B_attr1,dut.u_t1i_v.candidate_C_attr1} ||
                {dut.u_t1i_v.u_scalar2.a_r,dut.u_t1i_v.u_scalar2.b_r,dut.u_t1i_v.u_scalar2.acc} !==
                    {dut.u_t1i_v.candidate_A_attr2,dut.u_t1i_v.candidate_B_attr2,dut.u_t1i_v.candidate_C_attr2} ||
                {dut.u_t1i_v.u_scalar3.a_r,dut.u_t1i_v.u_scalar3.b_r,dut.u_t1i_v.u_scalar3.acc} !==
                    {dut.u_t1i_v.candidate_A_attr3,dut.u_t1i_v.candidate_B_attr3,dut.u_t1i_v.candidate_C_attr3}) begin
                failures=failures+1;$display("FAIL: complete U/V coefficients or accumulator re-anchor mismatch sid=%0d",sid);
            end
            if(sid==0) begin
                first_a_uv_coefficients=active_uv_coefficients;
                first_a_uv_frac=active_uv_frac;
                first_a_uv_reanchor=uv_reanchor;
                first_a_seen=1;
            end else if(sid==3 && (!first_a_seen || active_uv_coefficients!==first_a_uv_coefficients ||
                    active_uv_frac!==first_a_uv_frac || uv_reanchor!==first_a_uv_reanchor)) begin
                failures=failures+1;$display("FAIL: return-A committed U/V tuple/re-anchor differs from initial A");
            end
            scan_frame(sid);
        end
    endtask
    task send_invalid_material_packet;
        reg [SCENE_WIDTH-1:0] old_scene;
        reg [7:0] old_material_op;
        reg old_active_bank,old_scene_generation,old_candidate_generation;
        begin
            if(T1N) begin
                old_scene=dut.active_scene;
                old_material_op=dut.active_material_op;
                old_active_bank=dut.u_scene_loader.active_bank;
                old_scene_generation=dut.active_scene_generation;
                old_candidate_generation=dut.prepared_depth_control.u_prepared_control4.candidate_generation;
                send_byte(8'hA5);
                for(j=0;j<175;j=j+1) send_byte(SCENE_BAD[j*8+:8]);
                if(dut.scene_commit_pending || dut.u_scene_loader.receiving ||
                   dut.u_scene_loader.payload_count!==8'd0 ||
                   dut.u_scene_loader.active_bank!==old_active_bank ||
                   dut.active_scene!==old_scene || dut.active_material_op!==old_material_op ||
                   dut.active_scene_generation!==old_scene_generation ||
                   dut.prepared_depth_control.u_prepared_control4.candidate_generation!==old_candidate_generation) begin
                    failures=failures+1;
                    $display("FAIL: invalid opcode advanced bank/commit/generation or changed active tuple");
                end else begin
                    $display("PASS: T1n invalid opcode rejected without bank/generation advance; receiver recovered");
                end
            end
        end
    endtask
    task send_invalid_t1o_packet(input integer bad_lane);
        reg [SCENE_WIDTH-1:0] old_scene;
        reg [31:0] old_material_ops;
        reg old_active_bank,old_scene_generation,old_candidate_generation;
        begin
            if(T1O) begin
                old_scene=dut.active_scene;
                old_material_ops=dut.active_material_ops;
                old_active_bank=dut.u_scene_loader.active_bank;
                old_scene_generation=dut.active_scene_generation;
                old_candidate_generation=dut.prepared_depth_control.u_prepared_control4.candidate_generation;
                send_byte(8'hA5);
                for(j=0;j<178;j=j+1) begin
                    if(j==174+bad_lane) send_byte(8'h06);
                    else send_byte(SCENE_B[j*8+:8]);
                end
                if(dut.scene_commit_pending || dut.u_scene_loader.receiving ||
                   dut.u_scene_loader.payload_count!==8'd0 ||
                   dut.u_scene_loader.active_bank!==old_active_bank ||
                   dut.active_scene!==old_scene || dut.active_material_ops!==old_material_ops ||
                   dut.active_scene_generation!==old_scene_generation ||
                   dut.prepared_depth_control.u_prepared_control4.candidate_generation!==old_candidate_generation) begin
                    failures=failures+1;
                    $display("FAIL: T1o invalid opcode lane %0d advanced bank/commit/generation or changed active tuple",bad_lane);
                end else begin
                    $display("PASS: T1o invalid opcode lane %0d rejected without bank/generation advance",bad_lane);
                end
            end
        end
    endtask
    task send_invalid_t1p_packet(input integer bad_lane);
        reg [SCENE_WIDTH-1:0] old_scene;
        reg [31:0] old_ops,old_selectors;
        reg old_bank,old_generation,old_candidate_generation;
        begin
            if(T1P) begin
                old_scene=dut.active_scene;
                old_ops=dut.active_material_ops;
                old_selectors=dut.active_predicate_selectors;
                old_bank=dut.u_scene_loader.active_bank;
                old_generation=dut.active_scene_generation;
                old_candidate_generation=dut.prepared_depth_control.u_prepared_control4.candidate_generation;
                send_byte(8'hA5);
                for(j=0;j<182;j=j+1) begin
                    if(j==174+bad_lane) send_byte(8'h06);
                    else if(j>=178) send_byte(8'hff);
                    else send_byte(SCENE_B[j*8+:8]);
                    if(j<181 && dut.scene_commit_pending) begin
                        failures=failures+1;
                        $display("FAIL: T1p candidate completed before selector byte 181");
                    end
                end
                if(dut.scene_commit_pending || dut.u_scene_loader.receiving ||
                   dut.u_scene_loader.payload_count!==8'd0 ||
                   dut.u_scene_loader.active_bank!==old_bank ||
                   dut.active_scene!==old_scene || dut.active_material_ops!==old_ops ||
                   dut.active_predicate_selectors!==old_selectors ||
                   dut.active_scene_generation!==old_generation ||
                   dut.prepared_depth_control.u_prepared_control4.candidate_generation!==old_candidate_generation) begin
                    failures=failures+1;
                    $display("FAIL: T1p invalid opcode lane %0d advanced active state",bad_lane);
                end else begin
                    $display("PASS: T1p invalid opcode lane %0d rejected after legal selector tail",bad_lane);
                end
            end
        end
    endtask
    initial begin
        for(k=0;k<4;k=k+1) class_counts[k]=0;
        rst_n=1; #0.1; rst_n=0;
        #0.1;
        if(OUT_REG && (dut.video_r!==4'd0 || dut.video_g!==4'd0 || dut.video_b!==4'd0 ||
            dut.video_hsync!==1'b0 || dut.video_vsync!==1'b0 || dut.video_active!==1'b0)) begin
            failures=failures+1;$display("FAIL: post-winner output register reset values are not zero");
        end
        if((PROC || GRID || VIS_DIAG || T1L_MAT!=0 || T1M_ALU || T1N || T1O || T1P) && (t1j_selected_u_q!==56'sd0 ||
            t1j_selected_v_q!==56'sd0 ||
            t1j_selected_uv_valid_q!==1'b0 ||
            dut.display_r!==4'd0 || dut.display_g!==4'd0 || dut.display_b!==4'd0 ||
            dut.display_hsync!==1'b0 || dut.display_vsync!==1'b0 ||
            dut.display_active!==1'b0)) begin
            failures=failures+1;$display("FAIL: T1j U/V/control stage reset tuple is not zero");
        end
        repeat(4)@(negedge clk);rst_n=1;repeat(3)@(negedge clk);
        if(T1P) begin
            send_invalid_t1p_packet(0);send_scene(SCENE_A,0);
            send_invalid_t1p_packet(1);send_scene(SCENE_B,1);
            send_invalid_t1p_packet(2);send_scene(SCENE_C,2);
            send_invalid_t1p_packet(3);send_scene(SCENE_A,3);
        end else if(T1O) begin
            send_invalid_t1o_packet(0);send_scene(SCENE_A,0);
            send_invalid_t1o_packet(1);send_scene(SCENE_B,1);
            send_invalid_t1o_packet(2);send_scene(SCENE_C,2);
            send_invalid_t1o_packet(3);send_scene(SCENE_A,3);
        end else begin
            send_scene(SCENE_A,0);send_scene(SCENE_B,1);
            send_scene(SCENE_C,2);
            if(T1N) send_invalid_material_packet;
            send_scene(SCENE_A,3);
        end
        if(T1P) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 ||
               changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1p predicate classes blue=%0d yellow=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1p per-primitive predicates A/B/C/A blue=%0d yellow=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(T1O) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 ||
               changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1o per-primitive runtime classes blue=%0d yellow=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1o per-primitive runtime A/B/C/A blue=%0d yellow=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(T1N) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 ||
               changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1n runtime opcode classes blue=%0d yellow=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1n runtime opcode A/B/C/A blue=%0d yellow=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(T1M_ALU) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 ||
               changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1m ALU classes op=%0d blue=%0d yellow=%0d changedB=%0d changedC=%0d return=%0d",
                    T1M_OP,class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1m ALU op=%0d blue=%0d yellow=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    T1M_OP,class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(T1L_MAT!=0) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 ||
               changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1l material classes op=%0d black=%0d white=%0d changedB=%0d changedC=%0d return=%0d",
                    T1L_MAT,class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1l material op=%0d black=%0d white=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    T1L_MAT,class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(PROC) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 || changed_c==0 ||
               return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: procedural checker scene distinction failed black=%0d white=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1j checker classes black=%0d white=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(VIS_DIAG) begin
            if(class_counts[0]==0 || class_counts[1]==0 || class_counts[2]==0 ||
               changed_b==0 || changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1j visibility colors black=%0d blue=%0d white=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],class_counts[2],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1j visibility colors black=%0d blue=%0d white=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],class_counts[2],changed_b,changed_c,return_mismatches);
            end
        end else if(GRID) begin
            if(class_counts[0]==0 || class_counts[1]==0 || changed_b==0 || changed_c==0 ||
               return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: T1k grid classes black=%0d white=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: T1k grid classes black=%0d white=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],changed_b,changed_c,return_mismatches);
            end
        end else if(DIAG) begin
            if(class_counts[0]==0 || class_counts[1]==0 || class_counts[2]==0 || class_counts[3]==0 ||
               changed_b==0 || changed_c==0 || return_mismatches!=0) begin
                failures=failures+1;
                $display("FAIL: diagnostic class coverage/scene distinction failed black=%0d red=%0d green=%0d yellow=%0d changedB=%0d changedC=%0d return=%0d",
                    class_counts[0],class_counts[1],class_counts[2],class_counts[3],changed_b,changed_c,return_mismatches);
            end else begin
                $display("PASS: diagnostic classes black=%0d red=%0d green=%0d yellow=%0d changedB=%0d changedC=%0d A-return-mismatches=%0d",
                    class_counts[0],class_counts[1],class_counts[2],class_counts[3],changed_b,changed_c,return_mismatches);
            end
        end
        if(!failures&&pixels==4*H_ACTIVE*V_ACTIVE)
            $display("PASS: T1i A/B/C/A full-frame U/V activation pixels=%0d",pixels);
        else $display("FAIL: T1i failures=%0d pixels=%0d",failures,pixels);
        $finish;
    end
    initial begin #200000000;$display("FAIL: T1i simulation timeout");$finish;end
endmodule
"""


def signed(value: int, width: int) -> int:
    return value - (1 << width) if value & (1 << (width - 1)) else value


def load_scene(name: str) -> tuple[str, int]:
    wire = bytes.fromhex((ROOT / "fixtures" / name).read_text().strip())
    if len(wire) != 175 or wire[0] != 0xA5:
        raise AssertionError(f"{name}: expected a 175-byte A5 transaction")
    scene = int.from_bytes(wire[1:], "little")
    return f"{scene:0348x}", scene


def decode(scene: int):
    lanes = []
    for lane in range(4):
        record = (scene >> (lane * 348)) & ((1 << 348) - 1)
        base = record & ((1 << 252) - 1)
        edges = []
        for edge in range(3):
            offset = edge * 64
            edges.append((signed((base >> offset) & 0xFFFF, 16),
                          signed((base >> (offset + 16)) & 0xFFFF, 16),
                          signed((base >> (offset + 32)) & 0xFFFFFFFF, 32)))
        uv = [((record >> (252 + vertex * 32)) & 0xFFFF,
               (record >> (268 + vertex * 32)) & 0xFFFF) for vertex in range(3)]
        depth = [(base >> (204 + vertex * 16)) & 0xFFFF for vertex in range(3)]
        denominator = sum(edge[2] for edge in edges)
        sign = 1 if denominator > 0 else -1
        reciprocal, frac = full_reciprocal(abs(denominator))
        def plane(samples):
            terms = [sum(edges[i][axis] * samples[i] for i in range(3))
                     for axis in range(3)]
            return tuple(term * sign * reciprocal for term in terms) + (frac,)
        lanes.append((edges, uv, plane([p[0] for p in uv]),
                      plane([p[1] for p in uv]), plane(depth)))
    return lanes


def oracle(lanes, x: int, y: int):
    winner = None
    best = None
    for lane, (edges, _uv, _u, _v, depth_plane) in enumerate(lanes):
        if not all(a*x+b*y+c >= 0 for a,b,c in edges):
            continue
        a,b,c,frac=depth_plane
        depth=(a*x+b*y+c)>>frac
        if best is None or depth<best:
            winner,best=lane,depth
    if winner is None:
        return 0,0,0,0
    values=[]
    for plane in (lanes[winner][2],lanes[winner][3]):
        a,b,c,frac=plane
        values.append((a*x+b*y+c)>>frac)
    return 1,winner,*values


def main() -> int:
    fixtures=[load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    names={"SCENE_A":fixtures[0][0],"SCENE_B":fixtures[1][0],"SCENE_C":fixtures[2][0]}
    tb_text=TB
    for key,value in names.items(): tb_text=tb_text.replace(f"@@{key}@@",value)
    with tempfile.TemporaryDirectory(prefix="spu_t1i_uv_") as temp_dir:
        temp=Path(temp_dir);tb=temp/"t1i_uv_tb.v";out=temp/"t1i_uv_tb.vvp"
        tb.write_text(tb_text)
        compiled=subprocess.run(["iverilog","-g2012","-s","t1i_uv_tb","-o",str(out),
            str(tb),*[str(ROOT/p) for p in RTL_FILES]],cwd=ROOT,text=True,
            capture_output=True,check=False)
        if compiled.returncode:
            print(compiled.stderr);return 1
        invalid_tb=temp/"t1i_invalid_profile_tb.v";invalid_out=temp/"t1i_invalid_profile_tb.vvp"
        invalid_tb.write_text(r'''module t1i_invalid_profile_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(0),.T1I_UV_SCENE(1)) dut();
    endmodule
''')
        invalid=subprocess.run(["iverilog","-g2012","-s","t1i_invalid_profile_tb",
            "-o",str(invalid_out),str(invalid_tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if invalid.returncode==0 or "T1I_requires_prepared_four_primitive_scene" not in invalid.stderr:
            print("FAIL: illegal T1i profile did not fail elaboration");print(invalid.stderr);return 1
        mutual_tb=temp/"t1i_mutual_profile_tb.v";mutual_out=temp/"t1i_mutual_profile_tb.vvp"
        mutual_tb.write_text(r'''module t1i_mutual_profile_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1H_SCALAR_SCENE(1),.T1I_UV_SCENE(1)) dut();
    endmodule
''')
        mutual=subprocess.run(["iverilog","-g2012","-s","t1i_mutual_profile_tb",
            "-o",str(mutual_out),str(mutual_tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if mutual.returncode==0 or "T1I_and_T1H_are_mutually_exclusive" not in mutual.stderr:
            print("FAIL: simultaneous T1h/T1i selectors did not fail elaboration");print(mutual.stderr);return 1
        diag_tb=temp/"t1i_invalid_diag_tb.v";diag_out=temp/"t1i_invalid_diag_tb.vvp"
        diag_tb.write_text(r'''module t1i_invalid_diag_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1I_UV_SCENE(0),.T1I_UV_DIAG(1)) dut();
    endmodule
''')
        diag_invalid=subprocess.run(["iverilog","-g2012","-s","t1i_invalid_diag_tb",
            "-o",str(diag_out),str(diag_tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if diag_invalid.returncode==0 or "T1I_UV_diag_requires_uv_scene_without_t1h" not in diag_invalid.stderr:
            print("FAIL: T1i diagnostic without T1i scene did not fail elaboration");print(diag_invalid.stderr);return 1
        reg_invalid_tb=temp/"t1i_invalid_reg_diag_tb.v";reg_invalid_out=temp/"t1i_invalid_reg_diag_tb.vvp"
        reg_invalid_tb.write_text(r'''module t1i_invalid_reg_diag_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1I_UV_SCENE(1),.T1I_UV_REG_DIAG(1)) dut();
    endmodule
''')
        reg_invalid=subprocess.run(["iverilog","-g2012","-s","t1i_invalid_reg_diag_tb",
            "-o",str(reg_invalid_out),str(reg_invalid_tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if reg_invalid.returncode==0 or "T1I_UV_registered_diag_requires_uv_diag_only" not in reg_invalid.stderr:
            print("FAIL: registered U/V diagnostic without UV diagnostic did not fail elaboration");print(reg_invalid.stderr);return 1
        post_invalid_tb=temp/"t1i_invalid_post_winner_tb.v";post_invalid_out=temp/"t1i_invalid_post_winner_tb.vvp"
        post_invalid_tb.write_text(r'''module t1i_invalid_post_winner_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(0),
            .FOUR_PRIMITIVE_SCENE(0),.GPU_POST_WINNER_REG(1)) dut();
    endmodule
''')
        post_invalid=subprocess.run(["iverilog","-g2012","-s","t1i_invalid_post_winner_tb",
            "-o",str(post_invalid_out),str(post_invalid_tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if post_invalid.returncode==0 or "post_winner_register_requires_prepared_t1i_without_uv_register" not in post_invalid.stderr:
            print("FAIL: post-winner register accepted an illegal profile");print(post_invalid.stderr);return 1
        post_mutual_tb=temp/"t1i_mutual_post_winner_tb.v";post_mutual_out=temp/"t1i_mutual_post_winner_tb.vvp"
        post_mutual_tb.write_text(r'''module t1i_mutual_post_winner_tb;
        spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1I_UV_SCENE(1),.T1I_UV_REG_DIAG(1),
            .GPU_POST_WINNER_REG(1)) dut();
    endmodule
''')
        post_mutual=subprocess.run(["iverilog","-g2012","-s","t1i_mutual_post_winner_tb",
            "-o",str(post_mutual_out),str(post_mutual_tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if post_mutual.returncode==0 or "post_winner_register_requires_prepared_t1i_without_uv_register" not in post_mutual.stderr:
            print("FAIL: post-winner and registered U/V diagnostics were not rejected together");print(post_mutual.stderr);return 1
        result=subprocess.run(["vvp",str(out)],cwd=ROOT,text=True,capture_output=True,
            check=False,timeout=60)
        diag_compile=subprocess.run(["iverilog","-g2012","-s","t1i_uv_tb","-P","t1i_uv_tb.DIAG=1",
            "-o",str(temp/"t1i_uv_diag_tb.vvp"),str(tb),*[str(ROOT/p) for p in RTL_FILES]],
            cwd=ROOT,text=True,capture_output=True,check=False)
        if diag_compile.returncode:
            print(diag_compile.stderr);return 1
        diag_result=subprocess.run(["vvp",str(temp/"t1i_uv_diag_tb.vvp")],cwd=ROOT,
            text=True,capture_output=True,check=False,timeout=60)
        reg_compile=subprocess.run(["iverilog","-g2012","-s","t1i_uv_tb","-P","t1i_uv_tb.DIAG=1",
            "-P","t1i_uv_tb.REG_UV=1","-o",str(temp/"t1i_uv_reg_diag_tb.vvp"),str(tb),
            *[str(ROOT/p) for p in RTL_FILES]],cwd=ROOT,text=True,capture_output=True,check=False)
        if reg_compile.returncode:
            print(reg_compile.stderr);return 1
        reg_result=subprocess.run(["vvp",str(temp/"t1i_uv_reg_diag_tb.vvp")],cwd=ROOT,
            text=True,capture_output=True,check=False,timeout=60)
        post_normal_compile=subprocess.run(["iverilog","-g2012","-s","t1i_uv_tb",
            "-P","t1i_uv_tb.OUT_REG=1","-o",str(temp/"t1i_postreg_tb.vvp"),str(tb),
            *[str(ROOT/p) for p in RTL_FILES]],cwd=ROOT,text=True,capture_output=True,check=False)
        if post_normal_compile.returncode:
            print(post_normal_compile.stderr);return 1
        post_normal_result=subprocess.run(["vvp",str(temp/"t1i_postreg_tb.vvp")],cwd=ROOT,
            text=True,capture_output=True,check=False,timeout=60)
        post_diag_compile=subprocess.run(["iverilog","-g2012","-s","t1i_uv_tb",
            "-P","t1i_uv_tb.DIAG=1","-P","t1i_uv_tb.OUT_REG=1",
            "-o",str(temp/"t1i_postreg_diag_tb.vvp"),str(tb),
            *[str(ROOT/p) for p in RTL_FILES]],cwd=ROOT,text=True,capture_output=True,check=False)
        if post_diag_compile.returncode:
            print(post_diag_compile.stderr);return 1
        post_diag_result=subprocess.run(["vvp",str(temp/"t1i_postreg_diag_tb.vvp")],cwd=ROOT,
            text=True,capture_output=True,check=False,timeout=60)
    if any(run.returncode for run in (result,diag_result,reg_result,post_normal_result,post_diag_result)):
        for run in (result,diag_result,reg_result,post_normal_result,post_diag_result): print(run.stderr)
        return 1
    for label, simulation in (("normal", result), ("combinational diagnostic", diag_result),
                              ("registered diagnostic", reg_result),
                              ("post-winner register", post_normal_result),
                              ("post-winner diagnostic", post_diag_result)):
        failures_seen = [line for line in simulation.stdout.splitlines() if line.startswith("FAIL:")]
        if failures_seen:
            print(f"{label}: {len(failures_seen)} failure line(s)")
            print("\n".join(failures_seen[:8]))
    errors=0;counts=[0,0,0,0]
    decoded=[decode(item[1]) for item in fixtures]
    for line in result.stdout.splitlines():
        if not line.startswith("PIX "): continue
        _tag,sid_s,x_s,y_s,valid_s,lane_s,u_s,v_s=line.split()
        sid,x,y,valid,lane,u,v=map(int,(sid_s,x_s,y_s,valid_s,lane_s,u_s,v_s))
        expected=oracle(decoded[sid if sid<3 else 0],x,y)
        observed=(valid,lane,u,v)
        counts[sid]+=1
        if observed!=expected:
            errors+=1
            if errors<=12: print(f"MISMATCH scene={sid} xy=({x},{y}) expected={expected} got={observed}")
    if counts != [8000]*4:
        errors+=1;print(f"FAIL: frame counts expected={[8000]*4} got={counts}")
    if "PASS: T1i A/B/C/A full-frame U/V activation pixels=32000" not in result.stdout:
        errors+=1;print(result.stdout[-2500:])
    if "PASS: diagnostic classes " not in diag_result.stdout or \
       "PASS: T1i A/B/C/A full-frame U/V activation pixels=32000" not in diag_result.stdout:
        errors+=1;print(diag_result.stdout[-2500:])
    if "PASS: T1i A/B/C/A full-frame U/V activation pixels=32000" not in reg_result.stdout:
        errors+=1;print(reg_result.stdout[-2500:])
    for simulation in (post_normal_result,post_diag_result):
        if "PASS: T1i A/B/C/A full-frame U/V activation pixels=32000" not in simulation.stdout:
            errors+=1;print(simulation.stdout[-2500:])
    if errors:
        print(f"FAIL: T1i U/V oracle errors={errors}");return 1
    print("PASS: T1i independent U/V interpolation, shared depth winner, invalid zeroing, and atomic A/B/C/A activation (32,000 pixels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
