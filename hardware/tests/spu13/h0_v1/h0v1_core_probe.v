// h0v1_core_probe.v - H0-V1 directed instruction-acceptance probe (PRESERVED EVIDENCE, not a regression gate).
// Exercises spu13_core with the Artix-7 SPI-style one-cycle inst_valid strobe; read-only hierarchical observers; core-level stimulus, NOT the SPI transport.
// Run: python3 hardware/tests/spu13/h0_v1/run_h0_v1.py ; see docs/isa/ISA_V02_H0V1_FINDINGS.md.
// The file name deliberately avoids 'tb' so run_all_tests.py does not auto-discover it.
`timescale 1ns / 1ps
// H0-V1 scratch probe (outside tracked tree): one-cycle inst_valid strobes into spu13_core.
module h0v1_core_probe;
    reg clk = 1'b0; always #5 clk = ~clk;
    reg rst_n = 1'b0;
    reg boot_done = 1'b1;
    reg inst_valid = 1'b0; reg [63:0] inst_word = 64'd0;
    reg cfg_wr_en = 1'b0; reg [2:0] cfg_sel = 3'd0; reg [9:0] cfg_addr = 10'd0; reg [63:0] cfg_data = 64'd0;
    wire inst_done, qr_commit_valid;
    wire [3:0] qr_commit_lane; wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    localparam [2:0] CFG_PADE_NUM = 3'd1, CFG_PADE_DEN = 3'd2, CFG_BTU_ROW = 3'd3, CFG_KAPPA = 3'd6;

    spu13_core #(.DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1), .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0), .ENABLE_CORE_RPLU_V2(1), .ENABLE_CORE_RPLU_V2_PIPELINE(1),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0), .SHARE_RPLU_PADE_INV_MULT(1)) uut (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(cfg_wr_en), .dec_fast_cfg_sel(cfg_sel), .dec_fast_cfg_material(8'd0),
        .dec_fast_cfg_addr(cfg_addr), .dec_fast_cfg_data(cfg_data), .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0), .boot_done(boot_done),
        .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(), .mem_rd_manifold(832'd0),
        .mem_wr_manifold(), .mem_burst_done(1'b0), .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B), .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
        .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .ratio_cmp_res(), .ratio_cmp_valid(), .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(), .audio_mode(), .gasket_sum_out(), .quadrance_out(),
        .cycle_wrap(), .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(), .i2s_bclk(), .i2s_lrclk(),
        .i2s_dout(), .laminar_flow_index_out(), .thermal_pressure_out(), .hex_valid(), .hex_q(), .hex_r(),
        .audio_p_out(), .audio_q_out(), .axiomatic_fault(), .fault_type(), .fault_count(), .rns_error(),
        .ecc_single_err(), .ecc_double_err());

    function [63:0] pack; input [7:0] op, r1, r2; input [15:0] a, b; pack = {op, r1, r2, a, b, 8'd0}; endfunction
    function [63:0] qldi; input [7:0] lane; input signed [7:0] a, b, c, d;
        qldi = {8'h1D, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0}; endfunction

    // ---- observers (counted only while `logging`) ----
    integer cyc = 0, n_acc = 0, n_done = 0, n_commit = 0, n_rdt = 0, n_resv = 0, c_rdt = -1, c_resv = -1, c_qsub = -1;
    reg logging = 1'b0, verbose = 1'b0;
    always @(posedge clk) if (logging) begin
        cyc <= cyc + 1;
        if (uut.inst_accept) begin n_acc <= n_acc + 1; if (verbose) $display("  c=%0d accept op=%02h", cyc, inst_word[63:56]); end
        if (inst_done) begin n_done <= n_done + 1; if (verbose) $display("  c=%0d inst_done", cyc); end
        if (qr_commit_valid) begin n_commit <= n_commit + 1;
            if (verbose) $display("  c=%0d commit lane=%0d A=%h", cyc, qr_commit_lane, qr_commit_A[31:0]); end
        if (uut.rote_done_tdm) begin n_rdt <= n_rdt + 1; c_rdt <= cyc; if (verbose) $display("  c=%0d rote_done_tdm", cyc); end
        if (uut.rplu2_result_valid) begin n_resv <= n_resv + 1; c_resv <= cyc; if (verbose) $display("  c=%0d rplu2_result_valid", cyc); end
        if (uut.qsub_active && c_qsub < 0) c_qsub <= cyc;
    end

    task clear_counts; begin cyc = 0; n_acc = 0; n_done = 0; n_commit = 0; n_rdt = 0; n_resv = 0; c_rdt = -1; c_resv = -1; c_qsub = -1; end endtask
    function [127:0] lane_val; input [3:0] l;
        lane_val = {uut.gen_qrf.u_qrf.u_regfile.reg_A[l][31:0], uut.gen_qrf.u_qrf.u_regfile.reg_B[l][31:0],
                    uut.gen_qrf.u_qrf.u_regfile.reg_C[l][31:0], uut.gen_qrf.u_qrf.u_regfile.reg_D[l][31:0]}; endfunction
    function [63:0] sig; input dummy; integer i; reg [63:0] h; reg [127:0] v; begin h = 64'd0;
        for (i = 0; i < 13; i = i + 1) begin v = lane_val(i[3:0]); h = {h[58:0], h[63:59]} ^ v[127:64] ^ (v[63:0] * 3); end
        sig = h; end endfunction

    task do_reset; integer g; begin
        logging = 0; rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); rst_n <= 1; @(posedge clk);
        g = 0; while (!uut.boot_ready && g < 300) begin @(posedge clk); g = g + 1; end
        repeat (4) @(posedge clk); end endtask
    task cfg_write; input [2:0] sel; input [9:0] addr; input [63:0] data; begin
        @(negedge clk); cfg_sel = sel; cfg_addr = addr; cfg_data = data; cfg_wr_en = 1;
        @(negedge clk); cfg_wr_en = 0; cfg_sel = 0; cfg_addr = 0; cfg_data = 0; end endtask
    task issue_wait; input [63:0] w; integer g; begin   // setup only: one strobe, then wait for inst_done
        @(posedge clk); inst_word <= w; inst_valid <= 1; @(posedge clk); inst_valid <= 0;
        g = 0; while (!inst_done && g < 4000) begin @(posedge clk); g = g + 1; end repeat (3) @(posedge clk); end endtask
    task setup_basic; begin do_reset; issue_wait(qldi(8'd0, 8'sd1, 8'sd2, 8'sd3, 8'sd4)); issue_wait(qldi(8'd1, 8'sd5, 8'sd1, 8'sd1, 8'sd2)); end endtask
    task setup_pade; begin do_reset;
        cfg_write(CFG_PADE_NUM, 10'd0, {32'd0, 32'd2}); cfg_write(CFG_PADE_NUM, 10'd8, 64'd0);
        cfg_write(CFG_BTU_ROW, 10'd1, {32'd0, 32'd1}); cfg_write(CFG_BTU_ROW, 10'd65, 64'd0);
        issue_wait(qldi(8'd0, 8'sd2, 8'sd0, 8'sd0, 8'sd0)); issue_wait(qldi(8'd1, 8'sd5, 8'sd1, 8'sd1, 8'sd2));
        cfg_write(CFG_KAPPA, 10'd0, 64'd3); end endtask
    // two strobes: w1 sampled at edge 1, w2 at edge 1+gap (gap>=1); gap<0 => single strobe
    task run2; input [63:0] w1, w2; input integer gap, settle; integer c; begin
        clear_counts; logging = 1;
        if (gap == 1) $display("   NOTE gap=1: consecutive strobes hold inst_valid high (continuous-valid); not an independent collision");
        for (c = 0; c < settle; c = c + 1) begin
            @(posedge clk);
            inst_valid <= (c == 0) || (gap >= 1 && c == gap);
            inst_word  <= (c == 0) ? w1 : w2;
        end
        @(posedge clk); inst_valid <= 0; logging = 0; end endtask
    task show_lane; input [255:0] tag; input [3:0] l; reg [127:0] v; begin v = lane_val(l);
        $write(" %0s=(%0d,%0d,%0d,%0d)", tag, $signed(v[127:96]), $signed(v[95:64]), $signed(v[63:32]), $signed(v[31:0])); end endtask


    reg [63:0] sig0, sig1; integer k, g, nop; reg [7:0] op;
    reg [127:0] q6, q9, q5; reg ok6, ok9, ok5;
    localparam [127:0] E_ROTC = {32'sd1, 32'sd3, 32'sd2, 32'sd4};   // QR6 after ROTC angle1 on (1,2,3,4)
    localparam [127:0] E_QLDI = {32'sd7, 32'sd8, 32'sd9, 32'sd10};  // QR9 after intruder QLDI
    localparam [127:0] E_QSUB = {-32'sd4, 32'sd1, 32'sd2, 32'sd2};  // QR5 = QR0 - QR1 (basic setup)
    localparam [127:0] E_QSUB_P = {-32'sd3, -32'sd1, -32'sd1, -32'sd2}; // QR5 = QR0 - QR1 (pade setup)
    function [63:0] mk; input [7:0] op; mk = pack(op, 8'd2, 8'd0, 16'h0001, 16'h0000); endfunction
    task verdict_rotc_qldi; input integer gap; begin
        q6 = lane_val(6); q9 = lane_val(9);
        $display("RES rotc+qldi gap=%0d acc=%0d done=%0d commit=%0d rdt=%0d active_ok=%0d intruder_ok=%0d%s", gap, n_acc, n_done, n_commit, n_rdt,
                 q6 == E_ROTC, q9 == E_QLDI, (q6 == E_ROTC && q9 == E_QLDI && n_done == 2) ? "" : "  <-- ANOMALY"); end endtask
    initial begin
        $display("== B1 baseline timelines (c = cycle index; strobe sampled at c=1)");
        setup_basic; verbose = 1; run2(qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), 64'd0, -1, 40); verbose = 0;
        $display("   B1 QLDI: acc=%0d done=%0d commit=%0d", n_acc, n_done, n_commit);
        setup_basic; verbose = 1; run2(pack(8'h1C, 8'd6, 8'd0, 16'h0001, 16'h0000), 64'd0, -1, 80); verbose = 0;
        $display("   B2 ROTC: acc=%0d done=%0d commit=%0d", n_acc, n_done, n_commit);
        setup_basic; verbose = 1; run2(pack(8'h1B, 8'd5, 8'd0, 16'h0000, 16'h0001), 64'd0, -1, 40); verbose = 0;
        $display("   B3 QSUB: acc=%0d done=%0d commit=%0d qsub_active_first=%0d", n_acc, n_done, n_commit, c_qsub);
        setup_pade; verbose = 1; run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), 64'd0, -1, 2500); verbose = 0;
        $display("   B4 Pade 0x2A: acc=%0d done=%0d commit=%0d result_valid_cycle=%0d", n_acc, n_done, n_commit, c_resv);
        // ===== S1 single (see baselines) =====
        $display("== S1 single instructions after READY");
        setup_basic; sig0 = sig(0); run2(qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), 64'd0, -1, 40);
        $display("RES single qldi acc=%0d done=%0d commit=%0d state_changed=%0d QR9_ok=%0d", n_acc, n_done, n_commit, sig0 != sig(0), lane_val(9) == E_QLDI);
        // ===== S2 unsupported opcodes =====
        $display("== S2 opcodes outside the implemented set (core: ENABLE_MATH=1, RPLU2 pipeline; SOM, IROTC, Surd, extensions OFF)");
        for (nop = 0; nop < 40; nop = nop + 1) begin
            case (nop)
                0: op=8'h00; 1: op=8'h01; 2: op=8'h02; 3: op=8'h03; 4: op=8'h04; 5: op=8'h05; 6: op=8'h06; 7: op=8'h07; 8: op=8'h08;
                9: op=8'h10; 10: op=8'h11; 11: op=8'h12; 12: op=8'h13; 13: op=8'h14; 14: op=8'h15; 15: op=8'h17; 16: op=8'h18; 17: op=8'h19;
                18: op=8'h1A; 19: op=8'h1F; 20: op=8'h20; 21: op=8'h21; 22: op=8'h22; 23: op=8'hFF; 24: op=8'h2B; 25: op=8'hD6; 26: op=8'hD7;
                27: op=8'hD8; 28: op=8'h70; 29: op=8'h76; 30: op=8'h77; 31: op=8'h48; 32: op=8'h4C; 33: op=8'h5A; 34: op=8'hA0; 35: op=8'h30;
                36: op=8'h31; 37: op=8'h60; 38: op=8'h61; default: op=8'hE0;
            endcase
            setup_basic; sig0 = sig(0); run2(mk(op), 64'd0, -1, 60);
            $display("RES op=%02h acc=%0d done=%0d commit=%0d state_changed=%0d", op, n_acc, n_done, n_commit, sig0 != sig(0));
        end
        // ===== S3/S4/S5 overlap and priority windows =====
        $display("== S3 ROTC (QR6<-QR0 angle1) then QLDI intruder QR9 at gap g (ROTC: accept c=1, rote_done_tdm c=5, done c=6)");
        for (g = 1; g <= 9; g = g + 1) begin setup_basic;
            run2(pack(8'h1C, 8'd6, 8'd0, 16'h0001, 16'h0000), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), g, 80); verdict_rotc_qldi(g); end
        $display("== S3b QLDI then ROTC at gap g");
        for (g = 1; g <= 4; g = g + 1) begin setup_basic;
            run2(qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), pack(8'h1C, 8'd6, 8'd0, 16'h0001, 16'h0000), g, 80); verdict_rotc_qldi(g); end
        $display("== S3c ROTC then ROTC (same dest) at gap g");
        for (g = 1; g <= 7; g = g + 1) begin setup_basic;
            run2(pack(8'h1C, 8'd6, 8'd0, 16'h0001, 16'h0000), pack(8'h1C, 8'd7, 8'd0, 16'h0002, 16'h0000), g, 80);
            $display("RES rotc+rotc gap=%0d acc=%0d done=%0d commit=%0d QR6=%0d QR7=%0d%s", g, n_acc, n_done, n_commit,
                     lane_val(6) == E_ROTC, lane_val(7) == {32'sd1, 32'sd4, 32'sd2, 32'sd3}, (n_done == 2 && lane_val(6) == E_ROTC && lane_val(7) == {32'sd1, 32'sd4, 32'sd2, 32'sd3}) ? "" : "  <-- ANOMALY"); end
        $display("== S5b after the ROTC/QLDI collision (gap=4): is the core left wedged? follow-up ROTC QR8<-QR0 angle1");
        setup_basic; run2(pack(8'h1C, 8'd6, 8'd0, 16'h0001, 16'h0000), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), 4, 80);
        $display("   after collision: rote_active=%0d rotc_busy_flag=%0d QR6_ok=%0d", uut.rote_active, uut.rotc_debug_busy, lane_val(6) == E_ROTC);
        run2(pack(8'h1C, 8'd8, 8'd0, 16'h0001, 16'h0000), 64'd0, -1, 200);
        $display("RES followup rotc acc=%0d done=%0d commit=%0d QR8_ok=%0d rote_active=%0d", n_acc, n_done, n_commit, lane_val(8) == E_ROTC, uut.rote_active);
        $display("== S4 QSUB (QR5=QR0-QR1; qsub_active from c=2, done c=4) then QLDI intruder at gap g");
        for (g = 1; g <= 5; g = g + 1) begin setup_basic;
            run2(pack(8'h1B, 8'd5, 8'd0, 16'h0000, 16'h0001), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), g, 60);
            q5 = lane_val(5); q9 = lane_val(9);
            $display("RES qsub+qldi gap=%0d acc=%0d done=%0d commit=%0d active_ok=%0d intruder_ok=%0d%s", g, n_acc, n_done, n_commit, q5 == E_QSUB, q9 == E_QLDI,
                     (q5 == E_QSUB && q9 == E_QLDI && n_done == 2) ? "" : "  <-- ANOMALY"); end
        $display("== S4b ROTC then QSUB intruder at gap g");
        for (g = 1; g <= 7; g = g + 1) begin setup_basic;
            run2(pack(8'h1C, 8'd6, 8'd0, 16'h0001, 16'h0000), pack(8'h1B, 8'd5, 8'd0, 16'h0000, 16'h0001), g, 80);
            q6 = lane_val(6); q5 = lane_val(5);
            $display("RES rotc+qsub gap=%0d acc=%0d done=%0d commit=%0d active_ok=%0d intruder_ok=%0d%s", g, n_acc, n_done, n_commit, q6 == E_ROTC, q5 == E_QSUB,
                     (q6 == E_ROTC && q5 == E_QSUB && n_done == 2) ? "" : "  <-- ANOMALY"); end
        $display("== S4c Pade 0x2A (accept c=1, rplu2_result_valid c=555, done c=556) then QLDI intruder at gap g");
        for (g = 100; g <= 100; g = g + 1) begin setup_pade;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), g, 900);
            $display("RES pade+qldi gap=%0d acc=%0d done=%0d commit=%0d intruder_ok=%0d resv=%0d%s", g, n_acc, n_done, n_commit, lane_val(9) == E_QLDI, n_resv,
                     (n_done == 2 && lane_val(9) == E_QLDI) ? "" : "  <-- ANOMALY"); end
        for (g = 551; g <= 557; g = g + 1) begin setup_pade;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), g, 900);
            $display("RES pade+qldi gap=%0d acc=%0d done=%0d commit=%0d intruder_ok=%0d resv=%0d%s", g, n_acc, n_done, n_commit, lane_val(9) == E_QLDI, n_resv,
                     (n_done == 2 && lane_val(9) == E_QLDI && n_commit == 2) ? "" : "  <-- ANOMALY"); end
        $display("== S4d Pade then ROTC/QSUB intruder across result_valid window");
        for (g = 553; g <= 556; g = g + 1) begin setup_pade;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), pack(8'h1C, 8'd6, 8'd1, 16'h0001, 16'h0000), g, 900);
            $display("RES pade+rotc gap=%0d acc=%0d done=%0d commit=%0d rdt=%0d resv=%0d%s", g, n_acc, n_done, n_commit, n_rdt, n_resv, (n_done == 2 && n_commit == 2) ? "" : "  <-- ANOMALY"); end
        for (g = 553; g <= 556; g = g + 1) begin setup_pade;
            run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), pack(8'h1B, 8'd5, 8'd0, 16'h0000, 16'h0001), g, 900);
            $display("RES pade+qsub gap=%0d acc=%0d done=%0d commit=%0d resv=%0d QR5_ok=%0d%s", g, n_acc, n_done, n_commit, n_resv, lane_val(5) == E_QSUB_P, (n_done == 2 && n_commit == 2 && lane_val(5) == E_QSUB_P) ? "" : "  <-- ANOMALY"); end
        // ===== S6 repeated identical =====
        $display("== S6 repeated identical instructions");
        for (g = 1; g <= 3; g = g + 2) begin setup_basic; verbose = 1;
            run2(qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), g, 40); verbose = 0;
            $display("RES qldi x2 gap=%0d acc=%0d done=%0d commit=%0d", g, n_acc, n_done, n_commit); end
        setup_basic; verbose = 1; run2(qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), 20, 60); verbose = 0;
        $display("RES qldi x2 gap=20 acc=%0d done=%0d commit=%0d", n_acc, n_done, n_commit);
        setup_pade; verbose = 1; run2(pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), pack(8'h2A, 8'd4, 8'd0, 16'd0, 16'd0), 700, 1500); verbose = 0;
        $display("RES pade x2 gap=700 acc=%0d done=%0d commit=%0d resv=%0d", n_acc, n_done, n_commit, n_resv);
        // ===== S7 boot not ready =====
        $display("== S7 instruction while not READY (boot_done=1; strobe at c cycles after reset release)");
        for (g = 1; g <= 24; g = g + 3) begin
            logging = 0; rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); clear_counts; logging = 1; rst_n <= 1; k = -1;
            begin : bn integer c; for (c = 0; c < 120; c = c + 1) begin @(posedge clk);
                if (uut.boot_ready && k < 0) k = c;
                inst_valid <= (c == g); inst_word <= qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10); end end
            inst_valid <= 0; @(posedge clk); logging = 0;
            $display("RES boot strobe_at=%0d ready_first_seen=%0d acc=%0d done=%0d QR9_ok=%0d%s", g, k, n_acc, n_done, lane_val(9) == E_QLDI,
                     (n_acc == 0) ? "  <-- strobe lost (no accept, no done, no flag)" : ""); end
        $display("== S7b boot_done held 0 (never READY); strobe; then boot_done raised");
        boot_done = 0; logging = 0; rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); clear_counts; logging = 1; rst_n <= 1;
        repeat (20) @(posedge clk); inst_word <= qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10); inst_valid <= 1; @(posedge clk); inst_valid <= 0;
        repeat (20) @(posedge clk); boot_done = 1; repeat (200) @(posedge clk); logging = 0;
        $display("RES boot_done-late strobe acc=%0d done=%0d QR9_ok=%0d ready=%0d (instruction was not replayed after READY)", n_acc, n_done, lane_val(9) == E_QLDI, uut.boot_ready);
        $finish;
    end
endmodule
