// spu_quadrance_adder_tb.v — Exact Quadrance Adder Testbench
//
// Tests the Pythagorean property: for integer surds representing
// IVM distances, the hypotenuse quadrance is the exact sum.
//
// Test cases:
//   1. Basic: (a=1,b=0) + (a=1,b=0) → Q₃ = 1²+1² − 3(0+0) = 2
//   2. Surd:  (a=2,b=1) + (a=2,b=1) → Q₃ = 4+4 − 3(1+1) = 8−6 = 2
//   3. Zero:  (a=0,b=0) + (a=3,b=0) → Q₃ = 0+9 − 3(0+0) = 9
//   4. Pell:  (a=7,b=4) + (a=7,b=4) → Q₃ = 49+49 − 3(16+16) = 98−96 = 2
//   5. Right: (a=1,b=0) + (a=2,b=0) → Q₃ = 1+4 = 5 (IVM right triangle)

`timescale 1ns / 1ps

module spu_quadrance_adder_tb;

    reg         clk;
    reg         rst_n;
    reg         valid_in;
    reg  [15:0] a1, b1, a2, b2;
    wire [31:0] Q3;
    wire        valid_out;

    spu_quadrance_adder uut (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
        .a1(a1), .b1(b1), .a2(a2), .b2(b2),
        .Q3(Q3), .valid_out(valid_out)
    );

    always #5 clk = ~clk;  // 100 MHz

    integer pass, fail, i;

    task run_test;
        input [15:0] ta1, tb1, ta2, tb2;
        input [31:0] expected;
        input [255:0] name;
        begin
            a1 = ta1; b1 = tb1; a2 = ta2; b2 = tb2;
            valid_in = 1;
            @(posedge clk);
            valid_in = 0;

            // Wait for 3-stage pipeline
            repeat (4) @(posedge clk);

            if (Q3 == expected) begin
                $display("  PASS: %0s -> Q3=%0d", name, Q3);
                pass = pass + 1;
            end else begin
                $display("  FAIL: %0s → Q3=%0d (expected %0d)", name, Q3, expected);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; valid_in = 0;
        pass = 0; fail = 0;
        a1 = 0; b1 = 0; a2 = 0; b2 = 0;

        @(posedge clk); rst_n = 1;
        @(posedge clk);

        $display("\n── Exact Quadrance Adder Tests ──");

        // Test 1: Integer basis vectors
        run_test(16'd1, 16'd0, 16'd1, 16'd0, 32'd2,
                 "IVM: (1,0)+(1,0) = 2");
        run_test(16'd0, 16'd0, 16'd3, 16'd0, 32'd9,
                 "IVM: (0,0)+(3,0) = 9");

        // Test 2: Surd values — Pell rotor entries
        run_test(16'd2, 16'd1, 16'd2, 16'd1, 32'd2,
                 "Pell: (2,1)+(2,1) = 2");
        run_test(16'd7, 16'd4, 16'd7, 16'd4, 32'd2,
                 "Pell: (7,4)+(7,4) = 2");
        run_test(16'd26, 16'd15, 16'd26, 16'd15, 32'd2,
                 "Pell: (26,15)+(26,15) = 2");

        // Test 3: Pythagorean — right triangle hypotenuse
        run_test(16'd1, 16'd0, 16'd2, 16'd0, 32'd5,
                 "Right: Q1=1 Q2=4 → Q3=5");
        run_test(16'd3, 16'd0, 16'd4, 16'd0, 32'd25,
                 "Right: Q1=9 Q2=16 → Q3=25");

        // Test 4: Conjugate — (2,-1) has norm 4-3=1, (2,1) norm 4-3=1
        run_test(16'd2, -16'd1, 16'd2, 16'd1, 32'd2,
                 "Conj: (2,-1)+(2,1) = 2");

        // Test 5: Davis Gate — (1,1) has norm 1-3=-2, sum = -4
        run_test(16'd1, 16'd1, 16'd1, 16'd1, -32'd4,
                 "Gate: (1,1)+(1,1) = -4");

        // Test 6: Large Pell step
        run_test(16'd97, 16'd56, 16'd97, 16'd56, 32'd2,
                 "Large: r^4 + r^4 = 2");

        repeat (2) @(posedge clk);

        $display("\n──────────────────────────────");
        $display("Results: %0d passed, %0d failed", pass, fail);

        if (fail == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
