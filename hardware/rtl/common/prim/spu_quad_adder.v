// SPU-13: Asymmetrical Quadray Adder
// v_out = v1 + v2 in the ABCD Manifold

module quad_adder (
    input  wire [23:0] a1, b1, c1, d1, // Vector 1
    input  wire [23:0] a2, b2, c2, d2, // Vector 2
    output wire [23:0] a_out, b_out, c_out, d_out
);

    // Asymmetric Summation: Simple, Fast, Laminar.
    // We add the components, then the SPU-13 "Normalizer"
    // ensures the A+B+C+D=0 Invariant is held.
    assign a_out = a1 + a2;
    assign b_out = b1 + b2;
    assign c_out = c1 + c2;
    assign d_out = d1 + d2;

endmodule
