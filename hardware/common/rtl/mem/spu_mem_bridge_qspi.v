// spu_mem_bridge_qspi.v (v1.1 - Sovereign-to-QSPI Bridge)
// Objective: Adapt the Sovereign Manifold Bus to the Burst QSPI PSRAM controller.

`include "spu_arch_defines.vh"

module spu_mem_bridge_qspi (
    input  wire         clk,
    input  wire         reset,

    // --- Sovereign Manifold Bus ---
    output wire                   mem_ready,
    input  wire                   mem_burst_rd,
    input  wire                   mem_burst_wr,
    input  wire [`MEM_ADDR_WIDTH-1:0] mem_addr,
    output wire [`MANIFOLD_WIDTH-1:0] mem_rd_manifold,
    input  wire [`MANIFOLD_WIDTH-1:0] mem_wr_manifold,
    output wire                   mem_burst_done,

    // --- Physical PSRAM Pins ---
    output wire          psram_ce_n,
    output wire          psram_clk,
    inout  wire [3:0]    psram_dq
);

    // Instantiate the physical QSPI PSRAM controller
    spu_psram_ctrl u_phy (
        .clk(clk),
        .reset(reset),
        
        // Single-word interface (unused in this bridge)
        .rd_en(1'b0),
        .wr_en(1'b0),
        .addr(mem_addr[22:0]),
        .wr_data(16'h0),
        .rd_data(),
        .ready(mem_ready),
        .init_done(),

        // Burst Interface
        .burst_rd(mem_burst_rd),
        .burst_wr(mem_burst_wr),
        .manifold_wr_data(mem_wr_manifold),
        .manifold_rd_data(mem_rd_manifold),
        .burst_done(mem_burst_done),

        // Pins
        .psram_ce_n(psram_ce_n),
        .psram_clk(psram_clk),
        .psram_dq(psram_dq)
    );

endmodule
