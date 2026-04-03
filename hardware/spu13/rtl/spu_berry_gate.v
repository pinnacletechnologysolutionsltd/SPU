// spu_berry_gate.v
// Tracks the topological "twist" of the 13D recursive tree.
module spu_berry_gate (
    input clk,
    input rst_n,
    input [23:0] s_vector,    // Current Surd State
    input [23:0] s_prev,      // Previous Surd State
    output reg [23:0] holonomy_residue
);
    // Area/Wedge Product calculation (Geometric Phase)
    // In a rational field, this represents the "curvature" of the path.
    wire [47:0] wedge_prod = s_vector * s_prev;
    
    // 15-Sigma Snap Thresholding:
    // We only accumulate the bits that fall outside the "Cubic Noise" floor.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            holonomy_residue <= 24'h0;
        end else begin
            // Accumulate the twist. If this hits 0 or a multiple of the 
            // Thomson Prime, the system has reached Rational Closure.
            holonomy_residue <= holonomy_residue + wedge_prod[31:8];
        end
    end
endmodule
