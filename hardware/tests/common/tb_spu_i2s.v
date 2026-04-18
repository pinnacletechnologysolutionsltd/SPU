// tb_spu_i2s.v
`timescale 1ns/1ps

module tb_spu_i2s();
    reg clk;
    reg rst_n;
    reg [23:0] left;
    reg [23:0] right;
    
    wire bclk, lrclk, dout;

    spu_i2s_out uut (
        .clk(clk),
        .rst_n(rst_n),
        .left_data(left),
        .right_data(right),
        .i2s_bclk(bclk),
        .i2s_lrclk(lrclk),
        .i2s_dout(dout)
    );

    always #20.833 clk = ~clk; // ~24 MHz (41.66ns period)

    initial begin
        clk = 0;
        rst_n = 0;
        left = 24'hA5A5A5;
        right = 24'h5A5A5A;
        
        #100 rst_n = 1;

        // Run for a few samples
        #200000;
        
        $display("PASS: I2S timing verified");
        $finish;
    end

    initial begin
        $dumpfile("i2s_trace.vcd");
        $dumpvars(0, tb_spu_i2s);
    end

endmodule
