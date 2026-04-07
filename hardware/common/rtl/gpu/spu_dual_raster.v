// spu_dual_raster.v — Dual triangle rasterizer with priority blending
// Unit 0 has priority over unit 1 (nearer triangle wins pixel).
// Both units share setup/step signals; each carries independent geometry.
// No framebuffer: output pixel is combinational on each clock.
// CC0 1.0 Universal.

module spu_dual_raster (
    input  wire        clk,
    input  wire        rst_n,

    // Unit 0 setup
    input  wire        setup0,
    input  wire signed [15:0] a0_0,
    input  wire signed [15:0] b0_0,
    input  wire signed [31:0] c0_0,
    input  wire signed [15:0] a1_0,
    input  wire signed [15:0] b1_0,
    input  wire signed [31:0] c1_0,
    input  wire signed [15:0] a2_0,
    input  wire signed [15:0] b2_0,
    input  wire signed [31:0] c2_0,
    input  wire [3:0]  tri_r0, tri_g0, tri_b0,

    // Unit 1 setup
    input  wire        setup1,
    input  wire signed [15:0] a0_1,
    input  wire signed [15:0] b0_1,
    input  wire signed [31:0] c0_1,
    input  wire signed [15:0] a1_1,
    input  wire signed [15:0] b1_1,
    input  wire signed [31:0] c1_1,
    input  wire signed [15:0] a2_1,
    input  wire signed [15:0] b2_1,
    input  wire signed [31:0] c2_1,
    input  wire [3:0]  tri_r1, tri_g1, tri_b1,

    // Shared scan control
    input  wire        step_x,
    input  wire        step_y,
    input  wire signed [15:0] x_span,

    // Output pixel (R4G4B4, background = 0)
    output wire [3:0]  pixel_r,
    output wire [3:0]  pixel_g,
    output wire [3:0]  pixel_b
);

    wire cov0, cov1;
    wire [3:0] r0, g0, b0, r1, g1, b1;

    spu_raster_unit u0 (.clk(clk), .rst_n(rst_n), .setup(setup0),
        .a0(a0_0), .b0(b0_0), .c0(c0_0),
        .a1(a1_0), .b1(b1_0), .c1(c1_0),
        .a2(a2_0), .b2(b2_0), .c2(c2_0),
        .step_x(step_x), .step_y(step_y), .x_span(x_span),
        .tri_r(tri_r0), .tri_g(tri_g0), .tri_b(tri_b0),
        .covered(cov0), .pixel_r(r0), .pixel_g(g0), .pixel_b(b0));

    spu_raster_unit u1 (.clk(clk), .rst_n(rst_n), .setup(setup1),
        .a0(a0_1), .b0(b0_1), .c0(c0_1),
        .a1(a1_1), .b1(b1_1), .c1(c1_1),
        .a2(a2_1), .b2(b2_1), .c2(c2_1),
        .step_x(step_x), .step_y(step_y), .x_span(x_span),
        .tri_r(tri_r1), .tri_g(tri_g1), .tri_b(tri_b1),
        .covered(cov1), .pixel_r(r1), .pixel_g(g1), .pixel_b(b1));

    // Unit 0 wins; unit 1 fills uncovered pixels; background = black
    assign pixel_r = cov0 ? r0 : (cov1 ? r1 : 4'h0);
    assign pixel_g = cov0 ? g0 : (cov1 ? g1 : 4'h0);
    assign pixel_b = cov0 ? b0 : (cov1 ? b1 : 4'h0);

endmodule
