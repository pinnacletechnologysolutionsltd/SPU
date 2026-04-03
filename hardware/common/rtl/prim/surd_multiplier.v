// SPU-13 Surd Multiplier: The Rotor Core (v2.9.23)
// Logic: (a1 + b1*sqrt3) * (a2 + b2*sqrt3)
// Objective: Zero-latency Branch Growth and Forward Lean calculation.

module surd_multiplier #(
    parameter WIDTH = 32
)(
    input  wire clk,
    input  wire reset,
    input  wire signed [WIDTH-1:0] a1, b1, // Operand 1 (Source)
    input  wire signed [WIDTH-1:0] a2, b2, // Operand 2 (Rotor Constant)
    output reg  signed [WIDTH-1:0] res_a,  // Result Rational
    output reg  signed [WIDTH-1:0] res_b   // Result Surd (sqrt3)
);

    // 1. Parallel Cross-Products
    // We use four 32x32 multipliers to resolve the rotor expansion in one cycle.
    wire signed [63:0] prod_a1a2 = a1 * a2;
    wire signed [63:0] prod_b1b2 = b1 * b2;
    wire signed [63:0] prod_a1b2 = a1 * b2;
    wire signed [63:0] prod_b1a2 = b1 * a2;

    // 2. Surd Term Logic (3 * b1 * b2)
    // Shift-Adder: (x << 1) + x
    wire signed [63:0] surd_term = (prod_b1b2 << 1) + prod_b1b2;

    // 3. Clocked Output Dispatch (Laminar Flow)
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            res_a <= {WIDTH{1'b0}};
            res_b <= {WIDTH{1'b0}};
        end else begin
            // Result A: aa + 3bb (normalized by 16-bit shift)
            res_a <= (prod_a1a2 + surd_term) >>> 16;
            
            // Result B: ab + ba (normalized by 16-bit shift)
            res_b <= (prod_a1b2 + prod_b1a2) >>> 16;
        end
    end

endmodule
