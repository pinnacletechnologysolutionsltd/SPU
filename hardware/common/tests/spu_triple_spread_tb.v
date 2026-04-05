// spu_triple_spread_tb.v — Testbench: spu_triple_spread v1.0
// Vectors from C++ spu_wildberger_test.cpp and Python verification.
//
// IVM equilateral: s1=s2=s3=3/4 → numerators (3,3,3), d=4
//   d·(9)²=4×81=324, 2d·(9+9+9)+4×27=216+108=324 ✓
// Glass-air optical: s1=3/4, s2=1/4, s3=4/4=1 → numerators (3,1,4), d=4
//   d·(8)²=4×64=256, 2d·(9+1+16)+4×12=208+48=256 ✓
// Invalid: numerators (3,3,4), d=4
//   d·(10)²=400, 2d·(9+9+16)+4×36=272+144=416 ≠ 400 → invalid
// Degenerate flat: (4,0,4), d=4
//   d·(8)²=256, 2d·(16+0+16)+4×0=256 ✓

`timescale 1ns/1ps

module spu_triple_spread_tb;

    reg  [15:0] s1_n, s2_n, s3_n, d;
    wire        valid;

    spu_triple_spread u_dut (
        .s1_n(s1_n), .s2_n(s2_n), .s3_n(s3_n), .d(d),
        .valid(valid)
    );

    integer fail = 0;

    task check1;
        input        got;
        input        exp;
        input [127:0] name;
        begin
            if (got !== exp) begin
                $display("FAIL: %0s  got=%0b  exp=%0b", name, got, exp);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        // T1: IVM equilateral — s=3/4 for all three
        s1_n=3; s2_n=3; s3_n=3; d=4; #10;
        check1(valid, 1'b1, "T1 equilateral IVM (3,3,3)/4");

        // T2: Glass-air optical — s=(3/4, 1/4, 1)
        s1_n=3; s2_n=1; s3_n=4; d=4; #10;
        check1(valid, 1'b1, "T2 glass-air (3,1,4)/4");

        // T3: Invalid combination — (3,3,4)/4
        s1_n=3; s2_n=3; s3_n=4; d=4; #10;
        check1(valid, 1'b0, "T3 invalid (3,3,4)/4");

        // T4: Degenerate flat — s3=0 (flat surface, no refraction)
        s1_n=4; s2_n=0; s3_n=4; d=4; #10;
        check1(valid, 1'b1, "T4 degenerate flat (4,0,4)/4");

        // T5: All zero (trivial)
        s1_n=0; s2_n=0; s3_n=0; d=4; #10;
        check1(valid, 1'b1, "T5 all zero");

        // T6: Unit denominator — s1=1/1, s2=0/1, s3=1/1
        // (1+0+1)²=4, 2(1+0+1)=4, +4×0=0 → 4==4 ✓
        s1_n=1; s2_n=0; s3_n=1; d=1; #10;
        check1(valid, 1'b1, "T6 unit denom (1,0,1)/1");

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

endmodule
