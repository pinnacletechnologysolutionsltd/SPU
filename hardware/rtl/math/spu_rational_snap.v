// SPU-13 Rational Snap: Cartesian-to-Quadray Bridge (v3.3.64)
// Implementation: Thomson Transformation Matrix.
// Objective: Inject 3D Cartesian coordinates into the 4D Laminar Manifold.
// Logic: Bit-exact ℚ(√3) mapping.

module spu_rational_snap (
    input  wire signed [31:0] x, y, z, // 3D Cartesian Input
    output wire signed [31:0] a, b, c, d // 4D Quadray Output
);

    // Thomson Transformation:
    // a = ( x + y + z + 1) / 2
    // b = (-x - y + z + 1) / 2
    // c = (-x + y - z + 1) / 2
    // d = ( x - y - z + 1) / 2
    
    // We handle the +1 as a rounding/centering bias for the integer grid.
    assign a = ( x + y + z + 32'sd1) >>> 1;
    assign b = (-x - y + z + 32'sd1) >>> 1;
    assign c = (-x + y - z + 32'sd1) >>> 1;
    assign d = ( x - y - z + 32'sd1) >>> 1;

endmodule
