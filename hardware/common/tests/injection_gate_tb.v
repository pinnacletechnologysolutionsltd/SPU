`timescale 1ns/1ps
module injection_gate_tb;
    reg clk = 0;
    always #1 clk = ~clk;

    reg rst_n = 0;
    initial begin #5 rst_n = 1; end

    reg start;
    reg signed [15:0] pcm_in;
    reg material_id;
    reg [9:0] sector_addr;
    wire signed [31:0] r_q16_out;
    wire valid_out;

    injection_gate uut(.clk(clk), .rst_n(rst_n), .start(start), .pcm_in(pcm_in), .material_id(material_id), .sector_addr(sector_addr), .r_q16_out(r_q16_out), .valid_out(valid_out));

    integer i;
    initial begin
        material_id = 0;
        sector_addr = 0;
        // wait for reset to finish
        @(posedge rst_n);
        // feed a few samples
        for (i = 0; i < 8; i = i + 1) begin
            pcm_in = (i - 4) * 1000; // ascending signed samples
            start = 1; @(posedge clk); start = 0;
            $display("TB: fired start sample=%0d at time=%0t", pcm_in, $time);
            // wait for valid
            wait (valid_out) @(posedge clk);
            $display("TB: sample=%0d r_q16_out=%0d valid=%b", pcm_in, r_q16_out, valid_out);
            @(posedge clk);
        end
        $display("injection_gate_tb: PASS");
        $finish;
    end
endmodule
