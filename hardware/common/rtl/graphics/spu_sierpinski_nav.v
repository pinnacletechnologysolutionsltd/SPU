// SPU-13 Sierpiński Navigation (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Fractal Coordinate Mapping for 16-bit space.
// Feature: Bitwise AND-filtering to define the 'Sane' vs 'Void' regions.

module spu_sierpinski_nav (
    input  wire [15:0] coord_x,
    input  wire [15:0] coord_y,
    output wire [1:0]  quadrant_level, // Recursive depth identifier
    output wire        is_in_void      // 1 if in the 'Tuck Zone'
);

    // The Sierpiński Filter: 
    // In fractal space, (x AND y) == 0 defines the filled/sane regions.
    // If (x & y) != 0, we are in the 'Void' - the central inverted triangle.
    assign is_in_void = (coord_x & coord_y) != 16'd0;
    
    // Quadrant mapping based on MSBs
    // State 00: Bottom Left (Past), 01: Bottom Right (Present), 10: Top (Future)
    assign quadrant_level = {coord_y[15], coord_x[15]};

endmodule
