// Simulation stub for gowin_mult18 used by davis_gate_dsp.v
`ifndef GOWIN_MULT18_V
`define GOWIN_MULT18_V
module gowin_mult18 #(parameter DEVICE = "SIM", parameter ACCUM = 0) (
    input wire clk, input wire rst_n, input wire ce,
    input wire signed [17:0] A, input wire signed [17:0] B, input wire signed [35:0] C,
    output reg signed [35:0] P
);
    always @(*) begin
        P = A * B;
    end
endmodule
`endif // GOWIN_MULT18_V
