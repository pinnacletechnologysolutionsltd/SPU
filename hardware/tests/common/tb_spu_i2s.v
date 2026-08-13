// tb_spu_i2s.v
`timescale 1ns/1ps

module tb_spu_i2s();
    reg clk;
    reg rst_n;
    reg [1:0] mode;
    reg [15:0] lfi;
    reg [23:0] left;
    reg [23:0] right;
    
    wire bclk, lrclk, dout;

    spu_i2s_out uut (
        .clk(clk),
        .rst_n(rst_n),
        .mode(mode),
        .lfi(lfi),
        .left_data(left),
        .right_data(right),
        .i2s_bclk(bclk),
        .i2s_lrclk(lrclk),
        .i2s_dout(dout)
    );

    always #20.833 clk = ~clk; // ~24 MHz (41.66ns period)

    integer bclk_toggles;
    integer lrclk_toggles;
    reg prev_bclk;
    reg prev_lrclk;

    always @(posedge clk) begin
        if (!rst_n) begin
            prev_bclk = bclk;
            prev_lrclk = lrclk;
        end else begin
            if (bclk !== prev_bclk) bclk_toggles = bclk_toggles + 1;
            if (lrclk !== prev_lrclk) lrclk_toggles = lrclk_toggles + 1;
            prev_bclk = bclk;
            prev_lrclk = lrclk;
        end
    end

    initial begin
        clk = 0;
        rst_n = 0;
        mode = 2'b01; // passthrough mode exercises the active serializer
        lfi = 16'hFFFF;
        left = 24'hA5A5A5;
        right = 24'h5A5A5A;
        bclk_toggles = 0;
        lrclk_toggles = 0;
        prev_bclk = 0;
        prev_lrclk = 0;
        
        #100 rst_n = 1;

        // Run for a few samples
        #200000;
        
        if (bclk_toggles < 100 || lrclk_toggles < 2) begin
            $display("FAIL: I2S clocks did not run (bclk=%0d lrclk=%0d)",
                     bclk_toggles, lrclk_toggles);
            $finish(1);
        end else begin
            $display("PASS: I2S timing verified (bclk=%0d lrclk=%0d)",
                     bclk_toggles, lrclk_toggles);
            $finish;
        end
    end

    initial begin
        $dumpfile("i2s_trace.vcd");
        $dumpvars(0, tb_spu_i2s);
    end

endmodule
