// tang_nano_9k_top.v (v2.0 — Dual-Mode: Standalone + Satellite/Auxiliary)
// Target:  Gowin GW1N-9C  (Tang Nano 9K)
// Crystal: 27 MHz onboard
//
// Resource budget (GW1N-9C):
//   LUTs  : 8640    FFs: 6480    BSRAM: 26×18 Kb    DSPs: 20
//   SPU-4 core uses 16 DSPs → fits with 4 spare.
//   SPU-13 Cortex requires 52 DSPs → does NOT fit this device;
//   use Tang Primer 20K (GW2A-18, 50 DSPs) or Tang Primer 25K (GW5A-25).
//
// Memory:
//   PSRAM Bank 0: managed internally by spu4_core (APS6404L, 8 MB).
//   PSRAM Bank 1: secondary controller for auxiliary state / DMA overflow.
//   Both chips on independent QSPI buses (see tang_nano_9k.cst).
//
// Operating modes (mode_pin, sampled continuously):
//   0 = Standalone  — spu4_core runs autonomously; Whisper TX emits A_out.
//   1 = Satellite   — spu4_core substrate + spu_4_satellite active-inference
//                     kernel; Whisper RX decodes mother's prime anchor;
//                     Whisper TX reports satellite dissonance back up.
//
// CC0 1.0 Universal.

module tang_nano_9k_top (
    input  wire       clk_27mhz,

    // User LEDs (active-low on Tang Nano 9K)
    output wire [5:0] led_n,

    // Mode select: 0 = standalone, 1 = satellite/auxiliary
    input  wire       mode_pin,

    // Whisper serial (PWI)
    output wire       whisper_tx,   // outbound telemetry (always active)
    input  wire       whisper_rx,   // inbound anchor from mother (satellite mode)

    // PSRAM Bank 0 — driven by spu4_core directly
    output wire       psram0_ce_n,
    output wire       psram0_clk,
    inout  wire [3:0] psram0_dq,

    // PSRAM Bank 1 — secondary controller
    output wire       psram1_ce_n,
    output wire       psram1_clk,
    inout  wire [3:0] psram1_dq
);

    // ------------------------------------------------------------------ //
    // 1. Clock: 27 MHz → 24 MHz via Gowin rPLL                           //
    // ------------------------------------------------------------------ //
    wire clk_spu;
    wire clk_locked;

    rPLL #(
        .FCLKIN    ("27"),
        .IDIV_SEL  (8),      // ÷9 → 3 MHz
        .FBDIV_SEL (7),      // ×8 → 24 MHz
        .ODIV_SEL  (8),
        .DEVICE    ("GW1N-9C")
    ) u_pll (
        .CLKIN  (clk_27mhz),
        .CLKOUT (clk_spu),
        .LOCK   (clk_locked),
        .RESET  (1'b0), .RESET_P(1'b0),
        .FBDSEL (6'b0),  .IDSEL(6'b0),  .ODSEL(6'b0),
        .PSDA   (4'b0),  .DUTYDA(4'b0), .FDLY(4'b0)
    );

    wire rst_n = clk_locked;
    wire reset = ~clk_locked;

    // ------------------------------------------------------------------ //
    // 2. Fibonacci heartbeat (61.44 kHz Piranha Pulse)                   //
    // ------------------------------------------------------------------ //
    wire heartbeat;

    spu_sierpinski_clk u_sierpinski (
        .clk       (clk_spu),
        .rst_n     (rst_n),
        .phi_8     (),
        .phi_13    (),
        .phi_21    (),
        .heartbeat (heartbeat)
    );

    // ------------------------------------------------------------------ //
    // 3. SPU-4 Core (manages PSRAM Bank 0 internally)                    //
    // ------------------------------------------------------------------ //
    // In satellite mode the decoded anchor drives A_in so the core's
    // manifold is biased toward the mother's prime geometry.
    wire [15:0] anchor_decoded;

    wire [15:0] A_out, B_out, C_out, D_out;
    wire        bloom_complete;

    spu4_core u_spu4 (
        .clk             (clk_spu),
        .reset           (reset),

        // SPI boot interface — unused on 9K standalone
        .spi_cs_n        (),
        .spi_sck         (),
        .spi_mosi        (),
        .spi_miso        (1'b0),

        // Aux programming — unused
        .prog_en_aux     (1'b0),
        .prog_addr_aux   (4'h0),
        .prog_data_aux   (16'h0),
        .mode_autonomous (1'b1),

        // Quadray inputs: in satellite mode feed anchor on A axis
        .A_in            (mode_pin ? anchor_decoded : 16'h0),
        .B_in            (16'h0),
        .C_in            (16'h0),
        .D_in            (16'h0),

        // Rotor: geometric identity
        .F_rat           (16'h0100),
        .G_rat           (16'h0000),
        .H_rat           (16'h0000),

        // SovereignBus — unused at top level
        .bus_addr        (),
        .bus_wen         (),
        .bus_ren         (),
        .bus_ready       (1'b1),

        // PSRAM Bank 0 (core-managed)
        .psram_ce_n      (psram0_ce_n),
        .psram_clk       (psram0_clk),
        .psram_dq        (psram0_dq),

        // Quadray outputs
        .A_out           (A_out),
        .B_out           (B_out),
        .C_out           (C_out),
        .D_out           (D_out),
        .bloom_complete  (bloom_complete)
    );

    // ------------------------------------------------------------------ //
    // 4. PSRAM Bank 1 — secondary storage / satellite state log          //
    // ------------------------------------------------------------------ //
    wire psram1_init_done;

    spu_psram_ctrl u_psram1 (
        .clk              (clk_spu),
        .reset            (reset),
        .rd_en            (1'b0),
        .wr_en            (1'b0),
        .addr             (23'h0),
        .wr_data          (16'h0),
        .rd_data          (),
        .ready            (),
        .init_done        (psram1_init_done),
        .burst_rd         (1'b0),
        .burst_wr         (1'b0),
        .manifold_wr_data (832'h0),
        .manifold_rd_data (),
        .burst_done       (),
        .psram_ce_n       (psram1_ce_n),
        .psram_clk        (psram1_clk),
        .psram_dq         (psram1_dq)
    );

    // ------------------------------------------------------------------ //
    // 5. Whisper RX — decodes mother's prime anchor (satellite mode)     //
    // ------------------------------------------------------------------ //
    wire anchor_ready;

    SPU_WHISPER_RX #(.BIAS(16'd0)) u_whisper_rx (
        .clk      (clk_spu),
        .rst_n    (rst_n),
        .pwi_in   (whisper_rx),
        .is_cal   (1'b0),
        .surd_a   (anchor_decoded),
        .surd_b   (),
        .rx_ready (anchor_ready)
    );

    // ------------------------------------------------------------------ //
    // 6. Satellite inference kernel (active when mode_pin=1)             //
    //    A_out from spu4_core = "local reality"; anchor = mother guide   //
    // ------------------------------------------------------------------ //
    wire [7:0] dissonance;
    wire       snap_alert;

    spu_4_satellite u_satellite (
        .clk        (clk_spu),
        .rst_n      (rst_n & mode_pin),
        .anchor_in  (anchor_decoded),
        .sensor_in  (A_out),
        .dissonance (dissonance),
        .snap_alert (snap_alert)
    );

    // ------------------------------------------------------------------ //
    // 7. Node link — packs dissonance frame for uplink (satellite mode)  //
    // ------------------------------------------------------------------ //
    wire [31:0] node_tx;
    wire        sync_alert;

    spu_node_link u_node_link (
        .clk                  (clk_spu),
        .rst_n                (rst_n & mode_pin),
        .prime_anchor_in      ({anchor_decoded, 8'h0}),
        .rx_frame             ({snap_alert, dissonance, 7'h0}),
        .tx_frame             (node_tx),
        .sync_alert           (sync_alert),
        .satellite_dissonance ()
    );

    // ------------------------------------------------------------------ //
    // 8. Whisper TX                                                       //
    //    Standalone: emit A_out (primary manifold axis)                  //
    //    Satellite:  emit node status (top 16 bits of node_tx frame)     //
    // ------------------------------------------------------------------ //
    wire [15:0] whisper_surd_a = mode_pin ? node_tx[31:16] : A_out;

    SPU_WHISPER_TX u_whisper_tx (
        .clk      (clk_spu),
        .rst_n    (rst_n),
        .trig_en  (heartbeat),
        .is_sync  (1'b0),
        .surd_a   (whisper_surd_a),
        .surd_b   (16'h0),
        .pwi_out  (whisper_tx),
        .tx_ready ()
    );

    // ------------------------------------------------------------------ //
    // 9. Status LEDs (active-low)                                         //
    // ------------------------------------------------------------------ //
    assign led_n[0] = ~psram1_init_done;         // Bank 1 PSRAM ready
    assign led_n[1] = ~bloom_complete;           // Manifold bloom
    assign led_n[2] = ~snap_alert;               // Satellite snap
    assign led_n[3] = ~clk_locked;              // PLL locked
    assign led_n[4] = ~mode_pin;                 // Satellite mode active
    assign led_n[5] = mode_pin ? ~sync_alert     // Sync loss (satellite)
                               : ~anchor_ready;  // RX frame received

endmodule
