`timescale 1ns/1ps
module simple_lau_tb;
    reg clk = 0; always #1 clk = ~clk;
    reg rst_n = 0; initial begin #5 rst_n = 1; end

    reg start;
    reg signed [15:0] pcm_in;
    wire signed [31:0] vout_q16;
    wire valid_out;

    simple_lau uut(.clk(clk), .rst_n(rst_n), .start(start), .pcm_in(pcm_in), .vout_q16(vout_q16), .valid_out(valid_out));

    integer i;
    initial begin
        // wait for reset
        @(posedge rst_n);
        // feed a few PCM samples
        for (i = 0; i < 12; i = i + 1) begin
            pcm_in = (i - 6) * 4000; // sample values spanning negative..positive
            start = 1; @(posedge clk); start = 0;
            // wait for valid
            wait (valid_out) @(posedge clk);
            $display("TB: pcm=%0d idx=%0d vout=%0d", pcm_in, (pcm_in >>> 6) + 10'd512, vout_q16);
            @(posedge clk);
        end
        $display("simple_lau_tb: PASS");
        $finish;
    end
endmodule
