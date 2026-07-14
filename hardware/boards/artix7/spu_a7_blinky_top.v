// spu_a7_blinky_top.v — minimal bring-up sanity probe, no relation to any
// spu_a7_top spin. Only a free-running counter off raw clk_100mhz driving
// led_out[3]. Same port list/pin mapping as spu_a7_top so the existing
// spu_a7_100t.xdc applies unchanged. Purpose: rule in/out a fundamental
// toolchain or board-hardware problem, independent of the IROTC design's
// size/complexity, by testing the simplest possible design through the
// identical synth/PNR/pack/JTAG-load path.
module spu_a7_blinky_top (
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

    reg [26:0] ctr = 27'd0;
    always @(posedge clk_100mhz)
        ctr <= ctr + 27'd1;

    assign led_out = {ctr[26], ctr[25], ctr[24], ctr[23]};
    assign fault_led = 1'b0;
    assign spi_miso = 1'b0;
    assign uart_tx = 1'b1;
    assign hdmi_d_p = 4'd0;
    assign hdmi_d_n = 4'd0;
    assign hdmi_clk_p = 1'b0;
    assign hdmi_clk_n = 1'b0;
    assign i2s_bclk = 1'b0;
    assign i2s_lrclk = 1'b0;
    assign i2s_dout = 1'b0;

endmodule
