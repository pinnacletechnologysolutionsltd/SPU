// Rational Sine ROM - 4096 entries of 32-bit Q(\"\\u221A3\") surd-encoded words
// Upper 16 bits: signed P (Q15), Lower 16 bits: signed Q (Q15). Q field currently zero.
module rational_sine_rom #(parameter DEPTH=4096) (
    input wire [$clog2(DEPTH)-1:0] addr,
    output reg [31:0] dout
);
    reg [31:0] rom [0:DEPTH-1];
    initial begin
        $readmemh("hardware/common/rtl/gpu/rational_sine_4096.mem", rom);
    end
    always @(*) dout = rom[addr];
endmodule
