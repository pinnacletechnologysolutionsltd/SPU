// spu_psram_dual.v — Dual-Bank PSRAM Arbiter
// Target:     Two APS6404L (8MB each) on independent QSPI buses
// Board:      Tang Nano 9K — PMOD0 (bank 0) and PMOD1 (bank 1)
//
// Address space: 16 MB linear — fractal address from spu_laminar_ram.v
//   Bank 0:   addr[23:0] where addr[23]=0 → 0x000000 – 0x7FFFFF  (PMOD0)
//   Bank 1:   addr[23:0] where addr[23]=1 → 0x800000 – 0xFFFFFF  (PMOD1)
//
// Both chips initialise in parallel.
// mem_ready is asserted when both init_done are high AND the selected
// bank's controller reports ready.
// CC0 1.0 Universal.

module spu_psram_dual (
    input  wire        clk,
    input  wire        reset,

    // --- Sovereign Manifold Bus ---
    input  wire [23:0]   mem_addr,       // fractal address from spu_laminar_ram
    output wire          mem_ready,
    input  wire          mem_burst_rd,
    input  wire          mem_burst_wr,
    output wire [831:0]  mem_rd_manifold,
    input  wire [831:0]  mem_wr_manifold,
    output wire          mem_burst_done,
    output wire          mem_init_done,

    // Single-word legacy access (SovereignBus 16-bit)
    input  wire          mem_rd_en,
    input  wire          mem_wr_en,
    input  wire [15:0]   mem_wr_data,
    output wire [15:0]   mem_rd_data,

    // --- PSRAM Bank 0 — PMOD0 physical pins ---
    output wire          psram0_ce_n,
    output wire          psram0_clk,
    inout  wire [3:0]    psram0_dq,

    // --- PSRAM Bank 1 — PMOD1 physical pins ---
    output wire          psram1_ce_n,
    output wire          psram1_clk,
    inout  wire [3:0]    psram1_dq
);

    // Bank select: bit 23 of the fractal address (output of spu_laminar_ram)
    wire bank_sel;
    assign bank_sel = mem_addr[23];

    // Route each request class to the selected bank only
    wire rd0;
    assign rd0 = mem_rd_en    & ~bank_sel;
    wire wr0;
    assign wr0 = mem_wr_en    & ~bank_sel;
    wire brd0;
    assign brd0 = mem_burst_rd & ~bank_sel;
    wire bwr0;
    assign bwr0 = mem_burst_wr & ~bank_sel;

    wire rd1;
    assign rd1 = mem_rd_en    &  bank_sel;
    wire wr1;
    assign wr1 = mem_wr_en    &  bank_sel;
    wire brd1;
    assign brd1 = mem_burst_rd &  bank_sel;
    wire bwr1;
    assign bwr1 = mem_burst_wr &  bank_sel;

    // Per-bank response wires
    wire         ready0, ready1;
    wire         done0,  done1;
    wire         init0,  init1;
    wire [831:0] mrd0,   mrd1;
    wire [15:0]  srd0,   srd1;

    // Unified bus outputs
    assign mem_init_done   = init0 & init1;
    assign mem_ready       = mem_init_done & (bank_sel ? ready1 : ready0);
    assign mem_burst_done  = bank_sel ? done1 : done0;
    assign mem_rd_manifold = bank_sel ? mrd1  : mrd0;
    assign mem_rd_data     = bank_sel ? srd1  : srd0;

    spu_psram_ctrl u_psram0 (
        .clk              (clk),
        .reset            (reset),
        .rd_en            (rd0),
        .wr_en            (wr0),
        .addr             (mem_addr[22:0]),
        .wr_data          (mem_wr_data),
        .rd_data          (srd0),
        .ready            (ready0),
        .init_done        (init0),
        .burst_rd         (brd0),
        .burst_wr         (bwr0),
        .manifold_wr_data (mem_wr_manifold),
        .manifold_rd_data (mrd0),
        .burst_done       (done0),
        .psram_ce_n       (psram0_ce_n),
        .psram_clk        (psram0_clk),
        .psram_dq         (psram0_dq)
    );

    spu_psram_ctrl u_psram1 (
        .clk              (clk),
        .reset            (reset),
        .rd_en            (rd1),
        .wr_en            (wr1),
        .addr             (mem_addr[22:0]),
        .wr_data          (mem_wr_data),
        .rd_data          (srd1),
        .ready            (ready1),
        .init_done        (init1),
        .burst_rd         (brd1),
        .burst_wr         (bwr1),
        .manifold_wr_data (mem_wr_manifold),
        .manifold_rd_data (mrd1),
        .burst_done       (done1),
        .psram_ce_n       (psram1_ce_n),
        .psram_clk        (psram1_clk),
        .psram_dq         (psram1_dq)
    );

endmodule
