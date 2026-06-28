// HAL_HDMI.v — HDMI output driver supporting GW5A (Gowin) and Artix-7 (Xilinx)
// 3× TMDS channels + clock channel.
// clk_pixel = 25 MHz (640×480@60Hz pixel clock)
// clk_tmds  = 250 MHz (10× pixel clock for 10:1 serialisation)
// CC0 1.0 Universal.

module hal_hdmi #(
    parameter DEVICE = "GW5A" // "GW5A" for Gowin, "A7" or "XILINX" for Xilinx Artix-7
) (
    input  wire        clk_pixel,   // 25 MHz
    input  wire        clk_tmds,    // 250 MHz
    input  wire        rst_n,

    input  wire [7:0]  r,
    input  wire [7:0]  g,
    input  wire [7:0]  b,
    input  wire        hsync,
    input  wire        vsync,
    input  wire        active,

    // HDMI differential pairs
    output wire        tmds_clk_p,
    output wire        tmds_clk_n,
    output wire [2:0]  tmds_d_p,
    output wire [2:0]  tmds_d_n
);

    // ── TMDS encoding (one per channel, platform independent) ────────────
    wire [9:0] tmds_r, tmds_g, tmds_b;
    wire [1:0] sync_ctrl;
    assign sync_ctrl = {vsync, hsync};

    hal_hdmi_tmds u_enc_b (.clk(clk_pixel), .rst_n(rst_n),
        .data(b), .ctrl(sync_ctrl), .active(active), .tmds_out(tmds_b));
    hal_hdmi_tmds u_enc_g (.clk(clk_pixel), .rst_n(rst_n),
        .data(g), .ctrl(2'b00), .active(active), .tmds_out(tmds_g));
    hal_hdmi_tmds u_enc_r (.clk(clk_pixel), .rst_n(rst_n),
        .data(r), .ctrl(2'b00), .active(active), .tmds_out(tmds_r));

    generate
        if (DEVICE == "GW5A") begin: gowin_serdes
            // ── Gowin OSER10 serialisers (10:1 serialisation at clk_tmds) ──
            wire ser_b, ser_g, ser_r, ser_clk;

            OSER10 #(.GSREN("false"), .LSREN("true")) u_ser_b (
                .D0(tmds_b[0]), .D1(tmds_b[1]), .D2(tmds_b[2]), .D3(tmds_b[3]),
                .D4(tmds_b[4]), .D5(tmds_b[5]), .D6(tmds_b[6]), .D7(tmds_b[7]),
                .D8(tmds_b[8]), .D9(tmds_b[9]),
                .PCLK(clk_pixel), .FCLK(clk_tmds), .RESET(!rst_n), .Q(ser_b));

            OSER10 #(.GSREN("false"), .LSREN("true")) u_ser_g (
                .D0(tmds_g[0]), .D1(tmds_g[1]), .D2(tmds_g[2]), .D3(tmds_g[3]),
                .D4(tmds_g[4]), .D5(tmds_g[5]), .D6(tmds_g[6]), .D7(tmds_g[7]),
                .D8(tmds_g[8]), .D9(tmds_g[9]),
                .PCLK(clk_pixel), .FCLK(clk_tmds), .RESET(!rst_n), .Q(ser_g));

            OSER10 #(.GSREN("false"), .LSREN("true")) u_ser_r (
                .D0(tmds_r[0]), .D1(tmds_r[1]), .D2(tmds_r[2]), .D3(tmds_r[3]),
                .D4(tmds_r[4]), .D5(tmds_r[5]), .D6(tmds_r[6]), .D7(tmds_r[7]),
                .D8(tmds_r[8]), .D9(tmds_r[9]),
                .PCLK(clk_pixel), .FCLK(clk_tmds), .RESET(!rst_n), .Q(ser_r));

            // Clock channel: serialise 5-bit 1010101010 pattern
            OSER10 #(.GSREN("false"), .LSREN("true")) u_ser_clk (
                .D0(1'b1), .D1(1'b1), .D2(1'b1), .D3(1'b1), .D4(1'b1),
                .D5(1'b0), .D6(1'b0), .D7(1'b0), .D8(1'b0), .D9(1'b0),
                .PCLK(clk_pixel), .FCLK(clk_tmds), .RESET(!rst_n), .Q(ser_clk));

            // ── Gowin Differential output buffers ──────────────────────────
            ELVDS_OBUF u_obuf_clk (.I(ser_clk), .O(tmds_clk_p), .OB(tmds_clk_n));
            ELVDS_OBUF u_obuf_b   (.I(ser_b),   .O(tmds_d_p[0]), .OB(tmds_d_n[0]));
            ELVDS_OBUF u_obuf_g   (.I(ser_g),   .O(tmds_d_p[1]), .OB(tmds_d_n[1]));
            ELVDS_OBUF u_obuf_r   (.I(ser_r),   .O(tmds_d_p[2]), .OB(tmds_d_n[2]));

        end else begin: xilinx_serdes
            // ── Synchronize clk_pixel to clk_tmds to generate load pulse ──
            reg [2:0] clk_pixel_sync;
            always @(posedge clk_tmds or negedge rst_n) begin
                if (!rst_n) begin
                    clk_pixel_sync <= 3'd0;
                end else begin
                    clk_pixel_sync <= {clk_pixel_sync[1:0], clk_pixel};
                end
            end

            wire load_p = (clk_pixel_sync[1] && !clk_pixel_sync[2]);

            // ── Xilinx 10:1 Shift Registers (LSB first) ────────────────────
            reg [9:0] shift_r, shift_g, shift_b, shift_clk;

            always @(posedge clk_tmds or negedge rst_n) begin
                if (!rst_n) begin
                    shift_r   <= 10'd0;
                    shift_g   <= 10'd0;
                    shift_b   <= 10'd0;
                    shift_clk <= 10'b1111100000;
                end else if (load_p) begin
                    shift_r   <= tmds_r;
                    shift_g   <= tmds_g;
                    shift_b   <= tmds_b;
                    shift_clk <= 10'b1111100000; // 5-ones, 5-zeros clock pattern
                end else begin
                    shift_r   <= {1'b0, shift_r[9:1]};
                    shift_g   <= {1'b0, shift_g[9:1]};
                    shift_b   <= {1'b0, shift_b[9:1]};
                    shift_clk <= {1'b0, shift_clk[9:1]};
                end
            end

            wire ser_r   = shift_r[0];
            wire ser_g   = shift_g[0];
            wire ser_b   = shift_b[0];
            wire ser_clk = shift_clk[0];

            // ── Xilinx Differential output buffers ──────────────────────────
            OBUFDS u_obuf_clk (.I(ser_clk), .O(tmds_clk_p), .OB(tmds_clk_n));
            OBUFDS u_obuf_b   (.I(ser_b),   .O(tmds_d_p[0]), .OB(tmds_d_n[0]));
            OBUFDS u_obuf_g   (.I(ser_g),   .O(tmds_d_p[1]), .OB(tmds_d_n[1]));
            OBUFDS u_obuf_r   (.I(ser_r),   .O(tmds_d_p[2]), .OB(tmds_d_n[2]));
        end
    endgenerate

endmodule
