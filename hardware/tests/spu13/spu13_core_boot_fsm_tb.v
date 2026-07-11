// spu13_core_boot_fsm_tb.v — canonical boot-sequence FSM through the real core
//
// Copyright 2026 John Curley
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// RTL side of docs/BOOT_SEQUENCE_FSM.md (oracle: test_boot_sequence.py):
//   1. boot_ready low during VE hydration, high after, and an instruction
//      issued DURING hydration is held by the handshake then executes
//      (nothing lost, nothing overwritten);
//   2. SOM_HOST_HYDRATION=1 with no host writes: watchdog expires into
//      FAULT.HYDRATION_TIMEOUT — boot_ready never rises, instructions
//      never accepted (fault is terminal);
//   3. same config with the 28 host weight writes delivered: join
//      completes, boot_ready rises, dispatch opens.
`timescale 1ns/1ps

module spu13_core_boot_fsm_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    integer errors = 0;

    // ── DUT A: default config (VE hydration only) ───────────────────
    reg rst_n_a = 0;
    reg a_inst_valid = 0;
    reg [63:0] a_inst_word = 0;
    wire a_inst_done, a_boot_ready;

    spu13_core #(
        .DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0),
        .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(0), .ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0)
    ) dut_a (
        .clk(clk), .rst_n(rst_n_a),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(), .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(), .qr_commit_lane(),
        .qr_commit_A(), .qr_commit_B(), .qr_commit_C(), .qr_commit_D(),
        .inst_valid(a_inst_valid), .inst_word(a_inst_word), .inst_done(a_inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(),
        .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .rns_error(), .ecc_single_err(), .ecc_double_err(),
        .rotc_debug_status(), .boot_ready(a_boot_ready)
    );

    // ── DUT B: SOM host hydration required, tiny watchdog ──────────
    reg rst_n_b = 0;
    reg b_cfg_we = 0;
    reg [9:0] b_cfg_addr = 0;
    reg [63:0] b_cfg_data = 0;
    reg b_inst_valid = 0;
    reg [63:0] b_inst_word = 0;
    wire b_inst_done, b_boot_ready;

    spu13_core #(
        .DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0),
        .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(1),
        .ENABLE_CORE_RPLU_V2(0), .ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .SOM_HOST_HYDRATION(1),
        .BOOT_WATCHDOG_CYCLES(16'd60)
    ) dut_b (
        .clk(clk), .rst_n(rst_n_b),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(b_cfg_we), .dec_fast_cfg_sel(3'd4),  // SOM_CFG_WEIGHT
        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(b_cfg_addr),
        .dec_fast_cfg_data(b_cfg_data), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),
        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(),
        .mem_rd_manifold(832'd0), .mem_wr_manifold(), .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(), .qr_commit_lane(),
        .qr_commit_A(), .qr_commit_B(), .qr_commit_C(), .qr_commit_D(),
        .inst_valid(b_inst_valid), .inst_word(b_inst_word), .inst_done(b_inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(),
        .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .rns_error(), .ecc_single_err(), .ecc_double_err(),
        .rotc_debug_status(), .boot_ready(b_boot_ready)
    );

    task check;
        input cond;
        input [255:0] label;
        begin
            if (cond) $display("PASS %0s", label);
            else begin
                $display("FAIL %0s", label);
                errors = errors + 1;
            end
        end
    endtask

    // inst_done is a one-cycle pulse — capture it sticky for the scenario-1
    // check, since completion may occur inside the boot_ready polling loop.
    reg a_done_seen = 0;
    always @(posedge clk) if (a_inst_done) a_done_seen <= 1'b1;

    integer i, guard, rise_cycle;
    initial begin
        // ═══ Scenario 1: DUT A — hydration hold then dispatch ═══
        repeat (4) @(posedge clk);
        rst_n_a = 1;
        check(a_boot_ready === 1'b0, "A: boot_ready low at reset release");

        // Issue QLDI QR1 immediately — must be HELD, not lost/overwritten
        @(posedge clk);
        a_inst_word  = {8'h1D, 8'd1, 8'd0, 8'd7, 8'd8, 8'd9, 8'd10, 8'd0};
        a_inst_valid = 1;

        // boot_ready must rise within the VE walk + margin (spec: 13 lanes)
        rise_cycle = -1;
        for (i = 0; i < 40; i = i + 1) begin
            @(posedge clk);
            if (a_boot_ready === 1'b1 && rise_cycle == -1) rise_cycle = i;
        end
        check(rise_cycle != -1, "A: boot_ready rises after hydration");
        check(rise_cycle < 30, "A: rise within VE walk + margin (<30 cycles)");

        // the held instruction must complete now (sticky-captured: the done
        // pulse may already have fired inside the polling loop above)
        guard = 0;
        while (!a_done_seen && guard < 50) begin @(posedge clk); guard = guard + 1; end
        a_inst_valid = 0;
        check(a_done_seen, "A: instruction issued mid-hydration completes after READY");
        @(posedge clk);
        check(dut_a.gen_qrf.u_qrf.u_regfile.reg_A[1][31:0] === 32'd7,
              "A: held QLDI landed intact (not eaten by hydration)");

        // ═══ Scenario 2: DUT B — watchdog fault, terminal ═══
        repeat (2) @(posedge clk);
        rst_n_b = 1;
        // no SOM writes: watchdog (60) must expire
        repeat (80) @(posedge clk);
        check(b_boot_ready === 1'b0, "B: boot_ready never rises without SOM hydration");
        check(dut_b.boot_state === 2'd3, "B: FSM in FAULT.HYDRATION_TIMEOUT");

        // instructions must not be accepted in FAULT
        @(posedge clk);
        b_inst_word  = {8'h1D, 8'd1, 8'd0, 8'd1, 8'd2, 8'd3, 8'd4, 8'd0};
        b_inst_valid = 1;
        repeat (30) @(posedge clk);
        b_inst_valid = 0;
        check(dut_b.gen_qrf.u_qrf.u_regfile.reg_A[1][31:0] !== 32'd1,
              "B: no instruction accepted in FAULT (terminal)");

        // ═══ Scenario 3: DUT B rerun — hydrate 28 writes, join completes ═══
        rst_n_b = 0;
        repeat (3) @(posedge clk);
        rst_n_b = 1;
        @(posedge clk);
        for (i = 0; i < 28; i = i + 1) begin
            b_cfg_we   = 1;
            b_cfg_addr = i[9:0];
            b_cfg_data = 64'h0000_0001_0000_0001;
            @(posedge clk);
        end
        b_cfg_we = 0;
        repeat (25) @(posedge clk);
        check(b_boot_ready === 1'b1, "B: join completes after 28 SOM writes, READY");

        if (errors == 0) $display("spu13_core_boot_fsm_tb: PASS");
        else begin
            $display("spu13_core_boot_fsm_tb: FAIL (%0d errors)", errors);
            $display("FAIL");
        end
        $finish;
    end
endmodule
