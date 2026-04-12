// Rational Sine ROM (P/Q 32-bit per entry packed 64-bit hex)
module rational_sine_rom_q32 #(parameter DEPTH=4096) (
    input wire [$clog2(DEPTH)-1:0] addr,
    output reg signed [31:0] dout_p,
    output reg signed [31:0] dout_q
);
    reg [63:0] rom [0:DEPTH-1];
    initial begin
        $readmemh("hardware/common/rtl/gpu/rational_sine_4096_q32.mem", rom);
    end
    always @(*) begin
        {dout_p, dout_q} = rom[addr];
    end
endmodule
