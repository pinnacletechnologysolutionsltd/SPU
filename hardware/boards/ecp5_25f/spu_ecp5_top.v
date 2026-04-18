// spu_ecp5_top.v — Generic Lattice ECP5 Sovereign Cluster Top
// Target: Lattice ECP5 (LFE5U-12F/25F/45F/85F)
// Compatible with: iCESugar-Pro, Colorlight i5/i9, OrangeCrab, ULX3S
// Architecture: 1x SPU-13 Mother + 8x SPU-4 Sentinels (Sovereign Cluster)

`include "spu_arch_defines.vh"

module spu_ecp5_top (
    input  wire clk_25,            // Primary clock input (25MHz from PHY1)
    input  wire rst_n,             // Primary reset (active-low)

    output wire led_heartbeat,     // DATA_LED-
    output wire uart_tx,           // Telemetry Mirror

    // Artery Artery PIO (Ghost OS Domain)
    input  wire        artery_wr_en,
    input  wire [63:0] artery_wr_data,

    output wire        spi_miso,
    
    // JTAG Header (Repurposed as Industrial Inputs)
    input  wire        jtag_tck,
    input  wire        jtag_tms,
    input  wire        jtag_tdi,
    output wire        jtag_tdo,

    // SD Card Interface (on JTAG Header)
    output wire        sd_cs,
    output wire        sd_sck,
    output wire        sd_mosi,
    input  wire        sd_miso,

    // HUB75 Industrial Gateway Interface
    output wire        hub_clk, hub_lat, hub_oe,
    output wire        hub_a, hub_b, hub_c, hub_d, hub_e,
    output wire [5:0]  hub_j1, hub_j2, hub_j3, hub_j4,
    output wire [5:0]  hub_j5, hub_j6, hub_j7, hub_j8,

    // Onboard SPI Flash (via USRMCLK)
    output wire        flash_cs_n,
    output wire        flash_mosi,
    input  wire        flash_miso,

    // Onboard SDRAM (32-bit)
    output wire        sdram_clk,
    output wire        sdram_ras_n,
    output wire        sdram_cas_n,
    output wire        sdram_we_n,
    output wire [1:0]  sdram_ba,
    output wire [10:0] sdram_addr,
    inout  wire [31:0] sdram_dq,

    output wire        whisper_tx     // Legacy 1-wire telemetry
);

    // --- 1. Clock Management (PLL) ---
    // Generate 100 MHz for SDRAM and System from 25 MHz input
    wire clk_100;
    wire pll_lock;
    
    // ECP5 EHXPLLL Instance for 25MHz -> 100MHz
    EHXPLLL #(
        .PLLRST_ENA("DISABLED"),
        .INTFB_WAKE("DISABLED"),
        .STDBY_ENABLE("DISABLED"),
        .DPHASE_SOURCE("DISABLED"),
        .OUTDIVIDER_MUXA("DIVA"),
        .OUTDIVIDER_MUXB("DIVB"),
        .OUTDIVIDER_MUXC("DIVC"),
        .OUTDIVIDER_MUXD("DIVD"),
        .CLKI_DIV(1),
        .CLKOP_ENABLE("ENABLED"),
        .CLKOP_DIV(6),
        .CLKOP_CPHASE(2),
        .CLKOP_FPHASE(0),
        .FEEDBK_PATH("CLKOP"),
        .CLKFB_DIV(4)
    ) u_pll (
        .RST(1'b0),
        .STDBY(1'b0),
        .CLKI(clk_25),
        .CLKOP(clk_100),
        .CLKFB(clk_100),
        .CLKINTFB(),
        .PHASESEL0(1'b0),
        .PHASESEL1(1'b0),
        .PHASEDIR(1'b1),
        .PHASESTEP(1'b1),
        .PHASELOADREG(1'b1),
        .PLLWAKESYNC(1'b0),
        .ENCLKOP(1'b0),
        .LOCK(pll_lock)
    );

    wire clk_ghost = clk_100;
    wire clk_fast  = clk_100; // SPU core now running at 100 MHz
    wire clk_piranha;

    spu_sierpinski_clk u_clk_div (
        .clk(clk_fast),
        .rst_n(rst_n & pll_lock),
        .phi_8(), .phi_13(), .phi_21(),
        .heartbeat(clk_piranha)
    );

    // --- 2. 32-bit SDRAM Controller ---
    wire        mem_rd_en;
    wire        mem_wr_en;
    wire [23:0] mem_addr;
    wire [31:0] mem_wr_data;
    wire [31:0] mem_rd_data;
    wire        mem_ready;
    wire        mem_rd_valid;

    spu_sdram_ctrl_32bit u_sdram (
        .clk(clk_100),
        .rst_n(rst_n & pll_lock),
        .rd_en(mem_rd_en),
        .wr_en(mem_wr_en),
        .addr(mem_addr),
        .wr_data(mem_wr_data),
        .rd_data(mem_rd_data),
        .ready(mem_ready),
        .rd_valid(mem_rd_valid),
        .sdram_clk(sdram_clk),
        .sdram_ras_n(sdram_ras_n),
        .sdram_cas_n(sdram_cas_n),
        .sdram_we_n(sdram_we_n),
        .sdram_ba(sdram_ba),
        .sdram_addr(sdram_addr),
        .sdram_dq(sdram_dq)
    );

    // --- 3. Sovereign System Orchestrator ---
    wire [831:0] manifold_state;
    wire [7:0]   satellite_snaps;
    wire         is_janus_point;
    wire         turbulence_alert;

    spu_system u_cluster (
        .clk_ghost(clk_ghost),
        .clk_piranha(clk_piranha),
        .clk_fast(clk_fast),
        .rst_n(rst_n & pll_lock),
        
        .wr_en(artery_wr_en),
        .wr_data(artery_wr_data),
        .fifo_full(),

        // Internal ROMs (via USRMCLK Bridge)
        .pmod_sclk(), // Handled by USRMCLK in bridge
        .pmod_cs_n(flash_cs_n),
        .pmod_mosi(flash_mosi),
        .pmod_miso(flash_miso),

        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),

        .manifold_state(manifold_state),
        .satellite_snaps(satellite_snaps),
        .is_janus_point(is_janus_point),

        .i2s_bclk(i2s_bclk),
        .i2s_lrclk(i2s_lrclk),
        .i2s_dout(i2s_dout),

        .turbulence_alert(turbulence_alert),

        .sd_cs(sd_cs),
        .sd_sck(sd_sck),
        .sd_mosi(sd_mosi),
        .sd_miso(sd_miso),

        .industrial_inputs({jtag_tck, jtag_tms, jtag_tdi, 1'b0}), // TDO is output
        .industrial_io({hub_j8, hub_j7, hub_j6, hub_j5, hub_j4, hub_j3, hub_j2, hub_j1, 
                        hub_e, hub_d, hub_c, hub_b, hub_a, hub_oe, hub_lat, hub_clk})
    );

    // --- 4. I/O Mapping & Status ---
    assign led_heartbeat = !clk_piranha; // Blink LED with piranha pulse
    assign uart_tx = ^manifold_state;
    assign whisper_tx = ^satellite_snaps;

endmodule
