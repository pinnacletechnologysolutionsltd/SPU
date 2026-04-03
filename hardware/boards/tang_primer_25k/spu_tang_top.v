// spu_tang_top.v — Tang Primer 25K board top (v2.0)
// Target:  GW5A-LV25MG121C1/I0 (Tang Primer 25K)
// Crystal: 50 MHz  →  rPLL  →  24 MHz (clk_fast) + Piranha Pulse (61.44 kHz)
//
// Resources available (GW5A-25):
//   LUTs:  ~23 000     DSPs: 28     BSRAM: 28×18 Kb
//   SPU-13 Cortex (TDM) + 4× SPU-4 Sentinel + SDRAM bridge fits comfortably.
//
// Memory:
//   Onboard SDRAM  — spu_mem_bridge_sdram.v (TODO: implement post board-arrival)
//   PSRAM Bank 0   — APS6404L on PMOD-A (your 8 Mb module)
//   PSRAM Bank 1   — APS6404L on PMOD-B (your second 8 Mb module)
//
// RP2350 bridge: UART1 at 921 600 baud on PMOD/GPIO pins.
//
// LED status (active-low):
//   led[0] = PLL locked
//   led[1] = Janus point (manifold stable)
//   led[2] = bloom_complete pulse
//   led[3] = PSRAM Bank 0 init done
//   led[4] = PSRAM Bank 1 init done
//   led[5] = Whisper TX activity
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"

module spu_tang_top (
    input  wire        sys_clk,          // 50 MHz onboard crystal

    output wire [5:0]  led,              // active-low status LEDs

    // Onboard SDRAM (W9825G6KH-6, 32 MB)
    output wire        sdram_clk,
    output wire        sdram_cke,
    output wire        sdram_cs_n,
    output wire        sdram_ras_n,
    output wire        sdram_cas_n,
    output wire        sdram_we_n,
    output wire [1:0]  sdram_ba,
    output wire [12:0] sdram_addr,
    inout  wire [15:0] sdram_dq,

    // PSRAM Bank 0 — PMOD-A
    output wire        psram0_ce_n,
    output wire        psram0_clk,
    inout  wire [3:0]  psram0_dq,

    // PSRAM Bank 1 — PMOD-B
    output wire        psram1_ce_n,
    output wire        psram1_clk,
    inout  wire [3:0]  psram1_dq,

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

    rPLL #(
        .FCLKIN     ("50"),
        .IDIV_SEL   (1),     // input ÷ 2 = 25 MHz ref
        .FBDIV_SEL  (23),    // × 24 → VCO = 600 MHz
        .ODIV_SEL   (25),    // output ÷ 25 = 24 MHz
        .DEVICE     ("GW5A-25")
    ) u_pll (
        .CLKIN   (sys_clk),
        .CLKOUT  (clk_fast),
        .LOCK    (pll_lock),
        .RESET   (1'b0), .RESET_P(1'b0),
        .FBDSEL  (6'b0), .IDSEL(6'b0), .ODSEL(6'b0),
        .PSDA    (4'b0), .DUTYDA(4'b0), .FDLY(4'b0)
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
        .sdram_cke       (sdram_cke),
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
    // 5. PSRAM Bank 0 (your APS6404L module on PMOD-A)                   //
    // ------------------------------------------------------------------ //
    wire psram0_init_done;

    spu_psram_ctrl u_psram0 (
        .clk              (clk_fast),
        .reset            (~rst_n),
        .rd_en            (1'b0),
        .wr_en            (1'b0),
        .addr             (23'h0),
        .wr_data          (16'h0),
        .rd_data          (),
        .ready            (),
        .init_done        (psram0_init_done),
        .burst_rd         (1'b0),
        .burst_wr         (1'b0),
        .manifold_wr_data (`MANIFOLD_WIDTH'h0),
        .manifold_rd_data (),
        .psram_ce_n       (psram0_ce_n),
        .psram_clk        (psram0_clk),
        .psram_dq         (psram0_dq)
    );

    // ------------------------------------------------------------------ //
    // 6. PSRAM Bank 1 (your second APS6404L module on PMOD-B)            //
    // ------------------------------------------------------------------ //
    wire psram1_init_done;

    spu_psram_ctrl u_psram1 (
        .clk              (clk_fast),
        .reset            (~rst_n),
        .rd_en            (1'b0),
        .wr_en            (1'b0),
        .addr             (23'h0),
        .wr_data          (16'h0),
        .rd_data          (),
        .ready            (),
        .init_done        (psram1_init_done),
        .burst_rd         (1'b0),
        .burst_wr         (1'b0),
        .manifold_wr_data (`MANIFOLD_WIDTH'h0),
        .manifold_rd_data (),
        .psram_ce_n       (psram1_ce_n),
        .psram_clk        (psram1_clk),
        .psram_dq         (psram1_dq)
    );

    // ------------------------------------------------------------------ //
    // 7. Whisper TX (PWI 1-wire telemetry to RP2350/RP2040)              //
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
    // 8. LED status (active-low)                                         //
    // ------------------------------------------------------------------ //
    assign led[0] = ~pll_lock;           // PLL locked
    assign led[1] = ~is_janus_point;     // manifold stable
    assign led[2] = ~bloom_done;         // bloom pulse (brief flash)
    assign led[3] = ~psram0_init_done;   // PSRAM 0 ready
    assign led[4] = ~psram1_init_done;   // PSRAM 1 ready
    assign led[5] = ~whisper_ready;         // Whisper TX ready

endmodule

