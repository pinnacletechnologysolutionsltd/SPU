`timescale 1ns / 1ps
// A31-R3 directed probe: core RPLU2 arithmetic refusal (Pade flags_v) must end the instruction through a distinct refusal pulse
// aligned with inst_done, never through result-valid / commit telemetry. H0 configuration; `INV selects USE_STRUCTURED_INVERTER (0/1).
// Zero-divisor witness (denominator constant 2CEE24B2,0,0,1) as in A31-R2. Driver enforces the single-outstanding assumption.
// Not a regression-gate testbench (file name avoids 'tb'); run via run_a31_r3.py. Exits nonzero ($fatal) on any failed check.
`ifndef INV
`define INV 0
`endif
module a31r3_core_probe;
    reg clk = 1'b0; always #5 clk = ~clk;
    reg rst_n = 1'b0; reg inst_valid = 1'b0; reg [63:0] inst_word = 64'd0;
    reg cfg_wr_en = 1'b0; reg [2:0] cfg_sel = 3'd0; reg [9:0] cfg_addr = 10'd0; reg [63:0] cfg_data = 64'd0;
    wire inst_done, dref, aref, qr_commit_valid; wire [3:0] qr_commit_lane; wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    spu13_core #(.DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(1), .ENABLE_CORE_RPLU_V2_PIPELINE(1), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0), .SHARE_RPLU_PADE_INV_MULT(1),
        .USE_STRUCTURED_INVERTER(`INV)) uut (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(cfg_wr_en), .dec_fast_cfg_sel(cfg_sel), .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(cfg_addr),
        .dec_fast_cfg_data(cfg_data), .phinary_cfg(16'd0), .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0), .boot_done(1'b1),
        .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0), .mem_ready(1'b1),
        .mem_burst_rd(), .mem_burst_wr(), .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(), .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(), .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane), .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D), .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .rplu2_domain_refused(dref), .rplu2_arith_refused(aref), .ratio_cmp_res(), .ratio_cmp_valid(), .manifold_out(), .bloom_complete(),
        .scale_table_out(), .scale_overflow_out(), .is_janus_point(), .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(), .i2s_bclk(), .i2s_lrclk(), .i2s_dout(), .laminar_flow_index_out(),
        .thermal_pressure_out(), .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(), .axiomatic_fault(), .fault_type(),
        .fault_count(), .rns_error(), .ecc_single_err(), .ecc_double_err());

    integer cyc = 0, n_done = 0, n_dref = 0, n_aref = 0, n_resv = 0, n_commit = 0, n_thim = 0, n_thimref = 0, c_done = -1, c_aref = -1;
    reg logging = 1'b0;
    always @(posedge clk) if (logging) begin
        cyc = cyc + 1;
        if (inst_done) begin n_done = n_done + 1; if (c_done < 0) c_done = cyc; end
        if (dref) n_dref = n_dref + 1;
        if (aref) begin n_aref = n_aref + 1; if (c_aref < 0) c_aref = cyc; end
        if (uut.rplu2_result_valid) n_resv = n_resv + 1;
        if (qr_commit_valid) n_commit = n_commit + 1;
        if (uut.gen_rplu_v2.rplu2_thimble_valid) n_thim = n_thim + 1;
        if (uut.gen_rplu_v2.rplu2_thimble_refused) n_thimref = n_thimref + 1;
    end
    task clear_counts; begin cyc = 0; n_done = 0; n_dref = 0; n_aref = 0; n_resv = 0; n_commit = 0; n_thim = 0; n_thimref = 0; c_done = -1; c_aref = -1; end endtask

    integer fails = 0, checks = 0, g, r, gi;
    task chk; input ok; input [255:0] what; begin checks = checks + 1; if (!ok) begin fails = fails + 1; $display("   CHECK FAILED: %0s", what); end end endtask
    function [63:0] w2a; input [3:0] dst, src; w2a = {8'h2A, 4'd0, dst, 4'd0, src, 40'd0}; endfunction
    function [63:0] qldi; input [7:0] lane; input signed [7:0] a, b, c, d; qldi = {8'h1D, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0}; endfunction
    function [63:0] sig; input dummy; integer i; reg [63:0] h; begin h = 64'd0;
        for (i = 0; i < 13; i = i + 1) h = {h[58:0], h[63:59]} ^ uut.gen_qrf.u_qrf.u_regfile.reg_A[i] ^ (uut.gen_qrf.u_qrf.u_regfile.reg_B[i] * 3)
            ^ (uut.gen_qrf.u_qrf.u_regfile.reg_C[i] * 5) ^ (uut.gen_qrf.u_qrf.u_regfile.reg_D[i] * 7);
        sig = h; end endfunction
    task issue; input [63:0] w; begin @(posedge clk); inst_word <= w; inst_valid <= 1; @(posedge clk); inst_valid <= 0; end endtask
    task cfg_write; input [2:0] sel; input [9:0] addr; input [63:0] data; begin
        @(negedge clk); cfg_sel = sel; cfg_addr = addr; cfg_data = data; cfg_wr_en = 1; @(negedge clk); cfg_wr_en = 0; cfg_sel = 0; cfg_addr = 0; cfg_data = 0; end endtask
    task set_num0; input [31:0] c0, c1, c2, c3; begin cfg_write(3'd1, 10'd0, {c1, c0}); cfg_write(3'd1, 10'd8, {c3, c2}); end endtask
    task set_den0; input [31:0] c0, c1, c2, c3; begin cfg_write(3'd2, 10'd0, {c1, c0}); cfg_write(3'd2, 10'd8, {c3, c2}); end endtask
    task wait_ready; begin g = 0; while (!uut.boot_ready && g < 300) begin @(posedge clk); g = g + 1; end repeat (4) @(posedge clk); end endtask
    task setup; begin   // reset, SET-N-style configuration, source lane 3 = (2,0,0,0)
        logging = 0; rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); rst_n <= 1; @(posedge clk); wait_ready;
        set_num0(32'd2, 32'd0, 32'd0, 32'd0); set_den0(32'd1, 32'd0, 32'd0, 32'd0);
        for (r = 0; r < 7; r = r + 1) begin cfg_write(3'd3, r, {32'd0, 32'd1}); cfg_write(3'd3, r + 64, 64'd0); end
        cfg_write(3'd6, 10'd0, 64'd3);
        issue(qldi(8'd3, 8'sd2, 8'sd0, 8'sd0, 8'sd0)); repeat (10) @(posedge clk); end endtask
    task witness; begin set_den0(32'h2CEE24B2, 32'd0, 32'd0, 32'd1); end endtask   // SET-R: zero-divisor denominator
    task setden1; begin set_den0(32'd1, 32'd0, 32'd0, 32'd0); end endtask           // SET-N denominator

    reg [63:0] sig0; reg [319:0] cm0, cm1; reg [63:0] lastA;
    // kind: 0 = success, 1 = arithmetic refusal. Waits long enough to catch late or duplicate events.
    task txn; input [255:0] name; input integer kind; input [63:0] expA; begin
        sig0 = sig(0); cm0 = {qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D};
        clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); repeat (1400) @(posedge clk); logging = 0;
        cm1 = {qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D};
        chk(n_done == 1 && n_dref == 0, "exactly one completion, no domain refusal");
        chk(sig0 == sig(0), "no QR register write");
        if (kind == 0) begin
            chk(n_aref == 0 && n_resv == 1 && n_commit == 1 && n_thim == 1 && n_thimref == 0, "success: result and commit, no refusal");
            chk(qr_commit_lane == 4'd4 && qr_commit_A === expA && qr_commit_B === 64'd0 && qr_commit_C === 64'd0 && qr_commit_D === 64'd0, "success telemetry equals independent expectation");
        end else begin
            chk(n_aref == 1 && c_aref == c_done && n_resv == 0 && n_commit == 0 && n_thim == 1 && n_thimref == 1, "refusal: one aligned pulse, no result or commit");
            chk(cm0 === cm1, "commit telemetry unchanged (historical)");
        end
        $display("TXN %0s kind=%0d done=%0d aref=%0d dref=%0d resv=%0d commit=%0d thim=%0d thimref=%0d A=%h", name, kind, n_done, n_aref, n_dref, n_resv, n_commit, n_thim, n_thimref, qr_commit_A);
    end endtask
    // reset scenarios: count events after the reset is released
    task quiet_after; input [255:0] name; begin
        rst_n <= 1; clear_counts; repeat (1500) @(posedge clk); logging = 0;
        chk(n_done == 0 && n_aref == 0 && n_dref == 0 && n_resv == 0 && n_commit == 0, "no completion, refusal or result after reset");
        $display("RST %0s done=%0d aref=%0d dref=%0d resv=%0d commit=%0d", name, n_done, n_aref, n_dref, n_resv, n_commit); end endtask

    initial begin
        $display("== SET-N success / SET-R refusal / recovery in one session");
        setup; txn("S1 success (num0=2 den0=1)", 0, 64'd2);
        witness; txn("R1 refusal after success", 1, 64'd0);
        setden1; txn("S1b success after refusal", 0, 64'd2);
        $display("== second independent success vector (num0=3 den0=2 -> 3/2 = 1073741825)");
        set_num0(32'd3, 32'd0, 32'd0, 32'd0); set_den0(32'd2, 32'd0, 32'd0, 32'd0); txn("S2 success (3/2)", 0, 64'd1073741825);
        $display("== refusal as the first transaction after reset");
        setup; witness; txn("R0 refusal first after reset", 1, 64'd0);
        $display("== numeric-domain refusal unchanged (out-of-domain operand, valid denominator)");
        setup; @(negedge clk); force uut.gen_qrf.u_qrf.wr_en = 1'b1; force uut.gen_qrf.u_qrf.wr_lane = 4'd3; force uut.gen_qrf.u_qrf.wr_A = 64'd9458;
        force uut.gen_qrf.u_qrf.wr_B = 64'd0; force uut.gen_qrf.u_qrf.wr_C = 64'd0; force uut.gen_qrf.u_qrf.wr_D = 64'd0; @(negedge clk);
        release uut.gen_qrf.u_qrf.wr_en; release uut.gen_qrf.u_qrf.wr_lane; release uut.gen_qrf.u_qrf.wr_A; release uut.gen_qrf.u_qrf.wr_B;
        release uut.gen_qrf.u_qrf.wr_C; release uut.gen_qrf.u_qrf.wr_D; @(negedge clk);
        sig0 = sig(0); clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); repeat (300) @(posedge clk); logging = 0;
        chk(n_dref == 1 && n_aref == 0 && n_done == 1 && n_resv == 0 && n_commit == 0 && n_thim == 0 && sig0 == sig(0), "domain refusal: one pulse, no arithmetic refusal, nothing launched");
        $display("DOM done=%0d dref=%0d aref=%0d resv=%0d thim=%0d", n_done, n_dref, n_aref, n_resv, n_thim);
        $display("== reset during an outstanding operation (mid-Pade) then recovery");
        setup; clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); repeat (300) @(posedge clk); #3 rst_n = 0; repeat (4) @(posedge clk); quiet_after("mid-Pade");
        setup; txn("S1 recovery after reset", 0, 64'd2);
        $display("== reset in the cycle where a refusal completes (pade_done) and in the thimble_refused cycle");
        for (gi = 0; gi < 2; gi = gi + 1) begin
            setup; witness; clear_counts; logging = 1; issue(w2a(4'd4, 4'd3));
            if (gi == 0) begin r = 0; while (!uut.gen_rplu_v2.u_rplu_v2.pade_done && r < 1500) begin @(posedge clk); r = r + 1; end end
            else begin r = 0; while (!uut.gen_rplu_v2.rplu2_thimble_refused && r < 1500) begin @(posedge clk); r = r + 1; end end
            #3 rst_n = 0; repeat (4) @(posedge clk); quiet_after(gi == 0 ? "at-pade_done" : "at-thimble_refused");
            setup; witness; txn("R recovery after reset", 1, 64'd0); end
        $display("TOTAL checks=%0d fails=%0d", checks, fails);
        if (fails != 0) $fatal(1, "a31r3_core_probe: %0d check(s) failed", fails);
        $finish;
    end
    initial begin #2000000; $display("TIMEOUT"); $fatal(1, "timeout"); end
endmodule
