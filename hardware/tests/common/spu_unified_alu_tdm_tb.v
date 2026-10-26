// spu_unified_alu_tdm_tb.v — ROT opcode testbench
// Verifies Q(√3) rotation via TDM ALU + vault interface signals.
//
// Test cases (all in Q12, 1.0 = 0x1000):
//   1. OP_NOP: A_out = A_in unchanged
//   2. OP_ROT: identity rotor (1,0) → output = input
//   3. OP_ROT: r=(2,1) applied to q=(1,0) → q'=(2,1)  [r^0 × r^1 = r^1]
//   4. OP_ROT: r=(2,1) applied to q=(2,1) → q'=(7,4)  [r^1 × r^1 = r^2]
//   5. OP_ROT: r=(7,4) applied to q=(7,4) → q'=(97,56) [r^2 × r^2 = r^4]
//      NOTE: r^4=(97,56) — Ra=97*0x1000=397312 overflows int16, so Q12 result
//      will be the lower 16-bit truncated value (verified via Python reference).
//   6. rot_en pulses exactly once per ROT start, de-asserts after 1 cycle
//   7. OP_ADD: A_out=A+C, B_out=B+D

`timescale 1ns/1ps
`include "spu_unified_alu_tdm.v"

module spu_unified_alu_tdm_tb;

    reg  clk, reset;
    reg  start;
    reg  [2:0]  opcode;
    reg  [31:0] A_in, B_in, C_in, D_in;
    reg  [31:0] F_rat, F_surd;
    reg  [3:0]  rot_axis_in;
    wire        rot_en;
    wire [3:0]  rot_axis_out;
    wire [31:0] A_out, B_out;
    wire        done;
    wire        davis_violation, is_dissonant;

    integer fail = 0;

    spu_unified_alu_tdm #(.DEVICE("SIM")) uut (
        .clk(clk), .reset(reset),
        .start(start), .opcode(opcode),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F_rat(F_rat), .F_surd(F_surd),
        .G_rat(32'h0), .G_surd(32'h0), .H_rat(32'h0), .H_surd(32'h0),
        .rot_axis_in(rot_axis_in),
        .rot_en(rot_en), .rot_axis_out(rot_axis_out),
        .adaptive_tau_q(32'hFFFF_FFFF),
        .sync_alert(1'b0), .rst_n(1'b1),
        .operand_A(32'h0), .operand_B(32'h0),
        .A_out(A_out), .B_out(B_out),
        .done(done), .davis_violation(davis_violation),
        .is_dissonant(is_dissonant)
    );

    always #5 clk = ~clk;

    // Issue one instruction and wait for done
    task run_op;
        input [2:0] op;
        input [31:0] a, b, c, d, fr, fs;
        input [3:0]  axis;
        begin
            @(negedge clk);
            opcode = op; A_in = a; B_in = b; C_in = c; D_in = d;
            F_rat = fr; F_surd = fs; rot_axis_in = axis;
            start = 1;
            @(posedge clk); #1;
            start = 0;
            // Wait for done
            repeat(20) begin
                if (done) disable run_op;
                @(posedge clk); #1;
            end
        end
    endtask

    // Check A_out[15:0] = exp_p, B_out[15:0] = exp_q (Q12 format)
    task check_rot;
        input [127:0] label;
        input [15:0] exp_p, exp_q;
        begin
            if (A_out[15:0] !== exp_p || B_out[15:0] !== exp_q) begin
                $display("FAIL [%0s]: got P=%0d Q=%0d, expected P=%0d Q=%0d",
                    label, A_out[15:0], B_out[15:0], exp_p, exp_q);
                fail = fail + 1;
            end
        end
    endtask

    // Q12 scale: integer × 0x1000
    `define Q12(n) (16'(n) << 12)

    integer rot_en_count;
    integer i;

    initial begin
        clk = 0; reset = 1; start = 0;
        opcode = 0; A_in = 0; B_in = 0; C_in = 0; D_in = 0;
        F_rat = 0; F_surd = 0; rot_axis_in = 0;
        #12; reset = 0;

        // ── Case 1: OP_NOP ───────────────────────────────────────────────
        run_op(3'b000, 32'hDEAD_BEEF, 0, 0, 0, 0, 0, 4'd0);
        if (A_out !== 32'hDEAD_BEEF) begin
            $display("FAIL NOP: A_out=%08h", A_out);
            fail = fail + 1;
        end

        // ── Case 2: OP_ROT with identity rotor (1,0) → output = input ───
        // Ra = Q12(1) = 0x1000, Rb = 0
        // A_in = Q12(2) = 0x2000, B_in = Q12(1) = 0x1000
        // A' = 0x2000*0x1000 - 3*0x1000*0 = 0x2000_0000 → [27:12] = 0x2000
        // B' = 0x2000*0      + 0x1000*0x1000 = 0x1000_0000 → [27:12] = 0x1000
        run_op(3'b001, {16'h0, 16'h2000}, {16'h0, 16'h1000}, 0, 0,
               {16'h0, 16'h1000}, {16'h0, 16'h0000}, 4'd0);
        check_rot("identity", 16'h2000, 16'h1000);

        // ── Case 3: OP_ROT r=(2,1) on q=(1,0) → q'=(2,1) ───────────────
        // A=Q12(1)=0x1000, B=0; Ra=Q12(2)=0x2000, Rb=Q12(1)=0x1000
        // A' = 0x1000*0x2000 - 3*0*0x1000 = 0x2000_000 → [27:12] = 0x2000
        // B' = 0x1000*0x1000 + 0*0x2000   = 0x100_0000 → [27:12] = 0x1000
        run_op(3'b001, {16'h0, 16'h1000}, {16'h0, 16'h0000}, 0, 0,
               {16'h0, 16'h2000}, {16'h0, 16'h1000}, 4'd1);
        check_rot("r1_on_r0", 16'h2000, 16'h1000);

        // ── Case 4: OP_ROT r=(2,1) on q=(2,1) → q'=(7,4) ───────────────
        // A' = 2*2 + 3*1*1 = 4+3 = 7  → Q12(7) = 0x7000
        // B' = 2*1 + 1*2   = 2+2 = 4  → Q12(4) = 0x4000
        run_op(3'b001, {16'h0, 16'h2000}, {16'h0, 16'h1000}, 0, 0,
               {16'h0, 16'h2000}, {16'h0, 16'h1000}, 4'd2);
        check_rot("r1_on_r1", 16'h7000, 16'h4000);

        // ── Case 5: OP_ROT r=(7,4) on q=(7,4) → step4 overflow check ───────
        // A' = 7*7 + 3*4*4 = 49+48 = 97  → Q12 97*4096=0x61000
        //   0x7000*0x7000 = 0x31000000; 3*0x4000*0x4000 = 0x30000000
        //   nA = 0x31000000 + 0x30000000 = 0x61000000 → [27:12] = 0x1000
        //   (bit 30,29 outside [27:12] window; only bit 24 contributes → 0x1000)
        // B' = 7*4 + 4*7 = 56 → Q12: 0x7000*0x4000+0x4000*0x7000 = 0x38000000
        //   [27:12] of 0x38000000: bit27=1 → 0x8000
        // Both the P and Q values exceed Q12 range (>7.999); [27:12] wraps.
        // This test documents the overflow/wrap behaviour for Pell steps ≥3.
        run_op(3'b001, {16'h0, 16'h7000}, {16'h0, 16'h4000}, 0, 0,
               {16'h0, 16'h7000}, {16'h0, 16'h4000}, 4'd0);
        begin : step4_check
            if (A_out[15:0] !== 16'h1000 || B_out[15:0] !== 16'h8000) begin
                $display("FAIL step4_arith: got P=0x%04h Q=0x%04h, expected P=0x1000 Q=0x8000",
                    A_out[15:0], B_out[15:0]);
                fail = fail + 1;
            end
        end

        // ── Case 6: rot_en pulses exactly once per OP_ROT ────────────────
        rot_en_count = 0;
        @(negedge clk);
        opcode = 3'b001; A_in = {16'h0, 16'h1000}; B_in = 0;
        F_rat = {16'h0, 16'h1000}; F_surd = 0; rot_axis_in = 4'd5;
        start = 1;
        @(posedge clk); #1;
        start = 0;
        // Monitor rot_en for 20 cycles
        for (i = 0; i < 20; i = i + 1) begin
            if (rot_en) rot_en_count = rot_en_count + 1;
            @(posedge clk); #1;
        end
        if (rot_en_count !== 1) begin
            $display("FAIL rot_en_count: fired %0d times, expected 1", rot_en_count);
            fail = fail + 1;
        end

        // ── Case 7: OP_ADD ───────────────────────────────────────────────
        run_op(3'b010, 32'h0000_0003, 32'h0000_0005,
               32'h0000_0004, 32'h0000_0002, 0, 0, 4'd0);
        if (A_out !== 32'h7 || B_out !== 32'h7) begin
            $display("FAIL ADD: A_out=%0d B_out=%0d, expected 7 7", A_out, B_out);
            fail = fail + 1;
        end

        // ── Summary ──────────────────────────────────────────────────────
        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL: %0d error(s)", fail);
        $finish;
    end

endmodule
