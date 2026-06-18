// Minimal simulation stubs for Gowin primitives (iverilog only).
// Not for synthesis — provides behavioral equivalents for Verilog simulation.

module MULT27X36 (
    output [62:0] DOUT,
    input  [26:0] A,
    input  [35:0] B,
    input  [25:0] D,
    input  [1:0]  CLK,
    input  [1:0]  CE,
    input  [1:0]  RESET,
    input         PSEL,
    input         PADDSUB
);
    // Behavioral: A * B + D (simplified, ignores CE/RESET for sim)
    assign DOUT = A * B;
endmodule

module SDPB #(
    parameter BIT_WIDTH_0 = 16,
    parameter BIT_WIDTH_1 = 16
) (
    input  CLKA, CEA, RESETA,
    input  [13:0] ADA,
    input  [BIT_WIDTH_0-1:0] DIA,
    input  CLKB, CEB, RESETB,
    input  [13:0] ADB,
    output [BIT_WIDTH_1-1:0] DOB
);
    reg [BIT_WIDTH_0-1:0] mem [0:16383];
    always @(posedge CLKA) if (CEA) mem[ADA] <= DIA;
    assign DOB = mem[ADB];
endmodule
