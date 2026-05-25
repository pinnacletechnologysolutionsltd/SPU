// SPU-13 Surd Multiplier: Field-Selectable (v3.0)
// Logic: (a1 + b1√k) × (a2 + b2√k)  where k ∈ {3, 5, 15}
// field_sel: 2'b00 = Q(√3), 2'b01 = Q(√5), 2'b10 = Q(√15)
// Objective: Single multiplier for all polyhedral symmetry groups.

module surd_multiplier #(
    parameter WIDTH = 32,
    parameter SHIFT = 16     // 16 for Q16 I/O, 0 for pure integer
)(
    input  wire clk,
    input  wire reset,
    input  wire [1:0] field_sel,               // Q(√k) field selector
    input  wire signed [WIDTH-1:0] a1, b1,    // Operand 1 (Source)
    input  wire signed [WIDTH-1:0] a2, b2,    // Operand 2 (Rotor Constant)
    output reg  signed [WIDTH-1:0] res_a,      // Result Rational
    output reg  signed [WIDTH-1:0] res_b       // Result Surd (√k)
);

    // 1. Parallel Cross-Products
    // We use four 32x32 multipliers to resolve the rotor expansion in one cycle.
    wire signed [63:0] prod_a1a2;
    assign prod_a1a2 = a1 * a2;
    wire signed [63:0] prod_b1b2;
    assign prod_b1b2 = b1 * b2;
    wire signed [63:0] prod_a1b2;
    assign prod_a1b2 = a1 * b2;
    wire signed [63:0] prod_b1a2;
    assign prod_b1a2 = b1 * a2;

    // 2. Field-Selectable Surd Term: k × b1 × b2
    //    k=3:   (x << 1) + x       = 3x    (adder)
    //    k=5:   (x << 2) + x       = 5x    (adder)
    //    k=15:  (x << 4) − x       = 15x   (subtractor)
    // All avoid multipliers — shift-and-add only.
    wire signed [63:0] surd_term_3, surd_term_5, surd_term_15;
    assign surd_term_3  = (prod_b1b2 << 1) + prod_b1b2;
    assign surd_term_5  = (prod_b1b2 << 2) + prod_b1b2;
    assign surd_term_15 = (prod_b1b2 << 4) - prod_b1b2;

    wire signed [63:0] surd_term;
    assign surd_term = (field_sel == 2'b01) ? surd_term_5  :
                       (field_sel == 2'b10) ? surd_term_15 : surd_term_3;

    // 3. Clocked Output Dispatch
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            res_a <= {WIDTH{1'b0}};
            res_b <= {WIDTH{1'b0}};
        end else begin
            res_a <= (prod_a1a2 + surd_term) >>> SHIFT;
            // Result B: ab + ba (normalized)
            res_b <= (prod_a1b2 + prod_b1a2) >>> SHIFT;
        end
    end

endmodule
