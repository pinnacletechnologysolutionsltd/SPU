// spu_quad_raster.v — four parallel prepared-scene raster lanes.
// Family A keeps one completed VGA pixel per clk_pixel; depth selection is
// performed by the consumer, not by this coverage-only block.
// CC0 1.0 Universal.

module spu_quad_raster (
    input  wire clk, rst_n,
    input  wire setup0,
    input  wire signed [15:0] a0_0, b0_0, a1_0, b1_0, a2_0, b2_0,
    input  wire signed [31:0] c0_0, c1_0, c2_0,
    input  wire [3:0] tri_r0, tri_g0, tri_b0,
    input  wire setup1,
    input  wire signed [15:0] a0_1, b0_1, a1_1, b1_1, a2_1, b2_1,
    input  wire signed [31:0] c0_1, c1_1, c2_1,
    input  wire [3:0] tri_r1, tri_g1, tri_b1,
    input  wire setup2,
    input  wire signed [15:0] a0_2, b0_2, a1_2, b1_2, a2_2, b2_2,
    input  wire signed [31:0] c0_2, c1_2, c2_2,
    input  wire [3:0] tri_r2, tri_g2, tri_b2,
    input  wire setup3,
    input  wire signed [15:0] a0_3, b0_3, a1_3, b1_3, a2_3, b2_3,
    input  wire signed [31:0] c0_3, c1_3, c2_3,
    input  wire [3:0] tri_r3, tri_g3, tri_b3,
    input  wire step_x, step_y,
    output wire cov0, cov1, cov2, cov3,
    output wire [3:0] r0, g0, b0, r1, g1, b1,
    output wire [3:0] r2, g2, b2, r3, g3, b3
);

    spu_raster_unit u0 (.clk(clk), .rst_n(rst_n), .setup(setup0),
        .a0(a0_0), .b0(b0_0), .c0(c0_0), .a1(a1_0), .b1(b1_0), .c1(c1_0),
        .a2(a2_0), .b2(b2_0), .c2(c2_0), .step_x(step_x), .step_y(step_y),
        .tri_r(tri_r0), .tri_g(tri_g0), .tri_b(tri_b0),
        .covered(cov0), .pixel_r(r0), .pixel_g(g0), .pixel_b(b0));
    spu_raster_unit u1 (.clk(clk), .rst_n(rst_n), .setup(setup1),
        .a0(a0_1), .b0(b0_1), .c0(c0_1), .a1(a1_1), .b1(b1_1), .c1(c1_1),
        .a2(a2_1), .b2(b2_1), .c2(c2_1), .step_x(step_x), .step_y(step_y),
        .tri_r(tri_r1), .tri_g(tri_g1), .tri_b(tri_b1),
        .covered(cov1), .pixel_r(r1), .pixel_g(g1), .pixel_b(b1));
    spu_raster_unit u2 (.clk(clk), .rst_n(rst_n), .setup(setup2),
        .a0(a0_2), .b0(b0_2), .c0(c0_2), .a1(a1_2), .b1(b1_2), .c1(c1_2),
        .a2(a2_2), .b2(b2_2), .c2(c2_2), .step_x(step_x), .step_y(step_y),
        .tri_r(tri_r2), .tri_g(tri_g2), .tri_b(tri_b2),
        .covered(cov2), .pixel_r(r2), .pixel_g(g2), .pixel_b(b2));
    spu_raster_unit u3 (.clk(clk), .rst_n(rst_n), .setup(setup3),
        .a0(a0_3), .b0(b0_3), .c0(c0_3), .a1(a1_3), .b1(b1_3), .c1(c1_3),
        .a2(a2_3), .b2(b2_3), .c2(c2_3), .step_x(step_x), .step_y(step_y),
        .tri_r(tri_r3), .tri_g(tri_g3), .tri_b(tri_b3),
        .covered(cov3), .pixel_r(r3), .pixel_g(g3), .pixel_b(b3));

endmodule
