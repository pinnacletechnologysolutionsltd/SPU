// hal_hdmi_serdes_a7.v — Artix-7 10:1 TMDS serialiser for one channel.
//
// Replaces the fabric shift-register serialisation that hal_hdmi.v's Xilinx
// branch used until 2026-09-04. That version clocked a 10-bit shift register
// at 250 MHz (10x pixel) in general fabric, which does not close timing on a
// -1 speed grade. This uses the hard OSERDESE2 primitive in the canonical
// MASTER/SLAVE cascade, so the serial clock is 5x pixel (125 MHz) at DDR
// rather than 10x at SDR.
//
// Bit order is LSB-first, matching DVI 1.0 and the Gowin OSER10 branch.
// CC0 1.0 Universal.

module hal_hdmi_serdes_a7 (
    input  wire       clk_pixel,   // 25 MHz  — OSERDESE2 CLKDIV
    input  wire       clk_serial,  // 125 MHz — OSERDESE2 CLK (5x, DDR)
    input  wire       rst,         // active high, synchronous release
    input  wire [9:0] data,        // TMDS symbol, transmitted LSB first
    output wire       tmds_p,
    output wire       tmds_n
);

    wire ser_out;
    wire shift1, shift2;

    // OSERDESE2's RST asserts asynchronously but must be RELEASED
    // synchronously to CLKDIV, or the master/slave pair can come out of
    // reset on different CLKDIV edges and the 10-bit symbol phase is then
    // wrong for the life of the link. Two flops in the CLKDIV domain.
    // Purely synchronous: an async-preset version created a second control
    // set in the pixel domain, and a Xilinx SLICE shares one set/reset across
    // all its flip-flops. Reset is held far longer than two pixel clocks
    // (MMCM lock alone takes thousands), so synchronous assertion is enough.
    reg [1:0] rst_sync = 2'b11;
    always @(posedge clk_pixel) rst_sync <= {rst_sync[0], rst};
    wire rst_ser = rst_sync[1];

    // ── Master: carries data[7:0] ────────────────────────────────────────
    OSERDESE2 #(
        .DATA_RATE_OQ   ("DDR"),
        .DATA_RATE_TQ   ("SDR"),
        .DATA_WIDTH     (10),
        .SERDES_MODE    ("MASTER"),
        .TRISTATE_WIDTH (1),
        .TBYTE_CTL      ("FALSE"),
        .TBYTE_SRC      ("FALSE")
    ) u_master (
        .OQ        (ser_out),
        .OFB       (),
        .TQ        (),
        .TFB       (),
        .TBYTEOUT  (),
        .SHIFTOUT1 (),
        .SHIFTOUT2 (),
        .CLK       (clk_serial),
        .CLKDIV    (clk_pixel),
        .D1        (data[0]), .D2 (data[1]), .D3 (data[2]), .D4 (data[3]),
        .D5        (data[4]), .D6 (data[5]), .D7 (data[6]), .D8 (data[7]),
        .OCE       (1'b1),
        .RST       (rst_ser),
        .SHIFTIN1  (shift1),
        .SHIFTIN2  (shift2),
        .T1        (1'b0), .T2 (1'b0), .T3 (1'b0), .T4 (1'b0),
        .TBYTEIN   (1'b0),
        .TCE       (1'b0)
    );

    // ── Slave: carries data[9:8] on D3/D4, cascaded into the master ──────
    OSERDESE2 #(
        .DATA_RATE_OQ   ("DDR"),
        .DATA_RATE_TQ   ("SDR"),
        .DATA_WIDTH     (10),
        .SERDES_MODE    ("SLAVE"),
        .TRISTATE_WIDTH (1),
        .TBYTE_CTL      ("FALSE"),
        .TBYTE_SRC      ("FALSE")
    ) u_slave (
        .OQ        (),
        .OFB       (),
        .TQ        (),
        .TFB       (),
        .TBYTEOUT  (),
        .SHIFTOUT1 (shift1),
        .SHIFTOUT2 (shift2),
        .CLK       (clk_serial),
        .CLKDIV    (clk_pixel),
        .D1        (1'b0),    .D2 (1'b0),
        .D3        (data[8]), .D4 (data[9]),
        .D5        (1'b0),    .D6 (1'b0), .D7 (1'b0), .D8 (1'b0),
        .OCE       (1'b1),
        .RST       (rst_ser),
        .SHIFTIN1  (1'b0),
        .SHIFTIN2  (1'b0),
        .T1        (1'b0), .T2 (1'b0), .T3 (1'b0), .T4 (1'b0),
        .TBYTEIN   (1'b0),
        .TCE       (1'b0)
    );

    OBUFDS u_obuf (.I(ser_out), .O(tmds_p), .OB(tmds_n));

endmodule
