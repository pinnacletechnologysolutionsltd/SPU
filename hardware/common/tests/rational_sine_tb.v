`timescale 1ns/1ps
module rational_sine_tb;
    reg [11:0] addr;
    wire [31:0] dout;

    rational_sine_rom #(.DEPTH(4096)) UUT(.addr(addr), .dout(dout));

    integer i;
    initial begin
        $display("addr\tword_hex\tp16\tq16\tvalue_approx");
        for (i = 0; i < 16; i = i + 1) begin
            addr = i;
            #1; // allow combinational read
            $display("%0d\t%08x\t%0d\t%0d\t%0f", addr, dout, $signed(dout[31:16]), $signed(dout[15:0]), $signed(dout[31:16]) / 32767.0);
        end
        $finish;
    end
endmodule
