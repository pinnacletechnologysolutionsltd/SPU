`timescale 1ns / 1ps
// NUM-SOM-4 Phase B directed probe: RPLU2 numeric-domain guard + atomic refusal indication (core level, H0 configuration).
// Contract: docs/isa/H0_NUMSOM4_B2_COMPLETION_CONTRACT_DRAFT.md. Driver enforces the single-outstanding assumption (LI-7).
// Source lane values are injected through the register file write port (force) because QLDI cannot build them.
// Not a regression-gate testbench (file name avoids 'tb'); run via run_num_som_4_phaseB.py. Exits nonzero ($fatal) on any failed check.
module numsom4b_probe;
    reg clk = 1'b0; always #5 clk = ~clk;
    reg rst_n = 1'b0; reg inst_valid = 1'b0; reg [63:0] inst_word = 64'd0;
    reg cfg_wr_en = 1'b0; reg [2:0] cfg_sel = 3'd0; reg [9:0] cfg_addr = 10'd0; reg [63:0] cfg_data = 64'd0;
    wire inst_done, refused, qr_commit_valid; wire [3:0] qr_commit_lane; wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    spu13_core #(.DEVICE("SIM"), .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1), .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(1), .ENABLE_CORE_RPLU_V2_PIPELINE(1), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0), .SHARE_RPLU_PADE_INV_MULT(1)) uut (
        .clk(clk), .rst_n(rst_n), .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(cfg_wr_en), .dec_fast_cfg_sel(cfg_sel), .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(cfg_addr),
        .dec_fast_cfg_data(cfg_data), .phinary_cfg(16'd0), .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0), .boot_done(1'b1),
        .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0), .mem_ready(1'b1),
        .mem_burst_rd(), .mem_burst_wr(), .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(), .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(), .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane), .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D), .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),
        .rplu2_domain_refused(refused), .ratio_cmp_res(), .ratio_cmp_valid(), .manifold_out(), .bloom_complete(), .scale_table_out(),
        .scale_overflow_out(), .is_janus_point(), .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(), .rplu_dissoc_out(),
        .rplu_dissoc_mask_out(), .rplu_addr_out(), .i2s_bclk(), .i2s_lrclk(), .i2s_dout(), .laminar_flow_index_out(), .thermal_pressure_out(),
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(), .axiomatic_fault(), .fault_type(), .fault_count(), .rns_error(),
        .ecc_single_err(), .ecc_double_err());

    // ---- observers (counted while `logging`) ----
    integer cyc = 0, n_acc = 0, n_done = 0, n_ref = 0, n_commit = 0, n_resv = 0, n_start = 0, n_pend = 0, c_done = -1, c_ref = -1, c_resv = -1, c_start = -1;
    reg logging = 1'b0; reg [143:0] feat_start = 144'd0; reg [255:0] data_start = 256'd0, data_guard = 256'd0; reg [3:0] lane_start = 4'd15, lane_guard = 4'd15;
    always @(posedge clk) if (logging) begin
        cyc = cyc + 1;
        if (uut.inst_accept) n_acc = n_acc + 1;
        if (inst_done) begin n_done = n_done + 1; if (c_done < 0) c_done = cyc; end
        if (refused) begin n_ref = n_ref + 1; if (c_ref < 0) c_ref = cyc; end
        if (qr_commit_valid) n_commit = n_commit + 1;
        if (uut.rplu2_result_valid) begin n_resv = n_resv + 1; if (c_resv < 0) c_resv = cyc; end
        if (uut.gen_rplu_v2.rplu2_som_pending && !uut.gen_rplu_v2.rplu2_busy) begin n_pend = n_pend + 1;
            data_guard = {uut.qrf_rd_A, uut.qrf_rd_B, uut.qrf_rd_C, uut.qrf_rd_D}; lane_guard = uut.rote_src_lane; end
        if (uut.gen_rplu_v2.rplu2_som_start) begin n_start = n_start + 1; if (c_start < 0) c_start = cyc;
            feat_start = uut.rplu2_features; data_start = {uut.qrf_rd_A, uut.qrf_rd_B, uut.qrf_rd_C, uut.qrf_rd_D}; lane_start = uut.rote_src_lane; end
    end
    integer wq;
    task wt_done;  input integer n, lim; begin wq = 0; while (n_done  < n && wq < lim) begin @(posedge clk); wq = wq + 1; end end endtask
    task wt_resv;  input integer n, lim; begin wq = 0; while (n_resv  < n && wq < lim) begin @(posedge clk); wq = wq + 1; end end endtask
    task wt_start; input integer n, lim; begin wq = 0; while (n_start < n && wq < lim) begin @(posedge clk); wq = wq + 1; end end endtask
    task clear_counts; begin cyc = 0; n_acc = 0; n_done = 0; n_ref = 0; n_commit = 0; n_resv = 0; n_start = 0; n_pend = 0;
        c_done = -1; c_ref = -1; c_resv = -1; c_start = -1; lane_start = 4'd15; lane_guard = 4'd15; end endtask

    // ---- helpers ----
    integer fails = 0, checks = 0;
    task chk; input ok; input [255:0] what; begin checks = checks + 1; if (!ok) begin fails = fails + 1; $display("   CHECK FAILED: %0s", what); end end endtask
    function [63:0] w2a; input [3:0] dst, src; w2a = {8'h2A, 4'd0, dst, 4'd0, src, 40'd0}; endfunction
    function [63:0] qldi; input [7:0] lane; input signed [7:0] a, b, c, d; qldi = {8'h1D, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0}; endfunction
    function [63:0] comp; input integer p, q; comp = {q[31:0], p[31:0]}; endfunction   // {Q,P} signed 32-bit halves
    function [35:0] nr; input [63:0] x; nr = {x[32 +: 18], x[0 +: 18]}; endfunction
    function integer bad; input [31:0] v; reg signed [63:0] s; begin s = $signed(v); bad = (s > 9457) || (s < -9457); end endfunction
    function exp_refuse; input [63:0] a, b, c, d;
        exp_refuse = bad(a[31:0]) | bad(a[63:32]) | bad(b[31:0]) | bad(b[63:32]) | bad(c[31:0]) | bad(c[63:32]) | bad(d[31:0]) | bad(d[63:32]); endfunction
    function [63:0] sig; input dummy; integer i; reg [63:0] h; begin h = 64'd0;
        for (i = 0; i < 13; i = i + 1) h = {h[58:0], h[63:59]} ^ uut.gen_qrf.u_qrf.u_regfile.reg_A[i] ^ (uut.gen_qrf.u_qrf.u_regfile.reg_B[i] * 3)
            ^ (uut.gen_qrf.u_qrf.u_regfile.reg_C[i] * 5) ^ (uut.gen_qrf.u_qrf.u_regfile.reg_D[i] * 7);
        sig = h; end endfunction
    task inject; input [3:0] l; input [63:0] a, b, c, d; begin   // write a lane through the register-file write port (ECC parity follows)
        @(negedge clk);
        force uut.gen_qrf.u_qrf.wr_en = 1'b1; force uut.gen_qrf.u_qrf.wr_lane = l;
        force uut.gen_qrf.u_qrf.wr_A = a; force uut.gen_qrf.u_qrf.wr_B = b; force uut.gen_qrf.u_qrf.wr_C = c; force uut.gen_qrf.u_qrf.wr_D = d;
        @(negedge clk);
        release uut.gen_qrf.u_qrf.wr_en; release uut.gen_qrf.u_qrf.wr_lane;
        release uut.gen_qrf.u_qrf.wr_A; release uut.gen_qrf.u_qrf.wr_B; release uut.gen_qrf.u_qrf.wr_C; release uut.gen_qrf.u_qrf.wr_D;
        @(negedge clk); end endtask
    task issue; input [63:0] w; begin @(posedge clk); inst_word <= w; inst_valid <= 1; @(posedge clk); inst_valid <= 0; end endtask
    task cfg_write; input [2:0] sel; input [9:0] addr; input [63:0] data; begin
        @(negedge clk); cfg_sel = sel; cfg_addr = addr; cfg_data = data; cfg_wr_en = 1; @(negedge clk); cfg_wr_en = 0; cfg_sel = 0; cfg_addr = 0; cfg_data = 0; end endtask
    integer g, r;
    task do_reset; begin
        logging = 0; rst_n = 0; inst_valid = 0; repeat (4) @(posedge clk); rst_n <= 1; @(posedge clk);
        g = 0; while (!uut.boot_ready && g < 300) begin @(posedge clk); g = g + 1; end repeat (4) @(posedge clk);
        cfg_write(3'd1, 10'd0, {32'd0, 32'd2}); cfg_write(3'd1, 10'd8, 64'd0);                    // Pade numerator c0 = 2
        for (r = 0; r < 7; r = r + 1) begin cfg_write(3'd3, r, {32'd0, 32'd1}); cfg_write(3'd3, r + 64, 64'd0); end   // every reachable BTU row configured
        cfg_write(3'd6, 10'd0, 64'd3); end endtask
    task wait_term; input integer limit; begin g = 0; while (n_done == 0 && g < limit) begin @(posedge clk); g = g + 1; end repeat (60) @(posedge clk); end endtask

    // ---- one 0x2A case: source lane 3, result label lane 4 ----
    reg [63:0] sig0; reg [319:0] cm0, cm1; reg expr;
    task do_case; input [255:0] name; input [63:0] a, b, c, d; begin
        expr = exp_refuse(a, b, c, d);
        inject(4'd3, a, b, c, d);
        sig0 = sig(0); cm0 = {qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D};
        clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); wait_term(1500); logging = 0;
        cm1 = {qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D};
        if (expr) begin
            chk(n_ref == 1 && n_done == 1 && c_ref == c_done, "refusal exactly once, aligned with inst_done");
            chk(n_start == 0 && n_resv == 0 && n_commit == 0, "no launch, result or commit on refusal");
            chk(cm0 == cm1, "previous commit telemetry unchanged (historical)");
        end else begin
            chk(n_ref == 0 && n_start == 1 && n_resv == 1 && n_commit == 1 && n_done == 1, "valid input: one launch, one result, no refusal");
            chk(feat_start == {nr(d), nr(c), nr(b), nr(a)}, "launched features equal the checked operands (narrowed)");
        end
        chk(n_pend == 1 && lane_guard == 4'd3 && (expr || lane_start == 4'd3), "selected lane stable at guard (and launch)");
        chk(expr || data_guard == data_start, "guard data equals launch data");
        chk(sig0 == sig(0), "no QR register write");
        $display("CASE %0s exp=%0s ref=%0d done=%0d start=%0d resv=%0d commit=%0d pend=%0d", name, expr ? "REFUSE" : "LAUNCH", n_ref, n_done, n_start, n_resv, n_commit, n_pend);
    end endtask


    // ---- sequential, reset and collision scenarios ----
    localparam [63:0] RA = 64'd0;
    reg [63:0] r0, r1, r2, r3, q9a, q9b; integer gp, c, tres;
    task refuse_vec; begin inject(4'd3, comp(9458, 0), comp(0, 0), comp(0, 0), comp(0, 0)); end endtask
    task valid_vec;  begin inject(4'd5, comp(2, 0), comp(0, 0), comp(0, 0), comp(0, 0)); end endtask
    task recover; begin   // after any reset scenario: normal operation must be intact
        do_reset; do_case("recover-refuse", comp(0, -9458), 64'd0, 64'd0, 64'd0); do_case("recover-launch", comp(1, 1), comp(2, 2), comp(3, 3), comp(-4, -4)); end endtask
    task two_strobes; input [63:0] w1, w2; input integer gap, window; begin
        clear_counts; logging = 1;
        for (c = 0; c < window; c = c + 1) begin @(posedge clk); inst_valid <= (c == 0) || (c == gap); inst_word <= (c == 0) ? w1 : w2; end
        @(posedge clk); inst_valid <= 0; logging = 0; end endtask
    task obs; input [255:0] tag; begin
        $display("OBS %0s ref=%0d done=%0d start=%0d resv=%0d commit=%0d acc=%0d last_guard_lane=%0d last_start_lane=%0d", tag, n_ref, n_done, n_start, n_resv, n_commit, n_acc, lane_guard, lane_start); end endtask
    integer pos, vi, k; reg [63:0] z; reg [63:0] va [0:7]; reg [63:0] val; integer v32;
    task case_pos; input [255:0] name; input integer position; input integer value; begin
        va[0] = 0; va[1] = 0; va[2] = 0; va[3] = 0; va[4] = 0; va[5] = 0; va[6] = 0; va[7] = 0;
        // positions: 0=A.P 1=A.Q 2=B.P 3=B.Q 4=C.P 5=C.Q 6=D.P 7=D.Q
        va[position] = value;
        do_case(name, comp(va[0], va[1]), comp(va[2], va[3]), comp(va[4], va[5]), comp(va[6], va[7])); end endtask
    // comp() takes integers; positions carry integer P/Q halves
    initial begin
        do_reset;
        $display("== zero vector"); do_case("zero", 64'd0, 64'd0, 64'd0, 64'd0);
        $display("== boundaries +-9457 (accepted) and +-9458 (refused), each of the eight coefficient positions");
        for (pos = 0; pos < 8; pos = pos + 1) begin
            case_pos("p+9457", pos, 9457); case_pos("p-9457", pos, -9457); case_pos("p+9458", pos, 9458); case_pos("p-9458", pos, -9458); end
        $display("== signed 32-bit extremes");
        for (pos = 0; pos < 8; pos = pos + 1) begin case_pos("pMAX", pos, 32'sh7fffffff); case_pos("pMIN", pos, -32'sh80000000); end
        $display("== pre-narrowing aliases (low 18 bits in range, original value out of domain)");
        for (pos = 0; pos < 8; pos = pos + 1) begin case_pos("alias+", pos, 262149); case_pos("alias-", pos, -262149); end
        $display("== valid mixed-sign operands");
        do_case("mixed1", comp(9457, -9457), comp(-9457, 9457), comp(9457, 9457), comp(-9457, -9457));
        do_case("mixed2", comp(-3, 2), comp(-3, -3), comp(5, 0), comp(-1, 7));
        do_case("mixed3", comp(0, 9457), comp(-9457, 0), comp(1, -1), comp(-1, 1));

        $display("== sequential accepted operations (refuse, launch, refuse) with minimal gaps");
        do_reset; refuse_vec; valid_vec; clear_counts; logging = 1;
        issue(w2a(4'd4, 4'd3)); wt_done(1, 1500);
        issue(w2a(4'd4, 4'd5)); wt_resv(1, 1500); @(posedge clk);
        issue(w2a(4'd4, 4'd3)); wt_done(3, 1500); repeat (60) @(posedge clk); logging = 0;
        chk(n_ref == 2 && n_start == 1 && n_resv == 1 && n_commit == 1 && n_done == 3 && n_pend == 3, "sequence: 2 refusals, 1 launch, 1 result, 3 completions");
        $display("SEQ ref=%0d done=%0d start=%0d resv=%0d commit=%0d pend=%0d", n_ref, n_done, n_start, n_resv, n_commit, n_pend);
        $display("== reset during pending");
        do_reset; refuse_vec; clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); #2 rst_n = 0; repeat (4) @(posedge clk); rst_n <= 1;
        repeat (150) @(posedge clk); logging = 0;
        chk(n_ref == 0 && n_start == 0 && n_done == 0, "reset during pending: no refusal, launch or completion");
        $display("RST pending ref=%0d done=%0d start=%0d", n_ref, n_done, n_start); recover;
        $display("== reset coincident with the guard decision edge (refusing input)");
        refuse_vec; clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); @(posedge clk); rst_n <= 0; repeat (4) @(posedge clk); rst_n <= 1;
        repeat (150) @(posedge clk); logging = 0;
        chk(n_ref == 0 && n_done == 0 && n_start == 0, "reset on guard edge wins: no refusal event");
        $display("RST guard-edge ref=%0d done=%0d start=%0d", n_ref, n_done, n_start); recover;
        $display("== reset during the refusal pulse cycle");
        refuse_vec; clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); @(posedge clk); #3 rst_n = 0; repeat (4) @(posedge clk); rst_n <= 1;
        repeat (150) @(posedge clk); logging = 0;
        chk(n_ref == 0 && n_done == 0 && n_start == 0, "reset in the pulse cycle cancels it; nothing after");
        $display("RST pulse-cycle ref=%0d done=%0d start=%0d", n_ref, n_done, n_start); recover;
        $display("== reset during launch (start cycle) and mid-pipeline");
        for (k = 0; k < 2; k = k + 1) begin
            valid_vec; clear_counts; logging = 1; issue(w2a(4'd4, 4'd5)); wt_start(1, 1500); repeat (k * 200) @(posedge clk); #3 rst_n = 0;
            repeat (4) @(posedge clk); rst_n <= 1; clear_counts; repeat (1500) @(posedge clk); logging = 0;
            chk(n_ref == 0 && n_done == 0 && n_resv == 0 && n_commit == 0, "reset during launch: no result, completion or refusal afterwards");
            $display("RST launch+%0d ref=%0d done=%0d resv=%0d commit=%0d", k * 200, n_ref, n_done, n_resv, n_commit); recover; end
        $display("== previous result remains historical across a refusal");
        do_reset; valid_vec; refuse_vec; clear_counts; logging = 1; issue(w2a(4'd4, 4'd5)); wait_term(1500);
        cm0 = {qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D}; logging = 0;
        clear_counts; logging = 1; issue(w2a(4'd4, 4'd3)); wait_term(200); logging = 0;
        cm1 = {qr_commit_lane, qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D};
        chk(cm0 == cm1 && n_commit == 0 && n_ref == 1, "commit telemetry after refusal equals the previous result and no new commit");
        $display("HIST ref=%0d commit=%0d unchanged=%0d", n_ref, n_commit, cm0 == cm1);
        $display("== OBSERVATIONS (not supported behavior): second instruction while a refusal is pending");
        for (gp = 2; gp <= 5; gp = gp + 1) begin
            do_reset; refuse_vec; q9a = uut.gen_qrf.u_qrf.u_regfile.reg_A[9];
            two_strobes(w2a(4'd4, 4'd3), qldi(8'd9, 8'sd7, 8'sd8, 8'sd9, 8'sd10), gp, 120);
            $display("OBS qldi-after-refusal gap=%0d ref=%0d done=%0d start=%0d qr9_written=%0d", gp, n_ref, n_done, n_start, uut.gen_qrf.u_qrf.u_regfile.reg_A[9] != q9a); end
        $display("== OBSERVATIONS: refusing 0x2A issued while a valid 0x2A is in flight");
        do_reset; refuse_vec; valid_vec; two_strobes(w2a(4'd4, 4'd5), w2a(4'd4, 4'd3), 100, 1500); obs("refuse-during-flight");
        $display("== OBSERVATIONS: refusing 0x2A near the completion cycle of a valid 0x2A");
        do_reset; valid_vec; clear_counts; logging = 1; issue(w2a(4'd4, 4'd5)); wait_term(1500); logging = 0; tres = c_resv; $display("OBS calibration result_cycle=%0d", tres);
        for (gp = -3; gp <= 3; gp = gp + 1) begin
            do_reset; refuse_vec; valid_vec; two_strobes(w2a(4'd4, 4'd5), w2a(4'd4, 4'd3), tres + gp, 1500); $display("OBS offset=%0d", gp); obs("near-completion"); end
        $display("TOTAL checks=%0d fails=%0d", checks, fails);
        if (fails != 0) $fatal(1, "numsom4b_probe: %0d check(s) failed", fails);
        $finish;
    end
    initial begin #1000000; $display("TIMEOUT"); $fatal(1, "timeout"); end
endmodule
