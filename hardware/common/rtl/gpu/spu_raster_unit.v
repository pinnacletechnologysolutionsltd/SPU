// spu_raster_unit.v — Single triangle rasterizer
// Instantiates three edge steppers and produces per-pixel coverage.
// Pixel is covered when all three edges return inside=1.
// No framebuffer; outputs pixel data synchronously with the video scan.
// CC0 1.0 Universal.

module spu_raster_unit (
    clk,
    rst_n,
    setup,
    a0, b0, c0,
    a1, b1, c1,
    a2, b2, c2,
    step_x,
    step_y,
    x_span,
    tri_r,
    tri_g,
    tri_b,
    covered,
    pixel_r,
    pixel_g,
    pixel_b
);

    // Port directions (Verilog-2001/2012 compatible non-ANSI style)
    input  wire        clk;
    input  wire        rst_n;

    // Triangle setup (combinational; must be stable during setup pulse)
    input  wire        setup;

    // Edge 0: A0*x + B0*y + C0 >= 0
    input  wire signed [15:0] a0;
    input  wire signed [15:0] b0;
    input  wire signed [31:0] c0;
    // Edge 1
    input  wire signed [15:0] a1;
    input  wire signed [15:0] b1;
    input  wire signed [31:0] c1;
    // Edge 2
    input  wire signed [15:0] a2;
    input  wire signed [15:0] b2;
    input  wire signed [31:0] c2;

    // Pixel clock advance
    input  wire        step_x;
    input  wire        step_y;
    input  wire signed [15:0] x_span;

    // Flat colour for this triangle (R4G4B4)
    input  wire [3:0]  tri_r;
    input  wire [3:0]  tri_g;
    input  wire [3:0]  tri_b;

    // Output
    output wire        covered;
    output wire [3:0]  pixel_r;
    output wire [3:0]  pixel_g;
    output wire [3:0]  pixel_b;

    wire inside0, inside1, inside2;

    spu_edge_stepper u_e0 (
        clk, rst_n, setup,
        a0, b0, c0,
        step_x, step_y, x_span,
        inside0
    );

    spu_edge_stepper u_e1 (
        clk, rst_n, setup,
        a1, b1, c1,
        step_x, step_y, x_span,
        inside1
    );

    spu_edge_stepper u_e2 (
        clk, rst_n, setup,
        a2, b2, c2,
        step_x, step_y, x_span,
        inside2
    );

    assign covered = inside0 & inside1 & inside2;
    assign pixel_r = covered ? tri_r : 4'h0;
    assign pixel_g = covered ? tri_g : 4'h0;
    assign pixel_b = covered ? tri_b : 4'h0;

endmodule
