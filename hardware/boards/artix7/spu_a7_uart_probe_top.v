// spu_a7_uart_probe_top.v — minimal standalone UART bring-up probe.
// No relation to any spu_a7_top spin, no RP2350/J11 dependency at all.
// Continuously repeats "UART:P\r\n" out uart_tx (pin E3, onboard CP2102N,
// Mini-USB J4) at 115200 8N1, plus drives the same heartbeat pattern on
// led_out as spu_a7_blinky_top for a visual cross-check. Same port list as
// spu_a7_top so spu_a7_100t.xdc applies unchanged.
module spu_a7_uart_probe_top (
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

    // ── Heartbeat (same as spu_a7_blinky_top, for visual cross-check) ──
    reg [26:0] ctr = 27'd0;
    always @(posedge clk_100mhz)
        ctr <= ctr + 27'd1;
    assign led_out = {ctr[26], ctr[25], ctr[24], ctr[23]};
    assign fault_led = 1'b0;
    assign spi_miso = 1'b0;
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
    reg        baud_tick_r;
    wire       baud_tick = (baud_cnt == BAUD_DIV-1);

    reg [3:0]  msg_idx = 4'd0;
    reg [9:0]  shift_reg = 10'h3FF;
    reg [3:0]  bits_rem = 4'd0;
    reg        tx_r = 1'b1;
    // gap counter between repeated messages (~0.5s at 50MHz)
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
                // gap_cnt increments once per baud_tick (~115.2k ticks/s at
                // 115200 baud), so ~115200 ticks ~= 1 second gap.
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
