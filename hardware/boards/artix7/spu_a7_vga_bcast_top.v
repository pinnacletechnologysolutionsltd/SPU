// spu_a7_vga_top.v — Wukong Artix-7 640x480@60 VGA test-pattern spin.
//
// Exists because openXC7's nextpnr-xilinx cannot place differential outputs
// (OBUFDS/TMDS_33) -- upstream issue #66, open and unimplemented -- so the
// DVI spin (spu_a7_video_top.v) hangs in the placer. VGA is entirely
// single-ended LVCMOS33, needs no OSERDESE2, and needs no MMCM at all:
// 640x480@60 wants a 25 MHz pixel clock and the board oscillator is exactly
// 50 MHz, so a divide-by-two suffices.
//
// Output is analog VGA through three external resistors on connector J10.
// See spu_a7_vga.xdc for wiring and resistor values.
// CC0 1.0 Universal.

module spu_a7_vga_bcast_top (
    input  wire        sys_clk,      // M21, 50 MHz
    input  wire        rst_n,        // H7, active low, board PULLUP
    output wire        vga_r,        // 1 bit per channel: 8 colours
    output wire        vga_g,
    output wire        vga_b,
    output wire        vga_hsync,
    output wire [3:0]  vga_vsync
);

    // ── Reset conditioning ───────────────────────────────────────────────
    // rst_n (H7) has no external pull-down; feeding it straight into async
    // resets left this board dead in silicon for three weeks
    // (hardware_evidence.md 3.2m). Debounce before use.
    reg [15:0] db_cnt   = 16'd0;
    reg        rst_n_db = 1'b0;
    always @(posedge sys_clk) begin
        if (rst_n == rst_n_db)      db_cnt <= 16'd0;
        else if (&db_cnt) begin     rst_n_db <= rst_n; db_cnt <= 16'd0; end
        else                        db_cnt <= db_cnt + 16'd1;
    end

    // ── Pixel clock: 50 MHz / 2 = 25 MHz, exactly. No MMCM. ──────────────
    // 640x480@60 nominally wants 25.175 MHz; 25.000 gives 59.52 Hz refresh,
    // which every VGA monitor accepts. The existing RTL already assumes 25.
    reg clk_div = 1'b0;
    always @(posedge sys_clk) clk_div <= ~clk_div;

    wire clk_pixel;
    BUFG u_bufg_pix (.I(clk_div), .O(clk_pixel));

    reg [2:0] pix_rst_sync = 3'b000;
    always @(posedge clk_pixel) pix_rst_sync <= {pix_rst_sync[1:0], rst_n_db};
    wire pix_rst_n = pix_rst_sync[2];

    // ── Video timing ─────────────────────────────────────────────────────
    wire [9:0] vx, vy;
    wire hsync, vsync, active;
    spu_video_timing u_timing (
        .clk(clk_pixel), .rst_n(pix_rst_n),
        .x(vx), .y(vy), .hsync(hsync), .vsync(vsync), .active(active));

    // ── Test pattern ─────────────────────────────────────────────────────
    wire [7:0] pr, pg, pb;
    spu_video_pattern u_pattern (
        .clk_pixel(clk_pixel), .rst_n(pix_rst_n),
        .x(vx), .y(vy), .vsync(vsync), .r(pr), .g(pg), .b(pb));

    // spu_video_pattern registers its output, so delay sync/active by one
    // pixel to match, exactly as spu_gpu_top.v does. Without this the sync
    // domain describes pixel N while the colour pipeline delivers N-1.
    reg hsync_d, vsync_d, active_d;
    always @(posedge clk_pixel or negedge pix_rst_n) begin
        if (!pix_rst_n) begin
            hsync_d <= 1'b0; vsync_d <= 1'b0; active_d <= 1'b0;
        end else begin
            hsync_d <= hsync; vsync_d <= vsync; active_d <= active;
        end
    end

    // ── VGA output ───────────────────────────────────────────────────────
    // hal_vga still does the active-region blanking; only the MSB of each
    // channel is brought to a pin. spu_video_pattern drives every channel
    // fully on or fully off, so one bit per channel loses nothing here and
    // the whole DAC is three resistors. J10 has 8 IO pins; this uses 5.
    wire [3:0] r4, g4, b4;
    wire vs_one;
    hal_vga u_vga (
        .r(pr[7:4]), .g(pg[7:4]), .b(pb[7:4]),
        .hsync(hsync_d), .vsync(vsync_d), .active(active_d),
        .vga_r(r4), .vga_g(g4), .vga_b(b4),
        .vga_hsync(vga_hsync), .vga_vsync(vs_one));

    // VSYNC broadcast to every bottom-row pin, so it reaches the wire
    // whichever hole it is in. Diagnostic only.
    assign vga_vsync = {4{vs_one}};

    assign vga_r = r4[3];
    assign vga_g = g4[3];
    assign vga_b = b4[3];

endmodule
