// SPU-13 Rational Trigonometry Core (v3.3.22)
// Implementation: Norman Wildberger's Quadrance and Spread.
// Guard: Symmetry Guard added to decompose unbalanced exponents (e.g., d^3 -> Q*d).
// Objective: Absolute algebraic closure and Laminar symmetry enforcement.

module spu_rational_trig (
    input  wire signed [31:0] a, b, c, d, // Quadray ABCD coordinates
    output wire [63:0] quadrance,         // Q = a^2 + b^2 + c^2 + d^2
    output wire [31:0] spread_60_fixed,   // s = 3/4 (0.75) in 16.16 fixed-point
    
    // Symmetry Guarded Outputs (Laminar Decompositions)
    output wire [95:0] a_cubic_laminar,   // a^3 decomposed as Q_a * a
    output wire [95:0] b_cubic_laminar,
    output wire [95:0] c_cubic_laminar,
    output wire [95:0] d_cubic_laminar
);

    // 1. Bit-Exact Quadrance calculation
    // Q = d^2. Pure integer multiplication.
    wire signed [63:0] q_a = a * a;
    wire signed [63:0] q_b = b * b;
    wire signed [63:0] q_c = c * c;
    wire signed [63:0] q_d = d * d;

    assign quadrance = q_a + q_b + q_c + q_d;

    // 2. The 60-degree Invariant
    // In an IVM lattice, the spread between primary axes is exactly 0.75.
    assign spread_60_fixed = 32'h0000C000;

    // 3. The Symmetry Guard (Lego-to-Laminar)
    // Decompose cubic terms (3D volume) into Quadrance * Linear Vector.
    // This prevents "poking out" by ensuring 3rd-order interactions 
    // remain tied to the 2nd-order metric invariant.
    assign a_cubic_laminar = q_a * a;
    assign b_cubic_laminar = q_b * b;
    assign c_cubic_laminar = q_c * c;
    assign d_cubic_laminar = q_d * d;

endmodule
