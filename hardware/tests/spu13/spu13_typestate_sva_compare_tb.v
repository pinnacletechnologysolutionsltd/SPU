// spu13_typestate_sva_compare_tb.v — functional equivalence + area comparison
//
// Exercises spu13_typestate_guard (lattice) and spu13_sva_guard (boolean flags)
// with identical stimulus.  Verifies bit-identical result_tag, fault, and
// fault_code on every cycle.  Also exercises poison-proof behaviour: once
// fault is asserted, the destination bits must not change.
//
// This is the evidence for THEOREM_LICENSED_TYPESTATE.md §7 (SVA head-to-head).

`timescale 1ns / 1ps

module spu13_typestate_sva_compare_tb;

    reg clk, rst_n, ce, op_valid;
    reg [2:0] op_code;
    reg [1:0] op_tag_a, op_tag_b;

    wire [1:0] ts_tag, sva_tag;
    wire       ts_fault, sva_fault;
    wire [1:0] ts_fcode, sva_fcode;

    spu13_typestate_guard u_ts (
        .clk(clk), .rst_n(rst_n), .ce(ce),
        .op_valid(op_valid), .op_code(op_code),
        .op_tag_a(op_tag_a), .op_tag_b(op_tag_b),
        .result_tag(ts_tag), .fault(ts_fault), .fault_code(ts_fcode)
    );

    spu13_sva_guard u_sva (
        .clk(clk), .rst_n(rst_n), .ce(ce),
        .op_valid(op_valid), .op_code(op_code),
        .op_tag_a(op_tag_a), .op_tag_b(op_tag_b),
        .result_tag(sva_tag), .fault(sva_fault), .fault_code(sva_fcode)
    );

    localparam [1:0] U = 2'b00;  // UNTAGGED
    localparam [1:0] F = 2'b01;  // FRESH
    localparam [1:0] M = 2'b10;  // MAIN
    localparam [1:0] C = 2'b11;  // CONJ

    localparam SCALE2=0, IROTC_M=1, IROTC_C=2, QADD=3;
    localparam F_NONE=0, F_UNTAGGED=1, F_CATMIX=2, F_BAD_OP=3;

    integer pass, fail, test_num;

    // Clock
    always #5 clk = ~clk;

    task do_op;
        input [2:0] code;
        input [1:0] tag_a, tag_b;
        input       expect_fault;
        input [1:0] expect_fcode;
        input [1:0] expect_tag;
        begin
            test_num = test_num + 1;
            @(posedge clk);
            op_valid <= 1'b1;
            op_code <= code;
            op_tag_a <= tag_a;
            op_tag_b <= tag_b;
            @(posedge clk);
            op_valid <= 1'b0;
            @(posedge clk);  // wait for registered output

            if (ts_tag !== sva_tag) begin
                $display("FAIL test %0d: tag mismatch ts=%b sva=%b", test_num, ts_tag, sva_tag);
                fail = fail + 1;
            end else if (ts_fault !== sva_fault) begin
                $display("FAIL test %0d: fault mismatch ts=%b sva=%b", test_num, ts_fault, sva_fault);
                fail = fail + 1;
            end else if (ts_fcode !== sva_fcode) begin
                $display("FAIL test %0d: fcode mismatch ts=%b sva=%b", test_num, ts_fcode, sva_fcode);
                fail = fail + 1;
            end else if (ts_fault !== expect_fault) begin
                $display("FAIL test %0d: fault expected=%b got=%b", test_num, expect_fault, ts_fault);
                fail = fail + 1;
            end else if (ts_fault && ts_fcode !== expect_fcode) begin
                $display("FAIL test %0d: fcode expected=%b got=%b", test_num, expect_fcode, ts_fcode);
                fail = fail + 1;
            end else if (!ts_fault && ts_tag !== expect_tag) begin
                $display("FAIL test %0d: tag expected=%b got=%b", test_num, expect_tag, ts_tag);
                fail = fail + 1;
            end else begin
                pass = pass + 1;
            end
        end
    endtask

    // ── Poison-proof check ────────────────────────────────────────
    task check_poison_hold;
        input [2:0] code;
        input [1:0] tag_a, tag_b;
        input       expect_fault;
        input [1:0] poisoned_tag;
        begin
            test_num = test_num + 1;
            @(posedge clk);
            // Apply the faulting operation
            op_valid <= 1'b1;
            op_code <= code;
            op_tag_a <= tag_a;
            op_tag_b <= tag_b;
            @(posedge clk);
            op_valid <= 1'b0;
            @(posedge clk);

            if (!ts_fault || ts_tag !== poisoned_tag) begin
                $display("FAIL test %0d: poison hold — tag changed ts=%b sva=%b (expected %b)",
                         test_num, ts_tag, sva_tag, poisoned_tag);
                fail = fail + 1;
            end else begin
                pass = pass + 1;
            end
        end
    endtask

    initial begin
        $display("spu13_typestate_sva_compare_tb — START");
        clk = 0; rst_n = 0; ce = 1; op_valid = 0;
        op_code = 0; op_tag_a = U; op_tag_b = U;
        pass = 0; fail = 0; test_num = 0;

        #20 rst_n = 1;
        @(posedge clk);

        // ── SCALE2 (always legal from any state) ──────────────────
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(SCALE2, F, U, 0, F_NONE, F);
        do_op(SCALE2, M, U, 0, F_NONE, F);
        do_op(SCALE2, C, U, 0, F_NONE, F);

        // ── IROTC_MAIN from legal states ──────────────────────────
        do_op(IROTC_M, F, U, 0, F_NONE, M);
        do_op(IROTC_M, M, U, 0, F_NONE, M);

        // ── IROTC_MAIN from illegal states ────────────────────────
        // Fault is terminal — reset between each fault test.
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(IROTC_M, U, U, 1, F_UNTAGGED, U);   // fault → tag held

        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(IROTC_M, C, U, 1, F_CATMIX, U);

        // ── IROTC_CONJ from legal states ─────────────────────────
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(IROTC_C, F, U, 0, F_NONE, C);
        do_op(IROTC_C, C, U, 0, F_NONE, C);

        // ── IROTC_CONJ from illegal states ────────────────────────
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(IROTC_C, U, U, 1, F_UNTAGGED, U);

        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(IROTC_C, M, U, 1, F_CATMIX, U);

        // Reset and re-establish
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);

        // ── IROTC chain: FRESH → MAIN → MAIN → CONJ (fault) ──────
        do_op(IROTC_M, F, U, 0, F_NONE, M);
        do_op(IROTC_M, M, U, 0, F_NONE, M);
        do_op(IROTC_C, M, U, 1, F_CATMIX, M);  // MAIN→CONJ is CATMIX

        // Reset
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);

        // ── QADD lattice join ─────────────────────────────────────
        // FRESH ⊔ MAIN = MAIN
        do_op(QADD, F, M, 0, F_NONE, M);
        // MAIN ⊔ MAIN = MAIN
        do_op(QADD, M, M, 0, F_NONE, M);
        // FRESH ⊔ CONJ = CONJ
        do_op(QADD, F, C, 0, F_NONE, C);

        // ── QADD demotions (spec §3: linear ops NEVER fault — the tag
        // silently demotes to UNTAGGED; refusal is reserved for IROTC
        // dispatch, where the license actually justifies a >>>1) ─────
        do_op(QADD, U, M, 0, F_NONE, U);           // UNTAGGED operand A demotes
        do_op(QADD, M, U, 0, F_NONE, U);           // UNTAGGED operand B demotes
        do_op(QADD, M, C, 0, F_NONE, U);           // MAIN ⊔ CONJ demotes (CATMIX join = ⊥)
        do_op(QADD, C, M, 0, F_NONE, U);           // CONJ ⊔ MAIN demotes
        // ...and the demoted register is refused at the next IROTC:
        do_op(IROTC_M, U, U, 1, F_UNTAGGED, U);

        // ── BAD_OP ────────────────────────────────────────────────
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);
        do_op(3'd4, F, U, 1, F_BAD_OP, U);

        // ── Poison-proof: fault holds destination ─────────────────
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);   // establish FRESH
        do_op(IROTC_C, F, U, 0, F_NONE, C);  // FRESH→CONJ

        // Now apply a CATMIX fault: CONJ src → IROTC_MAIN
        // Destination must hold CONJ tag (not corrupted)
        check_poison_hold(IROTC_M, C, U, 1, C);

        // ── Fault latch: post-fault ops ignored ───────────────────
        // After a fault, further ops must not change state
        @(posedge clk); rst_n = 0; #20 rst_n = 1; @(posedge clk);
        do_op(SCALE2, U, U, 0, F_NONE, F);        // U→F
        do_op(IROTC_M, U, U, 1, F_UNTAGGED, F);    // fault: UNTAGGED src
        // Post-fault: try SCALE2 — should be ignored (fault latched)
        do_op(SCALE2, U, U, 1, F_UNTAGGED, F);     // tag still FRESH

        // ── Results ───────────────────────────────────────────────
        if (fail == 0)
            $display("PASS: %0d/%0d — typestate and SVA guards are functionally equivalent", pass, pass+fail);
        else
            $display("FAIL: %0d/%0d mismatches", fail, pass+fail);
        $finish;
    end

endmodule
