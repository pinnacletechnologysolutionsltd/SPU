// SPU-13 Rational Field Barycentric Rasterizer (v1.0)
// Field: Q(sqrt3)
// Logic: Exact Affine Mapping via Triple-Quad Areas
// This module determines if a pixel (px, py) is inside a triangle (A, B, C)
// using only integer polynomial operations.

module spu_affine_raster (
    input  wire signed [15:0] ax, ay, // Vertex A
    input  wire signed [15:0] bx, by, // Vertex B
    input  wire signed [15:0] cx, cy, // Vertex C
    input  wire signed [15:0] px, py, // Pixel P
    output wire               is_inside
);

    // Algebraic Area Calculation (Triple Quad Formula)
    // Area(ABC) = (Ax(By-Cy) + Bx(Cy-Ay) + Cx(Ay-By))
    wire signed [31:0] area2;
    assign area2 = (ax * (by - cy)) + (bx * (cy - ay)) + (cx * (ay - by));
    
    // Barycentric Weight Calculation
    // w = Weight * Area
    wire signed [31:0] w1;
    assign w1 = (px * (by - cy)) + (bx * (cy - py)) + (cx * (py - by));
    wire signed [31:0] w2;
    assign w2 = (ax * (py - cy)) + (px * (cy - ay)) + (cx * (ay - py));
    wire signed [31:0] w3;
    assign w3 = area2 - w1 - w2;
    
    // Inside if all weights have the same sign (Laminar logic)
    // If area2 > 0, weights must be positive. If area2 < 0, negative.
    // We handle this using a sign-consistent check.
    assign is_inside = (area2 > 0) ? (w1 >= 0 && w2 >= 0 && w3 >= 0) : 
                                    (w1 <= 0 && w2 <= 0 && w3 <= 0);

endmodule