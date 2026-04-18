// Simulation model for gowin_mult18 (simple behavioral multiplier + optional adder)
`ifndef GOWIN_MULT18_V
`define GOWIN_MULT18_V
module gowin_mult18 #(
    parameter DEVICE = "SIM",
    parameter ACCUM = 0
)(
    input wire clk,
    input wire rst_n,
    input wire ce,
    input wire signed [17:0] A,
    input wire signed [17:0] B,
    input wire signed [35:0] C,
    output reg signed [35:0] P
);
    always @(*) begin
        // combinational multiply + optional add
        P = $signed(A) * $signed(B) + C;
    end
endmodule
`endif // GOWIN_MULT18_V
