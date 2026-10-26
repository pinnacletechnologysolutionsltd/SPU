// spu13_su3_mult_tb.v — Self-checking testbench for 3×3 A₃₁[i] matrix multiply
//
// Tests:
//   1. Identity × Identity = Identity
//   2. λ₁ × λ₁ = λ₁² = diag(1,1,0)
//   3. Identity × λ₁ = λ₁
//   4. Zero × Identity = Zero
//   5. Dense A₃₁[i] matrix product with all lanes active
//
// Expected values match Python oracle (test_su3_oracle.py).
//
// Run: iverilog -g2012 -I hardware/common/rtl -I hardware/spu13/rtl
//         -I hardware/rtl/core/spu13 -I hardware/rtl/arch
//         -y hardware/rtl/core/spu13
//         -o build/su3_mult_tb.vvp hardware/tests/spu13/spu13_su3_mult_tb.v
//      vvp build/spu13_su3_mult_tb.vvp

`timescale 1ns / 1ps

module spu13_su3_mult_tb;

    reg clk, rst_n, start;
    reg load_a, load_b;
    reg [255:0] elem_data;
    wire [4:0]  elem_idx;
    wire        done, busy;
    wire [255:0] result_data;
    wire        result_valid;
    wire [3:0]  debug_state;

    // External shared multiplier for the refactored SU(3) module
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire        mult_done, mult_busy;
    wire        mult_start;
    wire [31:0] ma0, ma1, ma2, ma3;
    wire [31:0] mb0, mb1, mb2, mb3;

    spu13_m31_multiplier u_mult (
        .clk(clk), .rst_n(rst_n),
        .start(mult_start), .done(mult_done), .busy(mult_busy),
        .a0(ma0), .a1(ma1), .a2(ma2), .a3(ma3),
        .b0(mb0), .b1(mb1), .b2(mb2), .b3(mb3),
        .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
        .rns_error()
    );

    spu13_su3_mult uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .load_a(load_a), .load_b(load_b), .elem_data(elem_data),
        .elem_idx(elem_idx), .done(done), .busy(busy),
        .result_data(result_data), .result_valid(result_valid),
        .debug_state(debug_state),
        .m_start(mult_start),
        .ma0(ma0), .ma1(ma1), .ma2(ma2), .ma3(ma3),
        .mb0(mb0), .mb1(mb1), .mb2(mb2), .mb3(mb3),
        .mr0(mult_r0), .mr1(mult_r1), .mr2(mult_r2), .mr3(mult_r3),
        .m_done(mult_done), .m_busy(mult_busy)
    );

    always #5 clk = ~clk;  // 100 MHz

    // ── Element helpers ────────────────────────────────────────
    function [255:0] elem_one;
        begin elem_one = {128'd0, 96'd0, 32'd1}; end
    endfunction

    function [255:0] elem_zero;
        begin elem_zero = 256'd0; end
    endfunction

    // λ₁: off-diagonal ones
    function [255:0] elem_l1(input [1:0] r, c);
        begin
            if ((r == 0 && c == 1) || (r == 1 && c == 0))
                elem_l1 = elem_one();
            else
                elem_l1 = elem_zero();
        end
    endfunction

    // ── Load tasks ─────────────────────────────────────────────
    task load_elem_a(input [255:0] e);
        @(negedge clk); load_a = 1; elem_data = e;
        @(negedge clk); load_a = 0; elem_data = 256'd0;
    endtask

    task load_elem_b(input [255:0] e);
        @(negedge clk); load_b = 1; elem_data = e;
        @(negedge clk); load_b = 0; elem_data = 256'd0;
    endtask

    function elem_eq(input [255:0] a, b);
        begin elem_eq = (a == b); end
    endfunction

    function [255:0] dense_a_elem(input [1:0] r, c);
        integer idx;
        begin
            idx = r * 3 + c;
            case (idx)
                0: dense_a_elem = 256'h000000190000001700000013000000110000000a000000080000000600000004;
                1: dense_a_elem = 256'h0000002f0000002d00000029000000270000001500000013000000110000000f;
                2: dense_a_elem = 256'h00000045000000430000003f0000003d000000200000001e0000001c0000001a;
                3: dense_a_elem = 256'h00000023000000210000001d0000001b0000000f0000000d0000000b00000009;
                4: dense_a_elem = 256'h000000390000003700000033000000310000001a000000180000001600000014;
                5: dense_a_elem = 256'h0000004f0000004d00000049000000470000002500000023000000210000001f;
                6: dense_a_elem = 256'h0000002d0000002b00000027000000250000001400000012000000100000000e;
                7: dense_a_elem = 256'h00000043000000410000003d0000003b0000001f0000001d0000001b00000019;
                default: dense_a_elem = 256'h000000590000005700000053000000510000002a000000280000002600000024;
            endcase
        end
    endfunction

    function [255:0] dense_b_elem(input [1:0] r, c);
        integer idx;
        begin
            idx = r * 3 + c;
            case (idx)
                0: dense_b_elem = 256'h0000004d0000004b00000047000000450000002400000022000000200000001e;
                1: dense_b_elem = 256'h0000006700000065000000610000005f000000310000002f0000002d0000002b;
                2: dense_b_elem = 256'h000000810000007f0000007b000000790000003e0000003c0000003a00000038;
                3: dense_b_elem = 256'h0000005b0000005900000055000000530000002b000000290000002700000025;
                4: dense_b_elem = 256'h00000075000000730000006f0000006d00000038000000360000003400000032;
                5: dense_b_elem = 256'h0000008f0000008d00000089000000870000004500000043000000410000003f;
                6: dense_b_elem = 256'h0000006900000067000000630000006100000032000000300000002e0000002c;
                7: dense_b_elem = 256'h00000083000000810000007d0000007b0000003f0000003d0000003b00000039;
                default: dense_b_elem = 256'h0000009d0000009b00000097000000950000004c0000004a0000004800000046;
            endcase
        end
    endfunction

    function [255:0] matrix_elem(input integer matrix_id, input [1:0] r, c);
        begin
            if (matrix_id == 0)
                matrix_elem = (r == c) ? elem_one() : elem_zero();
            else if (matrix_id == 1)
                matrix_elem = elem_l1(r, c);
            else if (matrix_id == 3)
                matrix_elem = dense_a_elem(r, c);
            else if (matrix_id == 4)
                matrix_elem = dense_b_elem(r, c);
            else
                matrix_elem = elem_zero();
        end
    endfunction

    // ── Test harness ──────────────────────────────────────────
    integer errors;

    task run_test(input integer tid);
        integer r, c, idx, matrix_a, matrix_b, seen, guard;
        reg [255:0] expected [0:8];
        // Compute expected result
        for (r = 0; r < 9; r = r + 1) expected[r] = 256'd0;
        if (tid == 0) begin  // I × I = I
            matrix_a = 0; matrix_b = 0;
            expected[0] = elem_one(); expected[4] = elem_one(); expected[8] = elem_one();
        end else if (tid == 1) begin  // λ₁² = diag(1,1,0)
            matrix_a = 1; matrix_b = 1;
            expected[0] = elem_one(); expected[4] = elem_one();
        end else if (tid == 2) begin  // I × λ₁ = λ₁
            matrix_a = 0; matrix_b = 1;
            expected[1] = elem_one(); expected[3] = elem_one();
        end else if (tid == 3) begin  // Zero × I = Zero
            matrix_a = 2; matrix_b = 0;
        end else begin  // Dense A₃₁[i] product
            matrix_a = 3; matrix_b = 4;
            expected[0] = 256'h0000a30000014f3000021510000446a07fff6b677ffed36f7ffe271f7ffc43ef;
            expected[1] = 256'h0000d3240001b14c0002ae0400057e047fff41f77ffe7ff37ffda5ef7ffb3fbb;
            expected[2] = 256'h0001034800021368000346f80006b5687fff18877ffe2c777ffd24bf7ffa3b87;
            expected[3] = 256'h0000ca2400019e2c00028dc400053a247fff4bff7ffe94637ffdc7077ffb830b;
            expected[4] = 256'h00010678000218a800034b480006baa87fff196b7ffe2e9f7ffd2a6b7ffa47ff;
            expected[5] = 256'h000142cc00029324000408cc00083b2c7ffee6d77ffdc8db7ffc8dcf7ff90cf3;
            expected[6] = 256'h0000f1480001ed280003067800062da87fff2c977ffe55577ffd66ef7ffac227;
            expected[7] = 256'h000139cc000280040003e88c0007f74c7ffef0df7ffddd4b7ffcaee77ff95043;
            expected[8] = 256'h00018250000312e00004caa00009c0f07ffeb5277ffd653f7ffbf6df7ff7de5f;
        end
        // Load, run, check
        @(negedge clk); start = 1;
        @(negedge clk); start = 0;
        for (r = 0; r < 3; r = r + 1) begin
            for (c = 0; c < 3; c = c + 1) begin
                load_elem_a(matrix_elem(matrix_a, r[1:0], c[1:0]));
            end
        end
        for (r = 0; r < 3; r = r + 1) begin
            for (c = 0; c < 3; c = c + 1) begin
                load_elem_b(matrix_elem(matrix_b, r[1:0], c[1:0]));
            end
        end

        seen = 0;
        guard = 0;
        while (seen < 9 && guard < 2000) begin
            @(posedge clk); #1;
            if (result_valid) begin
                idx = elem_idx;
                if (idx != seen) begin
                    $display("FAIL: test %0d result index expected %0d got %0d", tid, seen, idx);
                    errors = errors + 1;
                end
                if (!elem_eq(result_data, expected[seen])) begin
                    $display("FAIL: test %0d [%0d] expected %h got %h", tid, seen, expected[seen], result_data);
                    errors = errors + 1;
                end
                seen = seen + 1;
            end
            guard = guard + 1;
        end
        if (seen != 9) begin
            $display("FAIL: test %0d timed out after %0d result elements", tid, seen);
            errors = errors + 1;
        end
        if (!done) begin
            $display("FAIL: test %0d did not assert done on final result", tid);
            errors = errors + 1;
        end
    endtask

    task run_named_test(input integer tid);
        begin
            if (tid == 0)
                $display("Test 1: I × I = I");
            else if (tid == 1)
                $display("Test 2: λ₁ × λ₁ = λ₁²");
            else if (tid == 2)
                $display("Test 3: I × λ₁ = λ₁");
            else if (tid == 3)
                $display("Test 4: Zero × I = Zero");
            else
                $display("Test 5: Dense A₃₁[i] matrix product");
            run_test(tid);
        end
    endtask

    initial begin
        $display("=== SU(3) Matrix Multiply Testbench ===");
        errors = 0;
        clk = 0; rst_n = 0;
        start = 0; load_a = 0; load_b = 0; elem_data = 256'd0;
        #15 rst_n = 1;

        run_named_test(0);
        run_named_test(1);
        run_named_test(2);
        run_named_test(3);
        run_named_test(4);

        $display("");
        if (errors == 0) begin
            $display("PASS: spu13_su3_mult_tb — 0 errors");
        end else begin
            $display("FAIL: spu13_su3_mult_tb — %0d error(s)", errors);
        end
        $finish;
    end

endmodule
