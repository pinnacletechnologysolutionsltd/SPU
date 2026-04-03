// SPU-13 Rational Impressionist Rotor (v2.0)
// Field: Q(sqrt3)
// Logic: Exact Algebraic Basis Rotation (Wildberger's Rational Rotor).
// Transforms (a + b*sqrt3) color vectors via Rational Parameters (t_num, t_den).

module spu_impressionist_rotor (
    input  wire signed [15:0] a_in, b_in,
    input  wire signed [15:0] t_num, t_den, // Rational parameter t = t_num / t_den
    output wire signed [15:0] a_out, b_out
);

    // Rational Rotor Expansion (R = (1-t^2) + 2t*sqrt(3) / (1+3t^2))
    // To maintain integer exactness, we use t_num/t_den
    // Let t = N/D. Then R = (D^2 - N^2) + 2ND*sqrt(3) / (D^2 + 3N^2)
    
    wire signed [31:0] N2 = t_num * t_num;
    wire signed [31:0] D2 = t_den * t_den;
    wire signed [31:0] ND = t_num * t_den;
    
    // Rational Polynomial expansion:
    // a_out = a*(D^2 - N^2) + b*(3 * 2ND)
    // b_out = a*(2ND) + b*(D^2 - N^2)
    // All scaled by (D^2 + 3N^2) which acts as the 'Normalization Field'
    
    wire signed [31:0] norm = D2 + (N2 * 3);
    wire signed [31:0] rot_a = (D2 - N2);
    wire signed [31:0] rot_b = (ND << 1);
    
    // Final Rational Application (with normalization)
    assign a_out = ((a_in * rot_a) + (b_in * rot_b * 3)) / norm;
    assign b_out = ((a_in * rot_b) + (b_in * rot_a)) / norm;

endmodule
