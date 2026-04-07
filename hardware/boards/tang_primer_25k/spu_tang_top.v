// spu_tang_top.v — Tang Primer 25K board top (v3.0 — dual-core: SPU-13 + 4× SPU-4)
// Target:  GW5A-LV25MG121NES (Tang Primer 25K)
// Crystal: 50 MHz  →  PLLA  →  25 MHz (clk_fast) + Piranha Pulse (61.44 kHz)
//
// Resources available (GW5A-25A):
//   LUTs: 20,736     DSPs: 54     BSRAM: 28×18 Kb
//   SPU-13 Cortex (TDM) + 4× SPU-4 Sentinel + SDRAM bridge.
//
// Sentinel array: 4× spu4_top on clk_piranha, one per Quadray axis (A,B,C,D).
// SPU-13 Cortex:  spu13_core on clk_fast (25 MHz TDM).
//
// Memory:
//   Onboard SDRAM  — spu_mem_bridge_sdram.v (W9825G6KH-6, 32 MB)
//   Expansion SDRAM (512 Mb Sipeed module) — to be wired when module arrives.
//
// RP2350 bridge: UART1 at 921 600 baud on GPIO pins.
//
// LED status (active-low):
//   led[0] = PLL locked
//   led[1] = Janus point (manifold stable)
//   led[2] = bloom_complete pulse
//   led[3] = SDRAM mem_ready
//   led[4] = burst active (rd or wr in flight)
//   led[5] = Whisper TX ready
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"

module spu_tang_top (
    input  wire        sys_clk,          // 50 MHz onboard crystal

    output wire [5:0]  led,              // active-low status LEDs

    // Onboard SDRAM (W9825G6KH-6, 32 MB)
    output wire        sdram_clk,
    output wire        sdram_cs_n,
    output wire        sdram_ras_n,
    output wire        sdram_cas_n,
    output wire        sdram_we_n,
    output wire [1:0]  sdram_ba,
    output wire [12:0] sdram_addr,
    inout  wire [15:0] sdram_dq,

    // RP2350 UART bridge
    input  wire        uart_rx,
    output wire        uart_tx,

    // Whisper 1-wire telemetry
    output wire        whisper_tx
);

    // ------------------------------------------------------------------ //
    // 1. PLL: 50 MHz → 24 MHz                                            //
    //    rPLL parameters for GW5A (verified via GOWIN IP wizard):         //
    //    IDIV_SEL=1 (÷2), FBDIV_SEL=23 (×24) → VCO=600 MHz              //
    //    ODIV_SEL=25 → Fout = 600/25 = 24 MHz                            //
    //    If nextpnr-gowin flags the ODIV, use GOWIN EDA PLL IP instead.   //
    // ------------------------------------------------------------------ //
    wire clk_fast;    // 24 MHz — SPU-13 TDM clock
    wire pll_lock;

    // PLLA: 50 MHz → 25 MHz
    // VCO = FCLKIN × MDIV_SEL / IDIV_SEL = 50 × 16 / 1 = 800 MHz (in-range: 800-1600 MHz)
    // CLKOUT0 = VCO / ODIV0_SEL = 800 / 32 = 25 MHz
    //
    // All ODIV1..6, DT_DIR, DT_STEP params are set explicitly so Yosys
    // encodes them as binary strings in the netlist JSON.  gowin_pack's built-in
    // PLLA defaults are Python ints that break its own int(val,2) parser — this
    // is a known gowin_pack bug workaround (oss-cad-suite apycula).
    PLLA #(
        .FCLKIN          ("50"),
        .IDIV_SEL        (1),
        .FBDIV_SEL       (1),
        .MDIV_SEL        (16),
        .MDIV_FRAC_SEL   (0),
        .ODIV0_SEL       (32),
        .ODIV1_SEL       (8),
        .ODIV2_SEL       (8),
        .ODIV3_SEL       (8),
        .ODIV4_SEL       (8),
        .ODIV5_SEL       (8),
        .ODIV6_SEL       (8),
        .CLKOUT0_EN      ("TRUE"),
        .CLKOUT1_EN      ("FALSE"),
        .CLKOUT2_EN      ("FALSE"),
        .CLKOUT3_EN      ("FALSE"),
        .CLKOUT4_EN      ("FALSE"),
        .CLKOUT5_EN      ("FALSE"),
        .CLKOUT6_EN      ("FALSE"),
        .CLKOUT0_DT_DIR  (1'b1),
        .CLKOUT1_DT_DIR  (1'b1),
        .CLKOUT2_DT_DIR  (1'b1),
        .CLKOUT3_DT_DIR  (1'b1),
        .CLKOUT0_DT_STEP (4'b0),
        .CLKOUT1_DT_STEP (4'b0),
        .CLKOUT2_DT_STEP (4'b0),
        .CLKOUT3_DT_STEP (4'b0),
        .CLK0_IN_SEL     (1'b0),
        .CLK0_OUT_SEL    (1'b0),
        .CLK1_IN_SEL     (1'b0),
        .CLK1_OUT_SEL    (1'b0),
        .CLK2_IN_SEL     (1'b0),
        .CLK2_OUT_SEL    (1'b0),
        .CLK3_IN_SEL     (1'b0),
        .CLK3_OUT_SEL    (1'b0)
    ) u_pll (
        .CLKIN   (sys_clk),
        .CLKOUT0 (clk_fast),
        .LOCK    (pll_lock),
        .RESET   (1'b0),
        .PLLPWD  (1'b0),
        .RESET_I (1'b0), .RESET_O(1'b0),
        .PSSEL   (3'b0), .PSDIR(1'b0), .PSPULSE(1'b0),
        .SSCPOL  (1'b0), .SSCON(1'b0),
        .SSCMDSEL(7'b0), .SSCMDSEL_FRAC(3'b0),
        .MDCLK   (1'b0), .MDAINC(1'b0),
        .MDOPC   (2'b0), .MDWDI(8'b0),
        .CLKFB   (1'b0),
        .CLKOUT1 (), .CLKOUT2 (), .CLKOUT3 (),
        .CLKOUT4 (), .CLKOUT5 (), .CLKOUT6 (),
        .CLKFBOUT(), .MDRDO()
    );

    wire rst_n = pll_lock;

    // ------------------------------------------------------------------ //
    // 2. Piranha Pulse (61.44 kHz) from Fibonacci clock divider          //
    // ------------------------------------------------------------------ //
    wire phi_8, phi_13, phi_21, clk_piranha;

    spu_sierpinski_clk u_clk (
        .clk       (clk_fast),
        .rst_n     (rst_n),
        .phi_8     (phi_8),
        .phi_13    (phi_13),
        .phi_21    (phi_21),
        .heartbeat (clk_piranha)
    );

    // ------------------------------------------------------------------ //
    // 3. SDRAM bridge (W9825G6KH-6, 32 MB)                              //
    // ------------------------------------------------------------------ //
    wire                          mem_ready;
    wire                          mem_burst_rd;
    wire                          mem_burst_wr;
    wire [`MEM_ADDR_WIDTH-1:0]    mem_addr;
    wire [`MANIFOLD_WIDTH-1:0]    mem_rd_manifold;
    wire [`MANIFOLD_WIDTH-1:0]    mem_wr_manifold;
    wire                          mem_burst_done;

    spu_mem_bridge_sdram u_sdram (
        .clk             (clk_fast),
        .reset           (!rst_n),
        .mem_ready       (mem_ready),
        .mem_burst_rd    (mem_burst_rd),
        .mem_burst_wr    (mem_burst_wr),
        .mem_addr        (mem_addr),
        .mem_rd_manifold (mem_rd_manifold),
        .mem_wr_manifold (mem_wr_manifold),
        .mem_burst_done  (mem_burst_done),
        .sdram_clk       (sdram_clk),
        .sdram_cs_n      (sdram_cs_n),
        .sdram_ras_n     (sdram_ras_n),
        .sdram_cas_n     (sdram_cas_n),
        .sdram_we_n      (sdram_we_n),
        .sdram_ba        (sdram_ba),
        .sdram_addr      (sdram_addr),
        .sdram_dq        (sdram_dq)
    );

    // ------------------------------------------------------------------ //
    // 4. SPU-13 Cortex (TDM, 1 DSP slice, fits on GW5A-25)              //
    // ------------------------------------------------------------------ //
    wire [`MANIFOLD_WIDTH-1:0] manifold_out;
    wire                       bloom_done;
    wire                       is_janus_point;

    spu13_core #(.DEVICE("GW5A")) u_cortex (
        .clk             (clk_fast),
        .rst_n           (rst_n),
        .phi_8           (phi_8),
        .phi_13          (phi_13),
        .phi_21          (phi_21),
        .mem_ready       (mem_ready),
        .mem_burst_rd    (mem_burst_rd),
        .mem_burst_wr    (mem_burst_wr),
        .mem_addr        (mem_addr),
        .mem_rd_manifold (mem_rd_manifold),
        .mem_wr_manifold (mem_wr_manifold),
        .mem_burst_done  (mem_burst_done),
        .manifold_out    (manifold_out),
        .bloom_complete  (bloom_done),
        .is_janus_point  (is_janus_point)
    );

    // ------------------------------------------------------------------ //
    // 5. 4× SPU-4 Sentinel Cores (Quadray satellite array)              //
    //    Each sentinel runs on clk_piranha (61.44 kHz), one per         //
    //    Quadray axis (A, B, C, D). All fed OP_SNAP continuously.       //
    // ------------------------------------------------------------------ //
    wire [3:0]  sentinel_snap;
    wire [3:0]  sentinel_whisper;
    wire [63:0] sentinel_r0 [0:3];

    genvar si;
    generate
        for (si = 0; si < 4; si = si + 1) begin : gen_sentinels
            spu4_top u_sentinel (
                .clk          (clk_piranha),
                .rst_n        (rst_n),
                .inst_data    (24'h800000),      // OP_SNAP: autonomous Quadray snap
                .pc           (),
                .snap_alert   (sentinel_snap[si]),
                .whisper_tx   (sentinel_whisper[si]),
                .debug_reg_r0 (sentinel_r0[si])
            );
        end
    endgenerate

    // Combine all sentinel snaps into artery-ready signal
    wire any_sentinel_snap = |sentinel_snap;

    // ------------------------------------------------------------------ //
    // 6. Whisper TX (PWI 1-wire telemetry to RP2350/RP2040)              //
    // ------------------------------------------------------------------ //
    wire whisper_ready;

    SPU_WHISPER_TX #(.K_FACTOR(8)) u_whisper (
        .clk     (clk_fast),
        .rst_n   (rst_n),
        .trig_en (bloom_done),
        .is_sync (1'b0),
        .surd_a  (manifold_out[15:0]),
        .surd_b  (manifold_out[31:16]),
        .pwi_out (whisper_tx),
        .tx_ready(whisper_ready)
    );

    // UART stub (RP2350 bridge — full framing in future firmware revision)
    assign uart_tx = 1'b1; // idle high

    // ------------------------------------------------------------------ //
    // 7. LED status (active-low)                                         //
    // ------------------------------------------------------------------ //
    assign led[0] = ~pll_lock;                        // PLL locked
    assign led[1] = ~is_janus_point;                  // manifold stable
    assign led[2] = ~bloom_done;                      // bloom pulse
    assign led[3] = ~any_sentinel_snap;               // any sentinel snap
    assign led[4] = ~(mem_burst_rd | mem_burst_wr);   // burst active
    assign led[5] = ~whisper_ready;                   // Whisper TX ready

endmodule

