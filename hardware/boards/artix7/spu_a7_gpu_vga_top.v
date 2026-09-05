// spu_a7_gpu_vga_top.v — Wukong Artix-7 spin: the real rasterizer on the
// proven VGA display path. One static triangle, no host link.
//
// Why this exists. hardware_evidence.md §3.8 established the VGA path in
// silicon (640x480@60, 0.006% timing error, colour bars on a monitor) using
// spu_video_pattern. This spin swaps the test pattern for spu_gpu_top's
// actual coverage rasterizer and changes nothing else about the display
// path: same clocking, same reset conditioning, same hal_vga, same
// three-resistor DAC on J10, same spu_a7_vga_fix.xdc mapping.
//
// The triangle is hardcoded. There is deliberately no host interface here:
// if the shape appears, the rasterizer works on silicon; if it does not, the
// fault is in the GPU and not in a link that would otherwise have to be
// debugged at the same time.
//
// spu_gpu_top is built with ENABLE_HDMI=0 -- openXC7's placer hangs on
// differential output (upstream issue #66) -- and DEVICE="A7".
//
// CC0 1.0 Universal.

module spu_a7_gpu_vga_top (
    input  wire        sys_clk,      // M21, 50 MHz
    input  wire        rst_n,        // H7, active low, board PULLUP
    output wire        vga_r,        // 1 bit per channel through 3 resistors
    output wire        vga_g,
    output wire        vga_b,
    output wire        vga_hsync,
    output wire        vga_vsync
);

    // ── Reset conditioning ───────────────────────────────────────────────
    // Identical to spu_a7_vga_top. rst_n (H7) has no external pull-down;
    // feeding it straight into async resets left this board dead for three
    // weeks (hardware_evidence.md §3.2m). Debounce before use.
    reg [15:0] db_cnt   = 16'd0;
    reg        rst_n_db = 1'b0;
    always @(posedge sys_clk) begin
        if (rst_n == rst_n_db)      db_cnt <= 16'd0;
        else if (&db_cnt) begin     rst_n_db <= rst_n; db_cnt <= 16'd0; end
        else                        db_cnt <= db_cnt + 16'd1;
    end

    // ── Pixel clock: 50 MHz / 2 = 25 MHz, exactly. No MMCM. ──────────────
    reg clk_div = 1'b0;
    always @(posedge sys_clk) clk_div <= ~clk_div;

    wire clk_pixel;
    BUFG u_bufg_pix (.I(clk_div), .O(clk_pixel));

    reg [2:0] pix_rst_sync = 3'b000;
    always @(posedge clk_pixel) pix_rst_sync <= {pix_rst_sync[1:0], rst_n_db};
    wire pix_rst_n = pix_rst_sync[2];

    // ── Frame-start pulse for triangle setup ─────────────────────────────
    // REQUIRED, not an optimisation. spu_gpu_top derives step_y from the
    // horizontal wrap alone, so step_y fires on all 525 lines of the frame
    // while only 480 are active. The edge accumulators are anchored to (0,0)
    // by `setup` and never re-anchored, so a triangle set up once drifts by
    // 45*B per frame and leaves the screen within a few frames. Re-pulsing
    // setup at (0,0) every frame re-anchors it.
    //
    // This second spu_video_timing instance exists only to see (x,y): it is
    // a pure counter on the same clock and reset as the one inside
    // spu_gpu_top, so the two stay in lockstep by construction. Cheaper than
    // widening spu_gpu_top's port list for a bring-up spin.
    wire [9:0] tx, ty;
    wire t_hsync, t_vsync, t_active;
    spu_video_timing u_tick (
        .clk(clk_pixel), .rst_n(pix_rst_n),
        .x(tx), .y(ty), .hsync(t_hsync), .vsync(t_vsync), .active(t_active));

    // setup coincides with (0,0). In spu_edge_stepper `setup` takes priority
    // over step_y, so f loads C -- the value for (0,0) -- on exactly the
    // cycle the counters read (0,0).
    wire frame_start = (tx == 10'd0) && (ty == 10'd0);

    // ── The triangle ─────────────────────────────────────────────────────
    // Vertices, screen coordinates, y down:
    //     V0 (320, 100)   V1 (150, 380)   V2 (490, 380)
    // Edge function for V_i -> V_j, inside when >= 0:
    //     A = yj - yi        B = -(xj - xi)        C = -(A*xi + B*yi)
    // Each edge evaluates to +95200 at the opposite vertex, so the winding
    // is consistent and all three half-planes agree on the interior.
    localparam signed [15:0] E0_A = 16'sd280,  E0_B = 16'sd170;
    localparam signed [31:0] E0_C = -32'sd106600;   // V0 -> V1
    localparam signed [15:0] E1_A = 16'sd0,    E1_B = -16'sd340;
    localparam signed [31:0] E1_C = 32'sd129200;    // V1 -> V2
    localparam signed [15:0] E2_A = -16'sd280, E2_B = 16'sd170;
    localparam signed [31:0] E2_C = 32'sd72600;     // V2 -> V0

    // ── GPU ──────────────────────────────────────────────────────────────
    wire [3:0] gr, gg, gb;
    wire g_hsync, g_vsync;

    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0)) u_gpu (
        .clk_pixel(clk_pixel),
        .clk_tmds (clk_pixel),   // unused with ENABLE_HDMI=0
        .rst_n    (pix_rst_n),

        .tri0_setup(frame_start),
        .tri0_a0(E0_A), .tri0_b0(E0_B), .tri0_c0(E0_C),
        .tri0_a1(E1_A), .tri0_b1(E1_B), .tri0_c1(E1_C),
        .tri0_a2(E2_A), .tri0_b2(E2_B), .tri0_c2(E2_C),
        .tri0_r(4'hF), .tri0_g(4'h0), .tri0_b(4'h0),   // red on black
        .tri0_z0(16'd1000), .tri0_z1(16'd1000), .tri0_z2(16'd1000),

        // Unit 1 unused. cov1=0 makes spu_depth_compare select unit 0
        // whenever it is covered, regardless of depth, so unit 1 being
        // never set up cannot affect what is displayed.
        .tri1_setup(1'b0),
        .tri1_a0(16'sd0), .tri1_b0(16'sd0), .tri1_c0(32'sd0),
        .tri1_a1(16'sd0), .tri1_b1(16'sd0), .tri1_c1(32'sd0),
        .tri1_a2(16'sd0), .tri1_b2(16'sd0), .tri1_c2(32'sd0),
        .tri1_r(4'h0), .tri1_g(4'h0), .tri1_b(4'h0),
        .tri1_z0(16'd0), .tri1_z1(16'd0), .tri1_z2(16'd0),

        .vga_r(gr), .vga_g(gg), .vga_b(gb),
        .vga_hsync(g_hsync), .vga_vsync(g_vsync),

        .tmds_clk_p(), .tmds_clk_n(), .tmds_d_p(), .tmds_d_n());

    // ── Output ───────────────────────────────────────────────────────────
    // spu_gpu_top already delays sync to match its colour pipeline and
    // already blanks through hal_vga, so only the MSB of each channel is
    // brought out, exactly as in the proven §3.8 spin.
    assign vga_r     = gr[3];
    assign vga_g     = gg[3];
    assign vga_b     = gb[3];
    assign vga_hsync = g_hsync;
    assign vga_vsync = g_vsync;

endmodule
