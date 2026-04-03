// spu_icesugar_top.v (v1.6 - Sovereign Handover)
// Target: iCEsugar (iCE40UP5K-SG48)
// Architecture: Phi-Gated Boot -> SQR Sovereign Operation.

`include "spu_arch_defines.vh"

module spu_icesugar_top (
    input  wire clk, // 12 MHz onboard
    
    // Onboard RGB LED
    output wire LED_R,
    output wire LED_G,
    output wire LED_B,

    // PSRAM QSPI Interface (PMOD1)
    output wire psram_ce_n,
    output wire psram_clk,
    inout  wire [3:0] psram_dq,

    // UART Telemetry (via Type-C Debugger)
    output wire uart_tx,
    input  wire uart_rx,

    // Heartbeat Monitor (for RP2040)
    output wire sovereign_heartbeat
);

    // --- 1. Clock Generation ---
    wire phi_8, phi_13, phi_21, phi_heart;
    spu_sierpinski_clk u_phi (
        .clk(clk),
        .rst_n(1'b1),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    assign sovereign_heartbeat = phi_heart;

    // --- 2. Phi-Gated Ghost Bootloader ---
    wire boot_done;
    wire boot_cs_n, boot_sck, boot_mosi;
    wire [3:0]  p_addr;
    wire [23:0] p_data;
    wire        p_we;

    spu_ghost_boot u_boot (
        .clk(clk),
        .rst_n(1'b1),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),
        .ext_spi_cs_n(boot_cs_n),
        .ext_spi_sck(boot_sck),
        .ext_spi_mosi(boot_mosi),
        .ext_spi_miso(psram_dq[1]), // Shared MISO on DQ1
        .boot_done(boot_done),
        .prime_addr(p_addr),
        .prime_data(p_data),
        .prime_we(p_we)
    );

    // --- 3. Sovereign Memory Bridge (QSPI) ---
    wire                   mem_ready;
    wire                   mem_burst_rd;
    wire                   mem_burst_wr;
    wire [`MEM_ADDR_WIDTH-1:0] mem_addr;
    wire [`MANIFOLD_WIDTH-1:0] mem_rd_manifold;
    wire [`MANIFOLD_WIDTH-1:0] mem_wr_manifold;
    wire                   mem_burst_done;

    wire core_ce_n, core_clk;
    wire [3:0] core_dq_out;
    wire core_dq_oe;

    spu_mem_bridge_qspi u_mem (
        .clk(clk),
        .reset(!boot_done), // Hold bridge in reset until boot finish
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),
        .psram_ce_n(core_ce_n),
        .psram_clk(core_clk),
        .psram_dq(psram_dq)
    );

    // --- 4. Sovereign Bus Handover Mux ---
    // Note: During boot, we use DQ0/DQ1 for standard SPI.
    // After boot, the QSPI bridge takes over.
    assign psram_ce_n = !boot_done ? boot_cs_n : core_ce_n;
    assign psram_clk  = !boot_done ? boot_sck  : core_clk;
    
    // During boot, DQ0 is MOSI. Bridge handles DQ mapping after.
    // This is a simplified mux; spu_mem_bridge_qspi owns psram_dq when !reset.
    // We only need to ensure boot_mosi drives DQ0 when !boot_done.
    // Using a primitive or simple tri-state:
    assign psram_dq[0] = !boot_done ? boot_mosi : 1'bz;

    // --- 5. SPU-13 Sovereign Core ---
    wire is_janus_point;
    wire bloom_complete;
    wire [3:0]  artery_axis_ptr;
    wire [63:0] artery_axis_data;

    spu13_core u_core (
        .clk(clk),
        .rst_n(boot_done), // Awake only after hydration
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),
        
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),

        .current_axis_ptr(artery_axis_ptr),
        .current_axis_data(artery_axis_data),
        .manifold_out(),
        .bloom_complete(bloom_complete),
        .is_janus_point(is_janus_point)
    );

    // --- 6. Artery Link (Whisper Protocol) ---
    // Wired to PMOD P2-2 (NERVE_MOSI) for RP2040 Inhalation
    wire artery_tx_active;
    spu_artery_tx u_artery (
        .clk(clk),
        .phi_21(phi_21),
        .axis_ptr(artery_axis_ptr),
        .axis_data(artery_axis_data),
        .tx_out(NERVE_MOSI),
        .tx_active(artery_tx_active)
    );

    // --- 7. Physical Status (LEDs) ---

    assign LED_B = !boot_done;      // Blue: Booting
    assign LED_G = is_janus_point; // Green: Sovereign Stability
    assign LED_R = !mem_ready;     // Red: Memory Dissonance

    assign uart_tx = is_janus_point ^ phi_heart;

endmodule
