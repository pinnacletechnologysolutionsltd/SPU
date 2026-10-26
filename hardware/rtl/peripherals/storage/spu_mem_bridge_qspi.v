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

    // Simulation-friendly bridge: tie off burst interface and simple passthrough
    assign mem_ready = 1'b1;
    assign mem_rd_manifold = {`MANIFOLD_WIDTH{1'b0}};
    assign mem_burst_done = 1'b0;
    assign psram_ce_n = 1'b1;
    assign psram_clk = clk;
    // Leave psram_dq as high-Z for simulation
    assign psram_dq = {4{1'bz}};

endmodule
