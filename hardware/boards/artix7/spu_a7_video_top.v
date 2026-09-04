// spu_a7_video_top.v — Wukong Artix-7 640x480@60 DVI test-pattern spin.
//
// First video top level for this board. Deliberately carries no SPU core,
// no southbridge and no GPU: it exists to prove the display path alone
// (MMCM -> video timing -> TMDS encode -> OSERDESE2 -> TMDS_33 pads) before
// anything is built on top of it. hal_hdmi.v had never been instantiated by
// any top on any board until this file.
//
// Output is DVI, not HDMI: no infoframes, no data islands, no audio. A DVI
// sink is the intended target.
// CC0 1.0 Universal.

module spu_a7_video_top (
    input  wire        sys_clk,      // M21, 50 MHz (NOT 100 - see xdc)
    input  wire        rst_n,        // H7, active low, board PULLUP
    output wire        hdmi_clk_p,
    output wire        hdmi_clk_n,
    output wire [2:0]  hdmi_d_p,
    output wire [2:0]  hdmi_d_n
);

    // ── Reset conditioning ───────────────────────────────────────────────
    // rst_n (H7) has no external pull-down and feeding it straight into async
    // resets left this board dead in silicon for three weeks
    // (hardware_evidence.md 3.2m). Debounce, then synchronise, then gate on
    // MMCM lock. Never wire the raw pad to a reset.
    reg [15:0] db_cnt = 16'd0;
    reg        rst_n_db = 1'b0;
    always @(posedge sys_clk) begin
        if (rst_n == rst_n_db) begin
            db_cnt <= 16'd0;
        end else if (&db_cnt) begin
            rst_n_db <= rst_n;
            db_cnt   <= 16'd0;
        end else begin
            db_cnt <= db_cnt + 16'd1;
        end
    end

    // ── MMCM: 50 MHz -> 125 MHz serial (5x DDR) + 25 MHz pixel ───────────
    // VCO = 50 * 20 / 1 = 1000 MHz, inside the Artix-7 -1 600-1200 MHz range.
    // 1000/8 = 125 MHz serial, 1000/40 = 25 MHz pixel.
    // 25.000 MHz gives 59.52 Hz rather than the nominal 59.94; every DVI sink
    // tested in practice accepts this, and the existing RTL assumes 25 MHz.
    wire clk_fb, clk_ser_raw, clk_pix_raw, mmcm_locked;

    MMCME2_BASE #(
        .CLKIN1_PERIOD    (20.000),
        .DIVCLK_DIVIDE    (1),
        .CLKFBOUT_MULT_F  (20.000),
        .CLKOUT0_DIVIDE_F (8.000),
        .CLKOUT1_DIVIDE   (40),
        .STARTUP_WAIT     ("FALSE")
    ) u_mmcm (
        .CLKIN1   (sys_clk),
        .CLKFBIN  (clk_fb),
        .CLKFBOUT (clk_fb),
        .CLKOUT0  (clk_ser_raw),
        .CLKOUT1  (clk_pix_raw),
        .CLKOUT2  (), .CLKOUT3 (), .CLKOUT4 (), .CLKOUT5 (), .CLKOUT6 (),
        .CLKOUT0B (), .CLKOUT1B (), .CLKOUT2B (), .CLKOUT3B (),
        .CLKFBOUTB(),
        .LOCKED   (mmcm_locked),
        .PWRDWN   (1'b0),
        .RST      (!rst_n_db)
    );

    wire clk_serial, clk_pixel;
    BUFG u_bufg_ser (.I(clk_ser_raw), .O(clk_serial));
    BUFG u_bufg_pix (.I(clk_pix_raw), .O(clk_pixel));

    // Release the pixel-domain reset only once the MMCM has locked.
    // Synchronous only. Using mmcm_locked as an async clear made it a third
    // control set in this clock domain; a Xilinx SLICE has exactly one
    // set/reset shared by all eight flip-flops, so mixed control sets force
    // the packer into awkward placements. mmcm_locked is already glitch-free.
    reg [2:0] pix_rst_sync = 3'b000;
    always @(posedge clk_pixel)
        pix_rst_sync <= {pix_rst_sync[1:0], mmcm_locked};
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
    // pixel to match. spu_gpu_top.v carries the same correction for the same
    // reason -- an uncorrected version produced a one-pixel horizontal shift.
    reg hsync_d, vsync_d, active_d;
    always @(posedge clk_pixel or negedge pix_rst_n) begin
        if (!pix_rst_n) begin
            hsync_d <= 1'b0; vsync_d <= 1'b0; active_d <= 1'b0;
        end else begin
            hsync_d <= hsync; vsync_d <= vsync; active_d <= active;
        end
    end

    // ── DVI/TMDS output ──────────────────────────────────────────────────
    hal_hdmi #(.DEVICE("A7")) u_hdmi (
        .clk_pixel(clk_pixel), .clk_tmds(clk_serial), .rst_n(pix_rst_n),
        .r(pr), .g(pg), .b(pb),
        .hsync(hsync_d), .vsync(vsync_d), .active(active_d),
        .tmds_clk_p(hdmi_clk_p), .tmds_clk_n(hdmi_clk_n),
        .tmds_d_p(hdmi_d_p),     .tmds_d_n(hdmi_d_n));

endmodule
