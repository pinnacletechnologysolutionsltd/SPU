// spu_icesugar_top.v (v2.0 - SPU-4 Sentinel)
// Target: iCEsugar v1.5 (iCE40UP5K-SG48)
// Architecture: Phi-Gated Clock -> SPU-4 Sentinel -> Artery/Whisper TX
// The SPU-13 full core exceeds UP5K capacity; the SPU-4 Sentinel is the
// correct deployment for this tier (see HARDWARE_MANIFEST_SPU13.md).

`include "spu_arch_defines.vh"

module spu_icesugar_top (
    input  wire clk,                // 12 MHz onboard oscillator

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

    // Artery nerve output (PMOD2 pin 2) for RP2040 inhalation
    output wire NERVE_MOSI,

    // Sovereign heartbeat (PMOD2 pin 1)
    output wire sovereign_heartbeat
);

    // --- 1. Phi-Gated Clock ---
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

    // --- 2. Ghost Boot ---
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
        .ext_spi_miso(psram_dq[1]),
        .boot_done(boot_done),
        .prime_addr(p_addr),
        .prime_data(p_data),
        .prime_we(p_we)
    );

    // --- 3. QSPI Memory Bridge ---
    // CE/CLK muxed between boot SPI and bridge; DQ fully owned by psram_ctrl
    // (holds hi-Z during reset=1 i.e. while boot is in progress).
    wire mem_ready, mem_burst_rd, mem_burst_wr, mem_burst_done;
    wire [`MEM_ADDR_WIDTH-1:0] mem_addr;
    wire [`MANIFOLD_WIDTH-1:0] mem_rd_manifold, mem_wr_manifold;
    wire core_ce_n, core_clk;

    assign psram_ce_n = !boot_done ? boot_cs_n : core_ce_n;
    assign psram_clk  = !boot_done ? boot_sck  : core_clk;

    spu_mem_bridge_qspi u_mem (
        .clk(clk),
        .reset(!boot_done),
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

    // --- 4. SPU-4 Sentinel Core ---
    // Seeded with unit Quadray (1,0,0,0) — IVM identity axis.
    wire [15:0] A_out, B_out, C_out, D_out;
    wire        janus_stable, henosis_pulse;

    spu4_sentinel u_sentinel (
        .clk(clk),
        .rst_n(boot_done),
        .heartbeat(phi_heart),
        .A_seed(16'h1000), .B_seed(16'h0),   // (1.0, 0, 0, 0) in Q12
        .C_seed(16'h0),    .D_seed(16'h0),
        .rot_mode(2'b01),                      // 60° IVM rotation
        .A_out(A_out), .B_out(B_out),
        .C_out(C_out), .D_out(D_out),
        .quadrance(),
        .quadrance_seed(),
        .janus_stable(janus_stable),
        .heartbeat_count(),
        .test_pass(),
        .henosis_pulse(henosis_pulse)
    );

    // Wire sentinel manifold into the memory bus (packed into MANIFOLD_WIDTH)
    // Remaining manifold bits tied to zero for SPU-4 tier.
    assign mem_burst_rd  = 1'b0;
    assign mem_burst_wr  = 1'b0;
    assign mem_addr      = {`MEM_ADDR_WIDTH{1'b0}};
    assign mem_wr_manifold = {{`MANIFOLD_WIDTH-64{1'b0}}, A_out, B_out, C_out, D_out};

    // --- 5. Artery TX (Whisper) ---
    wire [3:0]  artery_axis_ptr;
    wire [63:0] artery_axis_data;

    // Drive axis pointer from Pell heartbeat count (cycles through 13 axes)
    assign artery_axis_ptr  = 4'd0;
    assign artery_axis_data = {A_out, B_out, C_out, D_out};

    spu_artery_tx u_artery (
        .clk(clk),
        .phi_21(phi_21),
        .axis_ptr(artery_axis_ptr),
        .axis_data(artery_axis_data),
        .tx_out(NERVE_MOSI),
        .tx_active()
    );

    // --- 6. Status LEDs ---
    assign LED_B = !boot_done;      // Blue:  booting
    assign LED_G = janus_stable;    // Green: sovereign stability
    assign LED_R = henosis_pulse;   // Red:   Henosis fired (manifold drift)

    assign uart_tx = janus_stable ^ phi_heart;

endmodule

