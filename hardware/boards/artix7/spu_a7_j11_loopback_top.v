// spu_a7_j11_loopback_top.v — minimal J11 SPI electrical loopback probe.
// No dependency on spu_spi_slave.v (sidesteps the boot_ready/nextpnr timing
// regression tracked separately — see AGENTS.md). Purpose: verify the
// remapped J11 bottom-row pins (spi_cs_n/spi_sck/spi_mosi/spi_miso ->
// J4/G4/B4/B5, spu_a7_100t.xdc) carry a real, correctly-timed signal in
// both directions, independent of the main core or any protocol semantics.
// Same port list as spu_a7_top so spu_a7_100t.xdc applies unchanged.
//
// SPI loopback: each MOSI bit sampled on the rising edge of SCK is echoed
// back out on MISO from that edge until the next one (one-SCK-cycle
// digital loopback, entirely within the spi_sck clock domain — no cross-
// domain synchronizer needed for this purpose). MISO idles low while CS
// is deasserted so active vs. idle is visually/scope-obvious.
//
// UART heartbeat ("UART:P\r\n" on uart_tx/E3, the confirmed-healthy
// channel on this unit) proves clk_100mhz/core logic independent of SPI —
// same design as spu_a7_uart_probe_top.v. led_out is NOT used for status
// here: this unit's led_out bank is a known, unresolved anomaly (see
// spu_a7_100t.xdc) and would make a bad witness for a new test.
module spu_a7_j11_loopback_top (
    input  wire        clk_100mhz,
    input  wire        rst_n,
    input  wire        spi_cs_n, spi_sck, spi_mosi,
    output wire        spi_miso,
    output wire        uart_tx,
    output wire [3:0]  hdmi_d_p, hdmi_d_n,
    output wire        hdmi_clk_p, hdmi_clk_n,
    output wire        i2s_bclk, i2s_lrclk, i2s_dout,
    input  wire [7:0]  sensor_in,
    output wire [3:0]  led_out,
    output wire        fault_led
);

    // ── SPI loopback (spi_sck clock domain) ──
    reg mosi_capture;
    always @(posedge spi_sck)
        mosi_capture <= spi_mosi;
    assign spi_miso = spi_cs_n ? 1'b0 : mosi_capture;

    // ── Heartbeat (same as spu_a7_blinky_top; best-effort only, see above) ──
    reg [26:0] ctr = 27'd0;
    always @(posedge clk_100mhz)
        ctr <= ctr + 27'd1;
    assign led_out = {ctr[26], ctr[25], ctr[24], ctr[23]};
    assign fault_led = 1'b0;
    assign hdmi_d_p = 4'd0;
    assign hdmi_d_n = 4'd0;
    assign hdmi_clk_p = 1'b0;
    assign hdmi_clk_n = 1'b0;
    assign i2s_bclk = 1'b0;
    assign i2s_lrclk = 1'b0;
    assign i2s_dout = 1'b0;

    // ── Minimal free-running UART TX: "UART:P\r\n" repeated ──
    // 50 MHz / 115200 baud ~= 434 cycles/bit.
    localparam BAUD_DIV = 434;
    localparam MSG_LEN = 9;
    reg [7:0] msg [0:MSG_LEN-1];
    initial begin
        msg[0] = "U"; msg[1] = "A"; msg[2] = "R"; msg[3] = "T";
        msg[4] = ":"; msg[5] = "P"; msg[6] = "\r"; msg[7] = "\n";
        msg[8] = 8'h00; // unused pad
    end

    reg [15:0] baud_cnt = 16'd0;
    wire       baud_tick = (baud_cnt == BAUD_DIV-1);

    reg [3:0]  msg_idx = 4'd0;
    reg [9:0]  shift_reg = 10'h3FF;
    reg [3:0]  bits_rem = 4'd0;
    reg        tx_r = 1'b1;
    // gap counter between repeated messages (~1s at 115200 baud ticks)
    reg [24:0] gap_cnt = 25'd0;
    reg        gapping = 1'b0;

    assign uart_tx = tx_r;

    always @(posedge clk_100mhz) begin
        if (baud_tick)
            baud_cnt <= 16'd0;
        else
            baud_cnt <= baud_cnt + 16'd1;

        if (baud_tick) begin
            if (gapping) begin
                if (gap_cnt == 25'd115_200) begin
                    gapping <= 1'b0;
                    gap_cnt <= 25'd0;
                end else begin
                    gap_cnt <= gap_cnt + 25'd1;
                end
            end else if (bits_rem == 4'd0) begin
                if (msg_idx < MSG_LEN - 1) begin
                    shift_reg <= {1'b1, msg[msg_idx], 1'b0};
                    bits_rem <= 4'd10;
                    msg_idx <= msg_idx + 4'd1;
                end else begin
                    msg_idx <= 4'd0;
                    gapping <= 1'b1;
                    tx_r <= 1'b1;
                end
            end else begin
                tx_r <= shift_reg[0];
                shift_reg <= {1'b1, shift_reg[9:1]};
                bits_rem <= bits_rem - 4'd1;
            end
        end
    end

endmodule
