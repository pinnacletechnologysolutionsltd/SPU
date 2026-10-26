// spu13_rotor_core_tagged_tb.v — Exponent-tagged ROTC testbench
//
// Covers docs/ROTC_EXPONENT_STATE_MACHINE.md §7 acceptance checklist:
//   1. ROTATE normal case
//   2. ROTATE at MAX_EXPONENT boundary → OVERFLOW
//   3. REDUCE success at exact divisibility point (A≡0 mod 3)
//   4. REDUCE failure (INEXACT) — known counterexample (-5 at exp=1)
//   5. ALIGN correctness
//   6. MISALIGNED fault when B/C/D exponents differ

`timescale 1ns/1ps

module spu13_rotor_core_tagged_tb;

    localparam EXP_WIDTH = 4;

    reg         clk = 0;
    reg         rst_n = 0;
    reg         start = 0;
    wire        done;
    reg  [1:0]  op;
    reg  [63:0] A_in, B_in, C_in, D_in;
    reg  [EXP_WIDTH-1:0] exp_ap_in, exp_aq_in;
    reg  [EXP_WIDTH-1:0] exp_bp_in, exp_bq_in;
    reg  [EXP_WIDTH-1:0] exp_cp_in, exp_cq_in;
    reg  [EXP_WIDTH-1:0] exp_dp_in, exp_dq_in;
    reg  [63:0] F, G, H;
    reg  [EXP_WIDTH-1:0] align_target;
    reg  [2:0]  align_lane;
    reg  [2:0]  reduce_lane;
    reg  [5:0]  angle;
    reg         bypass_p5;
    reg         bypass_p5_inv;
    wire [63:0] A_out, B_out, C_out, D_out;
    wire [EXP_WIDTH-1:0] exp_ap_out, exp_aq_out;
    wire [EXP_WIDTH-1:0] exp_bp_out, exp_bq_out;
    wire [EXP_WIDTH-1:0] exp_cp_out, exp_cq_out;
    wire [EXP_WIDTH-1:0] exp_dp_out, exp_dq_out;
    wire [2:0]  fault;
    wire [3:0]  debug_state;

    spu13_rotor_core_tagged #(.EXP_WIDTH(EXP_WIDTH)) u_dut (
        .clk(clk), .rst_n(rst_n), .start(start), .done(done),
        .op(op),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .exp_ap_in(exp_ap_in), .exp_aq_in(exp_aq_in),
        .exp_bp_in(exp_bp_in), .exp_bq_in(exp_bq_in),
        .exp_cp_in(exp_cp_in), .exp_cq_in(exp_cq_in),
        .exp_dp_in(exp_dp_in), .exp_dq_in(exp_dq_in),
        .F(F), .G(G), .H(H),
        .align_target(align_target), .align_lane(align_lane),
        .reduce_lane(reduce_lane),
        .angle(angle),
        .bypass_p5(bypass_p5), .bypass_p5_inv(bypass_p5_inv),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .exp_ap_out(exp_ap_out), .exp_aq_out(exp_aq_out),
        .exp_bp_out(exp_bp_out), .exp_bq_out(exp_bq_out),
        .exp_cp_out(exp_cp_out), .exp_cq_out(exp_cq_out),
        .exp_dp_out(exp_dp_out), .exp_dq_out(exp_dq_out),
        .fault(fault), .debug_state(debug_state)
    );

    always #5 clk = ~clk;

    integer fail = 0;
    integer test_n = 0;

    function [63:0] pack_surd;
        input signed [31:0] p, q;
        begin pack_surd = {p, q}; end
    endfunction

    function [63:0] pack_coeff;
        input signed [31:0] c;
        begin pack_coeff = {32'd0, c}; end
    endfunction

    // Independent oracle for Test 9 — deliberately NOT shared with the
    // DUT's own pow3()/magic3() tables, so a bug in the DUT's table
    // can't accidentally cancel out against the same bug in the check.
    function signed [31:0] pow3_oracle;
        input [3:0] e;
        begin
            case (e)
                4'd1:  pow3_oracle = 3;
                4'd2:  pow3_oracle = 9;
                4'd3:  pow3_oracle = 27;
                4'd4:  pow3_oracle = 81;
                4'd5:  pow3_oracle = 243;
                4'd6:  pow3_oracle = 729;
                4'd7:  pow3_oracle = 2187;
                4'd8:  pow3_oracle = 6561;
                4'd9:  pow3_oracle = 19683;
                4'd10: pow3_oracle = 59049;
                4'd11: pow3_oracle = 177147;
                4'd12: pow3_oracle = 531441;
                4'd13: pow3_oracle = 1594323;
                4'd14: pow3_oracle = 4782969;
                4'd15: pow3_oracle = 14348907;
                default: pow3_oracle = 1;
            endcase
        end
    endfunction

    task set_all_exponents;
        input [EXP_WIDTH-1:0] e;
        begin
            exp_ap_in = e; exp_aq_in = e;
            exp_bp_in = e; exp_bq_in = e;
            exp_cp_in = e; exp_cq_in = e;
            exp_dp_in = e; exp_dq_in = e;
        end
    endtask

    task run_op;
        input [1:0] opcode;
        begin
            op = opcode;
            @(posedge clk);
            start = 1;
            @(posedge clk);
            start = 0;
            wait(done);
            @(posedge clk);
        end
    endtask

    task check_lane;
        input [127:0] tag;
        input signed [31:0] exp_p, exp_q;
        input signed [31:0] got_p, got_q;
        begin
            if (got_p !== exp_p) begin
                $display("FAIL: %0s P-lane: got=%d exp=%d", tag, got_p, exp_p);
                fail = fail + 1;
            end
            if (got_q !== exp_q) begin
                $display("FAIL: %0s Q-lane: got=%d exp=%d", tag, got_q, exp_q);
                fail = fail + 1;
            end
        end
    endtask

    task check_exp;
        input [127:0] tag;
        input [EXP_WIDTH-1:0] exp_val;
        input [EXP_WIDTH-1:0] got_val;
        begin
            if (got_val !== exp_val) begin
                $display("FAIL: %0s exp: got=%d exp=%d", tag, got_val, exp_val);
                fail = fail + 1;
            end
        end
    endtask

    task check_no_fault;
        input [127:0] tag;
        begin
            if (fault !== 3'b0) begin
                $display("FAIL: %0s unexpected fault=%b", tag, fault);
                fail = fail + 1;
            end
        end
    endtask

    task check_fault;
        input [127:0] tag;
        input [2:0] exp_fault;
        begin
            if (fault !== exp_fault) begin
                $display("FAIL: %0s fault got=%b exp=%b", tag, fault, exp_fault);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        rst_n = 0; start = 0; op = 0;
        bypass_p5 = 0; bypass_p5_inv = 0;
        A_in = 0; B_in = 0; C_in = 0; D_in = 0;
        F = 0; G = 0; H = 0;
        align_target = 0; align_lane = 0; reduce_lane = 0;
        set_all_exponents(0);
        #20 rst_n = 1;
        #20;

        // ── Test 1: ROTATE(angle=1) normal ─────────────────────────
        // A=(1,0), B=(1,0), C=(1,0), D=(-3,0), all exp=0
        // F=2, G=2, H=-1
        // B' = 2*1 + (-1)*1 + 2*(-3) = 2-1-6 = -5
        // C' = 2*1 + 2*1 + (-1)*(-3) = 2+2+3 = 7
        // D' = (-1)*1 + 2*1 + 2*(-3) = -1+2-6 = -5
        $display("── Test 1: ROTATE angle=1 normal ──");
        test_n = test_n + 1;
        A_in = pack_surd(1, 0);
        B_in = pack_surd(1, 0);
        C_in = pack_surd(1, 0);
        D_in = pack_surd(-3, 0);
        set_all_exponents(0);
        F = pack_coeff(2);
        G = pack_coeff(2);
        H = pack_coeff(-1);
        run_op(2'b00);
        check_no_fault("T1");
        check_lane("T1 A", 1, 0, A_out[63:32], A_out[31:0]);
        check_lane("T1 B", -5, 0, B_out[63:32], B_out[31:0]);
        check_lane("T1 C", 7, 0, C_out[63:32], C_out[31:0]);
        check_lane("T1 D", -5, 0, D_out[63:32], D_out[31:0]);
        check_exp("T1 A_P", 0, exp_ap_out);
        check_exp("T1 B_P", 1, exp_bp_out);
        check_exp("T1 C_P", 1, exp_cp_out);
        check_exp("T1 D_P", 1, exp_dp_out);

        // ── Test 2: ROTATE(angle=4) ────────────────────────────────
        // F=2, G=-1, H=2
        // A=(2,0), B=(3,0), C=(5,0), D=(7,0)
        // B' = 2*3 + 2*5 + (-1)*7 = 6+10-7 = 9
        // C' = (-1)*3 + 2*5 + 2*7 = -3+10+14 = 21
        // D' = 2*3 + (-1)*5 + 2*7 = 6-5+14 = 15
        $display("── Test 2: ROTATE angle=4 ──");
        test_n = test_n + 1;
        A_in = pack_surd(2, 0);
        B_in = pack_surd(3, 0);
        C_in = pack_surd(5, 0);
        D_in = pack_surd(7, 0);
        set_all_exponents(0);
        F = pack_coeff(2);
        G = pack_coeff(-1);
        H = pack_coeff(2);
        run_op(2'b00);
        check_no_fault("T2");
        check_lane("T2 A", 2, 0, A_out[63:32], A_out[31:0]);
        check_lane("T2 B", 9, 0, B_out[63:32], B_out[31:0]);
        check_lane("T2 C", 21, 0, C_out[63:32], C_out[31:0]);
        check_lane("T2 D", 15, 0, D_out[63:32], D_out[31:0]);

        // ── Test 3: REDUCE inexact — counterexample ────────────────
        // B = -5 at exp=1. -5 % 3 ≠ 0 → INEXACT
        $display("── Test 3: REDUCE INEXACT ──");
        test_n = test_n + 1;
        A_in = pack_surd(1, 0);
        B_in = pack_surd(-5, 0);
        C_in = pack_surd(7, 0);
        D_in = pack_surd(-5, 0);
        exp_ap_in = 0; exp_aq_in = 0;
        exp_bp_in = 1; exp_bq_in = 1;
        exp_cp_in = 1; exp_cq_in = 1;
        exp_dp_in = 1; exp_dq_in = 1;
        reduce_lane = 3'd2;  // BP
        run_op(2'b10);
        check_fault("T3", 3'b100);  // INEXACT
        check_lane("T3 B unchanged", -5, 0, B_out[63:32], B_out[31:0]);

        // ── Test 4: REDUCE success (A≡0 mod 3) ─────────────────────
        // B=18 at exp=1. 18/3 = 6 exact. REDUCE should set exp=0.
        $display("── Test 4: REDUCE success ──");
        test_n = test_n + 1;
        A_in = pack_surd(0, 0);
        B_in = pack_surd(18, 0);
        C_in = pack_surd(0, 0);
        D_in = pack_surd(0, 0);
        exp_ap_in = 0; exp_aq_in = 0;
        exp_bp_in = 1; exp_bq_in = 1;
        exp_cp_in = 1; exp_cq_in = 1;
        exp_dp_in = 1; exp_dq_in = 1;
        reduce_lane = 3'd2;  // BP
        run_op(2'b10);
        check_no_fault("T4");
        check_lane("T4 B reduced", 6, 0, B_out[63:32], B_out[31:0]);
        check_exp("T4 B_P exp", 0, exp_bp_out);

        // ── Test 5: ALIGN ─────────────────────────────────────────
        // B_P = 5 at exp=0. ALIGN to exp=2 → 5*9 = 45
        $display("── Test 5: ALIGN ──");
        test_n = test_n + 1;
        A_in = pack_surd(0, 0);
        B_in = pack_surd(5, 0);
        C_in = pack_surd(0, 0);
        D_in = pack_surd(0, 0);
        set_all_exponents(0);
        align_target = 4'd2;
        align_lane = 3'd2;  // BP
        run_op(2'b01);
        check_no_fault("T5");
        check_lane("T5 B aligned", 45, 0, B_out[63:32], B_out[31:0]);
        check_exp("T5 B_P exp", 2, exp_bp_out);

        // ── Test 6: MISALIGNED ────────────────────────────────────
        // B at exp=0, C at exp=1 → MISALIGNED
        $display("── Test 6: MISALIGNED ──");
        test_n = test_n + 1;
        A_in = pack_surd(0, 0);
        B_in = pack_surd(1, 0);
        C_in = pack_surd(1, 0);
        D_in = pack_surd(1, 0);
        exp_ap_in = 0; exp_aq_in = 0;
        exp_bp_in = 0; exp_bq_in = 0;  // B at 0
        exp_cp_in = 1; exp_cq_in = 1;  // C at 1 — MISMATCH!
        exp_dp_in = 0; exp_dq_in = 0;
        F = pack_coeff(2); G = pack_coeff(2); H = pack_coeff(-1);
        run_op(2'b00);
        check_fault("T6", 3'b001);  // MISALIGNED

        // ── Test 7: OVERFLOW ──────────────────────────────────────
        // All exp=15. ROTATE would push to 16 → OVERFLOW
        $display("── Test 7: OVERFLOW ──");
        test_n = test_n + 1;
        A_in = pack_surd(0, 0);
        B_in = pack_surd(1, 0);
        C_in = pack_surd(1, 0);
        D_in = pack_surd(1, 0);
        set_all_exponents(4'd15);
        F = pack_coeff(2); G = pack_coeff(2); H = pack_coeff(-1);
        run_op(2'b00);
        check_fault("T7", 3'b010);  // OVERFLOW

        // ── Test 8: REDUCE success on a negative value ─────────────
        // B=-9 at exp=1. -9/3 = -3 exactly — must succeed, no fault.
        // Regression test for a real bug: reduce_val64 was loaded via
        // zero-extension instead of sign-extension, so every negative
        // lane value reduced as if it were the huge positive number
        // 2^32+value, either missing a real exact division (this case)
        // or spuriously faulting INEXACT. Test 3 alone didn't catch it
        // because -5's zero-extended residue is *also* nonzero mod 3 —
        // a coincidence that masked the bug for that specific value.
        $display("── Test 8: REDUCE success on negative value ──");
        test_n = test_n + 1;
        A_in = pack_surd(0, 0);
        B_in = pack_surd(-9, 0);
        C_in = pack_surd(0, 0);
        D_in = pack_surd(0, 0);
        exp_ap_in = 0; exp_aq_in = 0;
        exp_bp_in = 1; exp_bq_in = 1;
        exp_cp_in = 1; exp_cq_in = 1;
        exp_dp_in = 1; exp_dq_in = 1;
        reduce_lane = 3'd2;  // BP
        run_op(2'b10);
        check_no_fault("T8");
        check_lane("T8 B reduced", -3, 0, B_out[63:32], B_out[31:0]);
        check_exp("T8 B_P exp", 0, exp_bp_out);

        // ── Test 9: REDUCE randomized marathon ─────────────────────
        // Cross-checks the DUT's division-free magic-multiply REDUCE
        // against an independent testbench-side oracle computed with
        // ordinary Verilog '/' and '%' — fine here since this is
        // verification code, not the synthesizable hot path the
        // project's no-division rule actually governs. 2000 random
        // (value, exponent) pairs over the full signed 32-bit range
        // and all 15 REDUCE exponents.
        $display("── Test 9: REDUCE randomized marathon ──");
        begin : marathon
            integer seed;
            integer m;
            integer rk_wide;
            reg signed [31:0] rn;
            reg [3:0] rk;
            reg signed [31:0] rd_oracle;
            reg oracle_exact;
            seed = 32'hC0FFEE;
            for (m = 0; m < 2000; m = m + 1) begin
                rn = $random(seed);
                rk_wide = $random(seed) % 15;         // -14..14
                if (rk_wide < 0) rk_wide = -rk_wide;   // 0..14
                rk = rk_wide[3:0] + 4'd1;              // 1..15

                A_in = pack_surd(0, 0);
                B_in = pack_surd(rn, 0);
                C_in = pack_surd(0, 0);
                D_in = pack_surd(0, 0);
                exp_ap_in = 0; exp_aq_in = 0;
                exp_bp_in = rk; exp_bq_in = rk;
                exp_cp_in = 0; exp_cq_in = 0;
                exp_dp_in = 0; exp_dq_in = 0;
                reduce_lane = 3'd2;  // BP

                oracle_exact = (rn % pow3_oracle(rk)) == 0;
                rd_oracle = rn / pow3_oracle(rk);

                run_op(2'b10);

                if (oracle_exact) begin
                    if (fault !== 3'b000) begin
                        $display("FAIL: T9[%0d] n=%0d k=%0d expected exact, got fault=%b",
                            m, rn, rk, fault);
                        fail = fail + 1;
                    end else if ($signed(B_out[63:32]) !== rd_oracle) begin
                        $display("FAIL: T9[%0d] n=%0d k=%0d got=%0d exp=%0d",
                            m, rn, rk, $signed(B_out[63:32]), rd_oracle);
                        fail = fail + 1;
                    end
                end else begin
                    if (fault !== 3'b100) begin
                        $display("FAIL: T9[%0d] n=%0d k=%0d expected INEXACT, got fault=%b",
                            m, rn, rk, fault);
                        fail = fail + 1;
                    end
                end
            end
        end
        test_n = test_n + 1;
        $display("    (2000 randomized REDUCE cases checked)");

        // ── Report ───────────────────────────────────────────────────
        if (fail == 0)
            $display("\nPASS (%0d tests)", test_n);
        else
            $display("\nFAIL (%0d failures in %0d tests)", fail, test_n);
        $finish;
    end

endmodule
