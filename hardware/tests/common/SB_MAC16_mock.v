`timescale 1ns/1ps

// SB_MAC16 Mock for iverilog Simulation
// Purpose: Provide a behavioral model for the iCE40 DSP primitive.

module SB_MAC16 #(
    parameter NEG_TRIGGER = 1'b0,
    parameter C_REG = 1'b0
)(
    input  wire [15:0] A, B, C, D,
    input  wire        CLK, CE, IRSTTOP, IRSTBOT,
    output reg  [31:0] O
);

    reg [31:0] o_next;

    always @(*) begin
        // Simple 16x16 Multiplication for Quadrance Check
        o_next = $signed(A) * $signed(B);
    end

    // SB_MAC16 has an internal output register (usually)
    always @(posedge CLK) begin
        if (CE) begin
            O <= o_next;
        end
    end

endmodule
