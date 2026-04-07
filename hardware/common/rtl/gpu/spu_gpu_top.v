// spu_gpu_top.v — GPU subsystem top for Tang Primer 25K
// Combines: video timing, dual rasterizer, Bresenham Killer, VGA + HDMI HAL.
// Pixel clock = 25 MHz (clk_pixel).  TMDS clock = 250 MHz (clk_tmds).
// No framebuffer: pixels stream out synchronously with display timing.
// CC0 1.0 Universal.

module spu_gpu_top (
    input  wire        clk_pixel,    // 25 MHz
    input  wire        clk_tmds,     // 250 MHz
    input  wire        rst_n,

    // Triangle 0 interface (from SPU-13 / CPU)
    input  wire        tri0_setup,
    input  wire signed [15:0] tri0_a0,
    input  wire signed [15:0] tri0_b0,
    input  wire signed [31:0] tri0_c0,
    input  wire signed [15:0] tri0_a1,
    input  wire signed [15:0] tri0_b1,
    input  wire signed [31:0] tri0_c1,
    input  wire signed [15:0] tri0_a2,
    input  wire signed [15:0] tri0_b2,
    input  wire signed [31:0] tri0_c2,
    input  wire [3:0]  tri0_r, tri0_g, tri0_b,

    // Triangle 1 interface
    input  wire        tri1_setup,
    input  wire signed [15:0] tri1_a0,
    input  wire signed [15:0] tri1_b0,
    input  wire signed [31:0] tri1_c0,
    input  wire signed [15:0] tri1_a1,
    input  wire signed [15:0] tri1_b1,
    input  wire signed [31:0] tri1_c1,
    input  wire signed [15:0] tri1_a2,
    input  wire signed [15:0] tri1_b2,
    input  wire signed [31:0] tri1_c2,
    input  wire [3:0]  tri1_r, tri1_g, tri1_b,

    // VGA PMOD outputs
    output wire [3:0]  vga_r, vga_g, vga_b,
    output wire        vga_hsync, vga_vsync,

    // HDMI differential outputs
    output wire        tmds_clk_p, tmds_clk_n,
    output wire [2:0]  tmds_d_p, tmds_d_n
);

    // ── Video timing ─────────────────────────────────────────────────────
    wire [9:0] vx, vy;
    wire hsync, vsync, active;
    wire step_x = active;
    wire step_y;  // one cycle after hsync falling (end of line)

    spu_video_timing u_timing (.clk(clk_pixel), .rst_n(rst_n),
        .x(vx), .y(vy), .hsync(hsync), .vsync(vsync), .active(active));

    // step_y when x wraps (start of each new visible row)
    reg [9:0] vx_d;
    always @(posedge clk_pixel) vx_d <= vx;
    assign step_y = (vx == 10'd0) && (vx_d != 10'd0);

    // ── Dual rasterizer ──────────────────────────────────────────────────
    wire [3:0] rast_r, rast_g, rast_b;

    spu_dual_raster u_rast (.clk(clk_pixel), .rst_n(rst_n),
        .setup0(tri0_setup),
        .a0_0(tri0_a0), .b0_0(tri0_b0), .c0_0(tri0_c0),
        .a1_0(tri0_a1), .b1_0(tri0_b1), .c1_0(tri0_c1),
        .a2_0(tri0_a2), .b2_0(tri0_b2), .c2_0(tri0_c2),
        .tri_r0(tri0_r), .tri_g0(tri0_g), .tri_b0(tri0_b),
        .setup1(tri1_setup),
        .a0_1(tri1_a0), .b0_1(tri1_b0), .c0_1(tri1_c0),
        .a1_1(tri1_a1), .b1_1(tri1_b1), .c1_1(tri1_c1),
        .a2_1(tri1_a2), .b2_1(tri1_b2), .c2_1(tri1_c2),
        .tri_r1(tri1_r), .tri_g1(tri1_g), .tri_b1(tri1_b),
        .step_x(step_x), .step_y(step_y), .x_span(10'd640),
        .pixel_r(rast_r), .pixel_g(rast_g), .pixel_b(rast_b));

    // ── HAL_VGA ──────────────────────────────────────────────────────────
    HAL_VGA u_vga (.r(rast_r), .g(rast_g), .b(rast_b),
        .hsync(hsync), .vsync(vsync), .active(active),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync));

    // ── HAL_HDMI ─────────────────────────────────────────────────────────
    HAL_HDMI u_hdmi (.clk_pixel(clk_pixel), .clk_tmds(clk_tmds), .rst_n(rst_n),
        .r({rast_r, 4'h0}), .g({rast_g, 4'h0}), .b({rast_b, 4'h0}),
        .hsync(hsync), .vsync(vsync), .active(active),
        .tmds_clk_p(tmds_clk_p), .tmds_clk_n(tmds_clk_n),
        .tmds_d_p(tmds_d_p), .tmds_d_n(tmds_d_n));

endmodule
