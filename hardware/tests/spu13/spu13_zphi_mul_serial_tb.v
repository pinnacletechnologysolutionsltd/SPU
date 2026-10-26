`timescale 1ns/1ps

module spu13_zphi_mul_serial_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;
    reg start = 0;
    reg signed [71:0] xa, xb;
    reg signed [33:0] ya, yb;
    wire busy, done;
    wire signed [107:0] out_a, out_b;
    integer errors = 0;

    spu13_zphi_mul_serial dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .xa(xa), .xb(xb), .ya(ya), .yb(yb),
        .busy(busy), .done(done), .out_a(out_a), .out_b(out_b)
    );

    task check_product;
        input signed [71:0] in_xa, in_xb;
        input signed [33:0] in_ya, in_yb;
        input signed [107:0] expect_a, expect_b;
        input [255:0] label;
        integer cycles;
        begin
            xa = in_xa; xb = in_xb; ya = in_ya; yb = in_yb;
            start = 1'b1;
            @(posedge clk); #1;
            start = 1'b0;
            cycles = 0;
            while (!done && cycles < 10) begin
                @(posedge clk); #1;
                cycles = cycles + 1;
            end
            if (!done || busy || cycles != 4 ||
                out_a !== expect_a || out_b !== expect_b) begin
                errors = errors + 1;
                $display("FAIL %0s cycles=%0d busy=%b done=%b got=(%0d,%0d) want=(%0d,%0d)",
                         label, cycles, busy, done, out_a, out_b,
                         expect_a, expect_b);
            end else begin
                $display("PASS %0s", label);
            end
            @(posedge clk); #1;
        end
    endtask

    initial begin
        xa = 0; xb = 0; ya = 0; yb = 0;
        repeat (3) @(posedge clk);
        rst_n = 1;

        check_product(2, 3, 5, 7, 31, 50, "positive coefficients");
        check_product(-2, 3, 5, -7, -31, 8, "mixed signed coefficients");
        check_product(0, 1, 0, 1, 1, 1, "phi squared identity");
        check_product(100000, -200000, -30000, 40000,
                      -11000000000, 2000000000, "wide exact coefficients");

        if (errors == 0)
            $display("SPU13_ZPHI_MUL_SERIAL_TB: PASS");
        else
            $display("SPU13_ZPHI_MUL_SERIAL_TB: FAIL errors=%0d", errors);
        $finish(errors != 0);
    end
endmodule
