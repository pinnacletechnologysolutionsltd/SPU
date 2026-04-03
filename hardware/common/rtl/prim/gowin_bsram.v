// gowin_bsram.v — GOWIN GW1N-9C SDPB (Simple Dual Port Block RAM) Wrapper
// Capacity:   18 Kb per instance (1024 × 18-bit or 512 × 36-bit)
// Interface:  Write port A (sync), Read port B (sync, 1-cycle latency)
// Default:    16-bit data width, 1024-deep (10-bit address)
// The GW1N-9C device has 26 × 18-Kb BSRAM blocks = 468 Kb total.
// CC0 1.0 Universal.
//
// BIT_WIDTH mapping for GOWIN SDPB:
//   BIT_WIDTH  | addr bits | data bits (excl. parity)
//   -----------+-----------+-------------------------
//       1      |    14     |    1
//       2      |    13     |    2
//       4      |    12     |    4
//       8      |    11     |    8
//      16      |    10     |   16  ← default
//      32      |     9     |   32
//
// Parity bits (DIN[17:16] / DOUT[17:16] for 16-bit mode) are tied to 0
// and left unconnected; they are not used by the SPU data path.

module gowin_bsram #(
    parameter BIT_WIDTH = 16,   // data width per port (8, 16 or 32)
    parameter ADDR_WIDTH = 10,  // must match BIT_WIDTH (see table above)
    parameter BLK_SEL   = 3'b000 // block cascade select — unique per instance
)(
    // Write port (A)
    input  wire                  clk_a,
    input  wire                  we_a,    // write enable
    input  wire                  rst_a,
    input  wire [ADDR_WIDTH-1:0] addr_a,
    input  wire [BIT_WIDTH-1:0]  din_a,

    // Read port (B) — 1 clock latency
    input  wire                  clk_b,
    input  wire                  re_b,    // read enable (output clock enable)
    input  wire                  rst_b,
    input  wire [ADDR_WIDTH-1:0] addr_b,
    output wire [BIT_WIDTH-1:0]  dout_b
);

    // Pad narrow data to the SDPB 36-bit data bus width
    wire [35:0] din_a_36  = {{(36-BIT_WIDTH){1'b0}}, din_a};
    wire [35:0] dout_b_36;
    assign dout_b = dout_b_36[BIT_WIDTH-1:0];

    // Pad narrow address to the SDPB 14-bit address bus
    wire [13:0] addr_a_14 = {{(14-ADDR_WIDTH){1'b0}}, addr_a};
    wire [13:0] addr_b_14 = {{(14-ADDR_WIDTH){1'b0}}, addr_b};

    SDPB #(
        .READ_MODE    (1'b0),       // 0 = transparent-off (normal)
        .BIT_WIDTH_0  (BIT_WIDTH),  // write port width
        .BIT_WIDTH_1  (BIT_WIDTH),  // read port width
        .BLK_SEL_0    (BLK_SEL),
        .BLK_SEL_1    (BLK_SEL),
        .RESET_MODE   ("SYNC")
    ) u_sdpb (
        // Write port A
        .CLKA   (clk_a),
        .CEA    (we_a),
        .RESETA (rst_a),
        .OCEA   (1'b0),
        .BLKSELA(BLK_SEL),
        .ADA    (addr_a_14),
        .DIN    (din_a_36),

        // Read port B
        .CLKB   (clk_b),
        .CEB    (re_b),
        .RESETB (rst_b),
        .BLKSELB(BLK_SEL),
        .ADB    (addr_b_14),
        .DOUT   (dout_b_36)
    );

endmodule
