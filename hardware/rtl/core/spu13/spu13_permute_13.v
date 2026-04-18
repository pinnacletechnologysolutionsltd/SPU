// SPU-13 Rational Field Permutator (v2.1 - Algebraic Basis Rotation)
// The IVM (Intrinsic Variable Manifold) is a cyclic rotation of the 13-axis basis vectors.
// Permutation is now a basis change in the Rational Manifold, preserving Q(sqrt3) structure.

module spu_permute_13 (
    input  wire [831:0] q_in,  // 13 Lanes x 64-bit (26 RationalSurds)
    output wire [831:0] q_out
);

    // Cyclic 13-Axis Shift (2 Registers per Axis)
    // Permutation is simply an index-map on the Rational Manifold,
    // preserving the RationalSurd (a,b) pairs for each lane.
    
    genvar i;
    generate
        for (i = 0; i < 13; i = i + 1) begin : rotate_lane
            assign q_out[(i*64) +: 64] = q_in[((i+1)%13)*64 +: 64];
        end
    endgenerate

endmodule
