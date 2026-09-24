#!/usr/bin/env python3
"""Measure T1g pacing and audit four-lane activation state at the top level."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RTL_FILES = [
    "hardware/rtl/gpu/spu_gpu_top.v",
    "hardware/rtl/gpu/spu_video_timing.v",
    "hardware/rtl/gpu/spu_scene_loader.v",
    "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v",
    "hardware/rtl/gpu/spu_prepared_scene_control.v",
    "hardware/rtl/gpu/spu_prepared_scene_control4.v",
    "hardware/rtl/gpu/spu_dual_raster.v",
    "hardware/rtl/gpu/spu_quad_raster.v",
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
    "hardware/rtl/gpu/spu_depth_compare4.v",
    "hardware/rtl/hal/hal_vga.v",
    "hardware/rtl/hal/hal_hdmi.v",
    "hardware/rtl/hal/hal_hdmi_tmds.v",
    "hardware/rtl/hal/hal_hdmi_serdes_a7.v",
]

TB = r'''
`timescale 1ns/1ps
module t1g_pacing_tb;
    localparam integer H_ACTIVE=80, H_FP=2, H_SYNC=2, H_BP=2;
    localparam integer V_ACTIVE=100, V_FP=1, V_SYNC=1, V_BP=1;
    localparam integer FRAME_CYCLES=(H_ACTIVE+H_FP+H_SYNC+H_BP)*
        (V_ACTIVE+V_FP+V_SYNC+V_BP);
    localparam [1007:0] SCENE_A=1008'h{scene_a};
    localparam [1007:0] SCENE_B=1008'h{scene_b};
    localparam [1007:0] SCENE_C=1008'h{scene_c};
    reg clk=0, rst_n=0, rx_valid=0;
    reg [7:0] rx_byte=0;
    wire [3:0] vr,vg,vb;
    integer cycles=0, failures=0, i, trial;
    integer final_cycle, ready_cycle, activate_cycle, clear_cycle;
    integer start_phase, end_phase, ready_frame, activate_frame;
    reg [3:0] changed_frac_mask=0;
    reg [1007:0] expected_active_scene=0;
    reg signed [55:0] model_A[0:3], model_B[0:3], model_C[0:3];
    reg [6:0] model_frac[0:3];
    integer frame_pixels=0, frame_failures=0;
    integer active_state_failures=0;

    spu_gpu_top #(.DEVICE("A7"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1),.H_ACTIVE(H_ACTIVE),.H_FP(H_FP),
        .H_SYNC(H_SYNC),.H_BP(H_BP),.V_ACTIVE(V_ACTIVE),.V_FP(V_FP),
        .V_SYNC(V_SYNC),.V_BP(V_BP)) dut (
        .clk_pixel(clk),.clk_tmds(clk),.rst_n(rst_n),
        .tri0_setup(1'b0),.tri0_a0(16'sd0),.tri0_b0(16'sd0),.tri0_c0(32'sd0),
        .tri0_a1(16'sd0),.tri0_b1(16'sd0),.tri0_c1(32'sd0),
        .tri0_a2(16'sd0),.tri0_b2(16'sd0),.tri0_c2(32'sd0),
        .tri0_r(4'd0),.tri0_g(4'd0),.tri0_b(4'd0),
        .tri0_z0(16'd0),.tri0_z1(16'd0),.tri0_z2(16'd0),
        .tri1_setup(1'b0),.tri1_a0(16'sd0),.tri1_b0(16'sd0),.tri1_c0(32'sd0),
        .tri1_a1(16'sd0),.tri1_b1(16'sd0),.tri1_c1(32'sd0),
        .tri1_a2(16'sd0),.tri1_b2(16'sd0),.tri1_c2(32'sd0),
        .tri1_r(4'd0),.tri1_g(4'd0),.tri1_b(4'd0),
        .tri1_z0(16'd0),.tri1_z1(16'd0),.tri1_z2(16'd0),
        .scene_rx_byte(rx_byte),.scene_rx_valid(rx_valid),
        .vga_r(vr),.vga_g(vg),.vga_b(vb),.vga_hsync(),.vga_vsync(),
        .tmds_clk_p(),.tmds_clk_n(),.tmds_d_p(),.tmds_d_n());

    always #1 clk=~clk;
    always @(posedge clk) if (rst_n) cycles=cycles+1;

    function integer frame_phase;
        begin frame_phase=(dut.u_timing.y*(H_ACTIVE+H_FP+H_SYNC+H_BP))+dut.u_timing.x; end
    endfunction
    function integer frame_number;
        begin frame_number=cycles/FRAME_CYCLES; end
    endfunction

    function [11:0] oracle_rgb(input [1007:0] scene, input integer px, input integer py);
        integer p, e;
        reg [251:0] rec;
        reg signed [15:0] ea, eb;
        reg signed [31:0] ec, edge_value;
        reg covered;
        reg signed [55:0] accum, depth_value, best_depth;
        reg best_valid;
        reg [11:0] best_rgb;
        begin
            best_valid=0; best_depth=0; best_rgb=0;
            for (p=0;p<4;p=p+1) begin
                rec=(scene >> (p*252));
                covered=1;
                for (e=0;e<3;e=e+1) begin
                    case (e)
                        0: begin ea=$signed(rec[15:0]); eb=$signed(rec[31:16]); ec=$signed(rec[63:32]); end
                        1: begin ea=$signed(rec[79:64]); eb=$signed(rec[95:80]); ec=$signed(rec[127:96]); end
                        default: begin ea=$signed(rec[143:128]); eb=$signed(rec[159:144]); ec=$signed(rec[191:160]); end
                    endcase
                    edge_value=ea*px + eb*py + ec;
                    if (edge_value < 0) covered=0;
                end
                accum=model_A[p]*px + model_B[p]*py + model_C[p];
                depth_value=accum >>> model_frac[p];
                if (covered && (!best_valid || depth_value < best_depth)) begin
                    best_valid=1; best_depth=depth_value;
                    best_rgb={{rec[195:192],rec[199:196],rec[203:200]}};
                end
            end
            oracle_rgb=best_rgb;
        end
    endfunction

    task check_frame_pixel(input [1007:0] scene, input integer px, input integer py);
        reg [11:0] expected;
        begin
            expected=oracle_rgb(scene,px,py);
            frame_pixels=frame_pixels+1;
            if ({{vr,vg,vb}} !== expected) begin
                frame_failures=frame_failures+1;
                failures=failures+1;
                if (frame_failures<=12)
                    $display("FAIL: first-frame pixel scene=%0d xy=(%0d,%0d) expected=%h got=%h",
                        scene===SCENE_B ? 1 : scene===SCENE_C ? 2 : 0,px,py,expected,{{vr,vg,vb}});
            end
            if (dut.active_scene !== scene) begin
                failures=failures+1;
                if (frame_failures<=12)
                    $display("FAIL: active raw scene changed within first frame at (%0d,%0d)",px,py);
            end
            if (dut.attr_A_z0 !== model_A[0] || dut.attr_B_z0 !== model_B[0] ||
                dut.attr_C_z0 !== model_C[0] || dut.attr_frac_bits0 !== model_frac[0] ||
                dut.attr_A_z1 !== model_A[1] || dut.attr_B_z1 !== model_B[1] ||
                dut.attr_C_z1 !== model_C[1] || dut.attr_frac_bits1 !== model_frac[1] ||
                dut.attr_A_z2 !== model_A[2] || dut.attr_B_z2 !== model_B[2] ||
                dut.attr_C_z2 !== model_C[2] || dut.attr_frac_bits2 !== model_frac[2] ||
                dut.attr_A_z3 !== model_A[3] || dut.attr_B_z3 !== model_B[3] ||
                dut.attr_C_z3 !== model_C[3] || dut.attr_frac_bits3 !== model_frac[3]) begin
                failures=failures+1;
                if (frame_failures<=12)
                    $display("FAIL: per-pixel derived state is not one committed generation at (%0d,%0d)",px,py);
            end
        end
    endtask

    task check_first_frame(input [1007:0] scene);
        integer x, y, target_phase;
        begin
            frame_failures=0;
            // The activation edge renders sample (0,0); its post-edge timing
            // counter is already at phase 1.
            check_frame_pixel(scene,0,0);
            for (y=0;y<V_ACTIVE;y=y+1) begin
                for (x=0;x<H_ACTIVE;x=x+1) begin
                    if (!(x==0 && y==0)) begin
                        target_phase=y*(H_ACTIVE+H_FP+H_SYNC+H_BP)+x;
                        while (frame_phase()!=target_phase) @(negedge clk);
                        @(posedge clk); #0.1;
                        check_frame_pixel(scene,x,y);
                    end
                end
            end
            if (frame_failures==0)
                $display("FRAME PASS: first complete frame pixels=%0d scene=%0d",
                    H_ACTIVE*V_ACTIVE,scene===SCENE_B ? 1 : scene===SCENE_C ? 2 : 0);
            else $display("FRAME FAIL: mismatches=%0d",frame_failures);
        end
    endtask

    task send_byte(input [7:0] v); begin
        @(negedge clk); rx_byte=v; rx_valid=1;
        @(negedge clk); rx_valid=0; rx_byte=0;
    end endtask
    task capture_active_derived_state; begin
        model_A[0]=dut.active_A_z0; model_B[0]=dut.active_B_z0; model_C[0]=dut.active_C_z0; model_frac[0]=dut.active_frac_bits0;
        model_A[1]=dut.active_A_z1; model_B[1]=dut.active_B_z1; model_C[1]=dut.active_C_z1; model_frac[1]=dut.active_frac_bits1;
        model_A[2]=dut.active_A_z2; model_B[2]=dut.active_B_z2; model_C[2]=dut.active_C_z2; model_frac[2]=dut.active_frac_bits2;
        model_A[3]=dut.active_A_z3; model_B[3]=dut.active_B_z3; model_C[3]=dut.active_C_z3; model_frac[3]=dut.active_frac_bits3;
    end endtask
    task check_active_derived_stable(input [8*40-1:0] phase_name); begin
        if (dut.active_A_z0 !== model_A[0] || dut.active_B_z0 !== model_B[0] || dut.active_C_z0 !== model_C[0] || dut.active_frac_bits0 !== model_frac[0] ||
            dut.active_A_z1 !== model_A[1] || dut.active_B_z1 !== model_B[1] || dut.active_C_z1 !== model_C[1] || dut.active_frac_bits1 !== model_frac[1] ||
            dut.active_A_z2 !== model_A[2] || dut.active_B_z2 !== model_B[2] || dut.active_C_z2 !== model_C[2] || dut.active_frac_bits2 !== model_frac[2] ||
            dut.active_A_z3 !== model_A[3] || dut.active_B_z3 !== model_B[3] || dut.active_C_z3 !== model_C[3] || dut.active_frac_bits3 !== model_frac[3]) begin
            if (active_state_failures==0)
                $display("FAIL: active derived tuple changed during %0s lane0=%0d,%0d model=%0d,%0d frac=%0d/%0d",
                    phase_name,dut.active_A_z0,dut.active_C_z0,model_A[0],model_C[0],dut.active_frac_bits0,model_frac[0]);
            active_state_failures=active_state_failures+1; failures=failures+1;
        end
    end endtask
    task send_scene(input [1007:0] s); begin
        send_byte(8'hA5);
        for (i=0;i<126;i=i+1) begin
            send_byte(s[i*8 +: 8]);
            if (dut.active_scene !== expected_active_scene) begin
                $display("FAIL: active raw scene changed during candidate receipt byte=%0d",i);
                failures=failures+1;
            end
            check_active_derived_stable("candidate receipt");
        end
        if (dut.candidate_scene !== s || !dut.scene_commit_pending) begin
            $display("FAIL: complete scene did not remain a pending private candidate");
            failures=failures+1;
        end
        final_cycle=cycles;
        end_phase=frame_phase();
    end endtask
    task wait_phase(input integer target); begin
        while (frame_phase()!=target) @(negedge clk);
    end endtask
    task measure_transition(input [1007:0] scene, input integer target_phase);
        integer packet_start_phase;
        reg [1007:0] old_scene;
        begin
            old_scene=dut.active_scene;
            capture_active_derived_state();
            packet_start_phase=(target_phase-254+FRAME_CYCLES)%FRAME_CYCLES;
            wait_phase(packet_start_phase);
            send_scene(scene);
            start_phase=end_phase;
            ready_frame=-1;
            while (!(dut.prepared_generation_matches &&
                dut.prepared_ready0 && dut.prepared_ready1 &&
                dut.prepared_ready2 && dut.prepared_ready3)) begin
                if (dut.active_scene !== old_scene || dut.candidate_scene !== scene ||
                    !dut.scene_commit_pending) begin
                    $display("FAIL: active/candidate bank changed during scene preparation");
                    failures=failures+1;
                end
                check_active_derived_stable("candidate preparation");
                if (dut.activate_scene) begin
                    $display("FAIL: candidate activated before all four ready results matched");
                    failures=failures+1;
                end
                @(negedge clk);
            end
            ready_cycle=cycles;
            ready_frame=frame_number();
            while (!dut.activate_scene) @(negedge clk);
            if (dut.prepared_ready3 && dut.prepared_ready2 && dut.prepared_ready1 && dut.prepared_ready0 &&
                dut.prepared_generation_matches) begin end
            else begin $display("FAIL: activation lacks four ready generation-matched results"); failures=failures+1; end
            if (dut.prepared_depth_control.u_prepared_control4.result_generation !==
                {{4{{dut.prepared_depth_control.u_prepared_control4.candidate_generation}}}}) begin
                $display("FAIL: result generation identity differs at activation"); failures=failures+1;
            end
            if (dut.active_frac_bits0 !== dut.frac_bits0 && dut.attr_frac_bits0 !== dut.frac_bits0) begin
                $display("FAIL: lane 0 activation fraction stale old=%0d new=%0d selected=%0d",
                    dut.active_frac_bits0,dut.frac_bits0,dut.attr_frac_bits0); failures=failures+1;
            end
            if (dut.active_frac_bits1 !== dut.frac_bits1 && dut.attr_frac_bits1 !== dut.frac_bits1) begin
                $display("FAIL: lane 1 activation fraction stale old=%0d new=%0d selected=%0d",
                    dut.active_frac_bits1,dut.frac_bits1,dut.attr_frac_bits1); failures=failures+1;
            end
            if (dut.attr_frac_bits2 !== dut.frac_bits2 || dut.attr_frac_bits3 !== dut.frac_bits3) begin
                $display("FAIL: lane 2/3 activation fractions do not select candidates"); failures=failures+1;
            end
            if (dut.active_frac_bits0 !== dut.frac_bits0) changed_frac_mask[0]=1;
            if (dut.active_frac_bits1 !== dut.frac_bits1) changed_frac_mask[1]=1;
            if (dut.active_frac_bits2 !== dut.frac_bits2) changed_frac_mask[2]=1;
            if (dut.active_frac_bits3 !== dut.frac_bits3) changed_frac_mask[3]=1;
            model_A[0]=dut.A_z0; model_B[0]=dut.B_z0; model_C[0]=dut.C_z0; model_frac[0]=dut.frac_bits0;
            model_A[1]=dut.A_z1; model_B[1]=dut.B_z1; model_C[1]=dut.C_z1; model_frac[1]=dut.frac_bits1;
            model_A[2]=dut.A_z2; model_B[2]=dut.B_z2; model_C[2]=dut.C_z2; model_frac[2]=dut.frac_bits2;
            model_A[3]=dut.A_z3; model_B[3]=dut.B_z3; model_C[3]=dut.C_z3; model_frac[3]=dut.frac_bits3;
            if (dut.attr_A_z0 !== dut.A_z0 || dut.attr_B_z0 !== dut.B_z0 || dut.attr_C_z0 !== dut.C_z0 ||
                dut.attr_A_z1 !== dut.A_z1 || dut.attr_B_z1 !== dut.B_z1 || dut.attr_C_z1 !== dut.C_z1 ||
                dut.attr_A_z2 !== dut.A_z2 || dut.attr_B_z2 !== dut.B_z2 || dut.attr_C_z2 !== dut.C_z2 ||
                dut.attr_A_z3 !== dut.A_z3 || dut.attr_B_z3 !== dut.B_z3 || dut.attr_C_z3 !== dut.C_z3) begin
                $display("FAIL: activation coefficients do not select one candidate generation"); failures=failures+1;
            end
            activate_cycle=cycles;
            activate_frame=frame_number();
            @(posedge clk); #0.1;
            clear_cycle=cycles;
            if (dut.scene_commit_pending !== 1'b0) begin
                $display("FAIL: commit_pending did not clear with activation"); failures=failures+1;
            end
            if (dut.active_scene !== scene) begin
                $display("FAIL: active scene does not equal candidate after activation"); failures=failures+1;
            end
            expected_active_scene=scene;
            if (dut.active_frac_bits0 !== dut.frac_bits0 || dut.active_frac_bits1 !== dut.frac_bits1 ||
                dut.active_frac_bits2 !== dut.frac_bits2 || dut.active_frac_bits3 !== dut.frac_bits3) begin
                $display("FAIL: active fraction state did not commit as one four-lane set"); failures=failures+1;
            end
            if (dut.active_A_z0 !== dut.A_z0 || dut.active_B_z0 !== dut.B_z0 || dut.active_C_z0 !== dut.C_z0 ||
                dut.active_A_z1 !== dut.A_z1 || dut.active_B_z1 !== dut.B_z1 || dut.active_C_z1 !== dut.C_z1 ||
                dut.active_A_z2 !== dut.A_z2 || dut.active_B_z2 !== dut.B_z2 || dut.active_C_z2 !== dut.C_z2 ||
                dut.active_A_z3 !== dut.A_z3 || dut.active_B_z3 !== dut.B_z3 || dut.active_C_z3 !== dut.C_z3) begin
                $display("FAIL: active coefficient tuple differs from the ready candidate"); failures=failures+1;
            end
            if (!dut.depth_armed0 || !dut.depth_armed1 || !dut.depth_armed2 || !dut.depth_armed3) begin
                $display("FAIL: activation did not arm all four derived lanes"); failures=failures+1;
            end
            if (dut.prepared_ready0 || dut.prepared_ready1 || dut.prepared_ready2 || dut.prepared_ready3 ||
                dut.prepared_generation_matches) begin
                $display("FAIL: ready/generation validity was not consumed by activation"); failures=failures+1;
            end
            // The activation condition is sampled at the edge whose old
            // counter values are (0,0); after that edge the raster counter
            // has advanced to x=1.
            if (frame_phase()!=1) begin
                $display("FAIL: activation was not sampled at frame_start phase=%0d",frame_phase()); failures=failures+1;
            end
            if (ready_cycle<final_cycle || activate_cycle<ready_cycle || clear_cycle<activate_cycle) begin
                $display("FAIL: nonmonotonic event timestamps"); failures=failures+1;
            end
            check_first_frame(scene);
            $display("MEASURE target_phase=%0d final_phase=%0d final_to_ready=%0d ready_to_activate=%0d final_to_clear=%0d ready_frame=%0d activate_frame=%0d",
                target_phase,start_phase,ready_cycle-final_cycle,activate_cycle-ready_cycle,
                clear_cycle-final_cycle,ready_frame,activate_frame);
        end
    endtask

    initial begin
        repeat(5) @(negedge clk); rst_n=1;
        @(negedge clk); capture_active_derived_state();
        send_scene(SCENE_A);
        wait(dut.active_scene===SCENE_A);
        expected_active_scene=SCENE_A;
        wait_phase(1);
        // Probe final-byte phases just after frame start, mid-frame, and
        // immediately before the next frame boundary. Alternate A/B so every
        // measured transaction begins from a qualified active scene.
        measure_transition(SCENE_B, 5);
        measure_transition(SCENE_A, FRAME_CYCLES-5);
        measure_transition(SCENE_B, FRAME_CYCLES/2);
        measure_transition(SCENE_C, FRAME_CYCLES/3);
        measure_transition(SCENE_A, FRAME_CYCLES-100);
        if (changed_frac_mask !== 4'b1111) begin
            $display("FAIL: test scenes did not change frac_bits in every lane mask=%b",changed_frac_mask);
            failures=failures+1;
        end
        if (!failures) $display("PASS: T1g pacing characterization FRAME_CYCLES=%0d",FRAME_CYCLES);
        else $display("FAIL: T1g pacing characterization failures=%0d",failures);
        $finish;
    end
    initial begin #200000000; $display("FAIL: global timeout"); $finish; end
endmodule
'''


def fixture_scene(name: str) -> str:
    wire = bytes.fromhex((ROOT / "fixtures" / name).read_text().strip())
    if len(wire) != 127 or wire[0] != 0xA5:
        raise AssertionError(f"{name}: expected 127-byte A5 scene")
    return f"{int.from_bytes(wire[1:], 'little'):0252x}"


def main() -> int:
    tb_text = TB.format(
        scene_a=fixture_scene("gpu_t1f_scene_wire_127b.hex"),
        scene_b=fixture_scene("gpu_t1f_coverage_scene_wire_127b.hex"),
        scene_c=fixture_scene("gpu_t1g_scene_c_wire_127b.hex"),
    )
    with tempfile.TemporaryDirectory(prefix="spu_t1g_pacing_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1g_pacing_tb.v"
        out = temp / "t1g_pacing_tb.vvp"
        tb.write_text(tb_text)
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1g_pacing_tb", "-o", str(out), str(tb),
             *[str(ROOT / source) for source in RTL_FILES]],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if compile_result.returncode:
            print(compile_result.stdout, end="")
            print(compile_result.stderr, end="")
            return compile_result.returncode
        result = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=55,
        )
        print(result.stdout, end="")
        print(result.stderr, end="")
        if "PASS: T1g pacing characterization" not in result.stdout:
            return result.returncode or 1
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
