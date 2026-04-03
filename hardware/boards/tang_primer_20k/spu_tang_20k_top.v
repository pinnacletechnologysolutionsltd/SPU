// spu_tang_20k_top.v — Tang Primer 20K board top (v1.0)
// Target:  GW2A-LV18PG256C8/I7 (Tang Primer 20K)
// Crystal: 27 MHz  →  rPLL  →  24 MHz (clk_fast) + Piranha Pulse (61.44 kHz)
//
// Resources available (GW2A-18):
//   LUTs: ~20 736     DSPs: 48     BSRAM: 41×18 Kb
//   SPU-13 Cortex (TDM) + 4× SPU-4 Sentinel + DDR3 bridge fits comfortably.
//   48 DSPs is a useful increase over the 25K's 28 — good for future ALU work.
//
// Memory:
//   Onboard DDR3 (MT41K128M16JT-125, 128 MB) — spu_mem_bridge_ddr3.v (TBD)
//   LiteDRAM GW2A target will generate the PHY + controller Verilog.
//   Until then: DDR3 outputs held at safe idle; mem_ready = 0.
//
// Video:
//   HDMI TX via LVDS output buffer (OBUFDS) — HAL_Cartesian driver TBD.
//   Ports present; outputs tristated/low until driver is wired in.
//
// RP2350 bridge: UART at 921 600 baud on GPIO header pins.
//
// LED status (active-low, 5 LEDs):
//   led[0] = PLL locked
//   led[1] = Janus point (manifold stable)
//   led[2] = bloom_complete pulse
//   led[3] = DDR3 init done (stays 1 until bridge is wired)
//   led[4] = Whisper TX activity
//
// PLL: 27 MHz → 24 MHz
//   IDIV_SEL=0 (÷1), FBDIV_SEL=15 (×16) → VCO = 432 MHz (in GW2A 200–800 MHz range)
//   ODIV_SEL=18 → F_OUT = 432 / 18 = 24 MHz
//   Verify with GOWIN EDA PLL wizard before first build.
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"

module spu_tang_20k_top (
    input  wire        sys_clk,          // 27 MHz onboard crystal

    output wire [4:0]  led,              // active-low status LEDs

    // Onboard DDR3 (MT41K128M16JT-125, 128 MB)
    // ⚠ These signals connect to the LiteDRAM-generated PHY wrapper.
    //   Until spu_mem_bridge_ddr3.v is implemented they are held at safe idle.
    output wire        ddr3_ck_p,
    output wire        ddr3_ck_n,
    output wire        ddr3_cke,
    output wire        ddr3_cs_n,
    output wire        ddr3_ras_n,
    output wire        ddr3_cas_n,
    output wire        ddr3_we_n,
    output wire        ddr3_odt,
    output wire        ddr3_reset_n,
    output wire [2:0]  ddr3_ba,
    output wire [13:0] ddr3_addr,
    inout  wire [15:0] ddr3_dq,
    inout  wire [1:0]  ddr3_dqs_p,
    inout  wire [1:0]  ddr3_dqs_n,
    output wire [1:0]  ddr3_dm,

    // HDMI TX (LVDS differential — HAL_Cartesian driver TBD)
    output wire        hdmi_clk_p,
    output wire        hdmi_clk_n,
    output wire [2:0]  hdmi_d_p,
    output wire [2:0]  hdmi_d_n,

    // RP2350 UART bridge (GPIO header)
    input  wire        uart_rx,
    output wire        uart_tx,

    // Whisper 1-wire telemetry
    output wire        whisper_tx
);

    // ------------------------------------------------------------------ //
    // 1. PLL: 27 MHz → 24 MHz                                            //
    //    GW2A rPLL: VCO = 27 × (FBDIV_SEL+1) / (IDIV_SEL+1)            //
    //    IDIV=0 (÷1), FBDIV=15 (×16) → VCO = 432 MHz                   //
    //    ODIV=18 → F_OUT = 432/18 = 24 MHz                               //
    // ------------------------------------------------------------------ //
    wire clk_fast;
    wire pll_lock;

    rPLL #(
        .FCLKIN     ("27"),
        .IDIV_SEL   (0),
        .FBDIV_SEL  (15),
        .ODIV_SEL   (18),
        .DEVICE     ("GW2A-18")
    ) u_pll (
        .CLKIN   (sys_clk),
        .CLKOUT  (clk_fast),
        .LOCK    (pll_lock),
        .RESET   (1'b0), .RESET_P(1'b0),
        .FBDSEL  (6'b0), .IDSEL  (6'b0), .ODSEL  (6'b0),
        .PSDA    (4'b0), .DUTYDA (4'b0), .FDLY   (4'b0)
    );

    // ------------------------------------------------------------------ //
    // 2. Reset: hold until PLL locks                                      //
    // ------------------------------------------------------------------ //
    reg [3:0] rst_ctr = 4'hF;
    wire      rst_n   = (rst_ctr == 4'h0);

    always @(posedge clk_fast) begin
        if (!pll_lock)      rst_ctr <= 4'hF;
        else if (!rst_n)    rst_ctr <= rst_ctr - 1;
    end

    wire sys_reset = !rst_n;

    // ------------------------------------------------------------------ //
    // 3. Fractal clock: Fibonacci pulse (61.44 kHz Piranha Pulse)         //
    // ------------------------------------------------------------------ //
    wire phi_8, phi_13, phi_21, heartbeat;

    spu_sierpinski_clk u_fclk (
        .clk       (clk_fast),
        .reset     (sys_reset),
        .phi_8     (phi_8),
        .phi_13    (phi_13),
        .phi_21    (phi_21),
        .heartbeat (heartbeat)
    );

    // ------------------------------------------------------------------ //
    // 4. Soft start (Fibonacci-stepped bloom)                             //
    // ------------------------------------------------------------------ //
    wire [7:0] bloom_intensity;
    wire       bloom_complete;

    spu_soft_start u_soft_start (
        .clk            (clk_fast),
        .rst_n          (rst_n),
        .bloom_intensity(bloom_intensity),
        .bloom_complete (bloom_complete)
    );

    // ------------------------------------------------------------------ //
    // 5. DDR3 memory bridge stub                                          //
    //    ⚠ TODO: replace with spu_mem_bridge_ddr3 (LiteDRAM GW2A target) //
    //    Until then: DDR3 outputs held at safe idle state.               //
    // ------------------------------------------------------------------ //
    wire mem_ready = 1'b0;   // core waits in IDLE until bridge ready

    // DDR3 safe idle: deselect, CKE low, reset asserted
    assign ddr3_ck_p    = 1'b0;
    assign ddr3_ck_n    = 1'b1;
    assign ddr3_cke     = 1'b0;
    assign ddr3_cs_n    = 1'b1;
    assign ddr3_ras_n   = 1'b1;
    assign ddr3_cas_n   = 1'b1;
    assign ddr3_we_n    = 1'b1;
    assign ddr3_odt     = 1'b0;
    assign ddr3_reset_n = 1'b0;   // keep DRAM in reset
    assign ddr3_ba      = 3'b0;
    assign ddr3_addr    = 14'b0;
    assign ddr3_dm      = 2'b0;
    // ddr3_dq / ddr3_dqs_p / ddr3_dqs_n are inout — tristated by default

    // ------------------------------------------------------------------ //
    // 6. SPU-13 Cortex core                                               //
    // ------------------------------------------------------------------ //
    wire [12:0] manifold_P, manifold_Q;
    wire        janus_point;
    wire [15:0] mem_rd_data = 16'h0;   // DDR3 read data (stub)

    spu13_core #(
        .DEVICE("GW2A")
    ) u_spu13 (
        .clk            (clk_fast),
        .reset          (sys_reset),
        .heartbeat      (heartbeat),
        .bloom_intensity(bloom_intensity),
        .mem_ready      (mem_ready),
        .mem_rd_data    (mem_rd_data),
        .manifold_P     (manifold_P),
        .manifold_Q     (manifold_Q),
        .janus_point    (janus_point)
    );

    // ------------------------------------------------------------------ //
    // 7. Whisper TX (PWI telemetry → RP2350)                              //
    // ------------------------------------------------------------------ //
    SPU_WHISPER_TX u_whisper (
        .clk        (clk_fast),
        .reset      (sys_reset),
        .heartbeat  (heartbeat),
        .manifold_P (manifold_P[0]),
        .manifold_Q (manifold_Q[0]),
        .whisper_out(whisper_tx)
    );

    // ------------------------------------------------------------------ //
    // 8. UART loopback placeholder (RP2350 bridge)                        //
    // ------------------------------------------------------------------ //
    assign uart_tx = uart_rx;   // loopback until full bridge wired

    // ------------------------------------------------------------------ //
    // 9. HDMI stub — outputs low until HAL_Cartesian driver added         //
    // ------------------------------------------------------------------ //
    assign hdmi_clk_p = 1'b0;
    assign hdmi_clk_n = 1'b1;
    assign hdmi_d_p   = 3'b000;
    assign hdmi_d_n   = 3'b111;

    // ------------------------------------------------------------------ //
    // 10. LED status indicators (active-low)                              //
    // ------------------------------------------------------------------ //
    wire whisper_active;
    reg  [19:0] whisper_stretch;

    always @(posedge clk_fast)
        if (whisper_tx) whisper_stretch <= 20'hFFFFF;
        else if (|whisper_stretch) whisper_stretch <= whisper_stretch - 1;

    assign whisper_active = |whisper_stretch;

    assign led[0] = !pll_lock;
    assign led[1] = !janus_point;
    assign led[2] = !bloom_complete;
    assign led[3] = 1'b1;            // DDR3 init: always-off until bridge live
    assign led[4] = !whisper_active;

endmodule
