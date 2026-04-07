// spu_sdram_arbiter.v — Dual-core SDRAM priority arbiter (v1.0)
// CC0 1.0 Universal.
//
// Arbitrates one physical SDRAM port between two SPU-13 cortex cores.
// Bank partition: core 0 → banks 0-1 (addr bit 23 forced 0)
//                core 1 → banks 2-3 (addr bit 23 forced 1)
// Priority: core 0 > core 1.
//
// Protocol contract (matches spu13_core hydration FSM):
//   • Core holds mem_burst_rd/wr HIGH until it sees mem_burst_done.
//   • Core only asserts when it has seen mem_ready=1.
//   • SDRAM bridge deasserts mem_ready while a burst is in flight,
//     so grant is naturally stable between arbitration points.
//
// Arbitration cycle:
//   1. When sdram_ready=1 and core N requests: registered grant → N.
//   2. One-cycle delay before SDRAM sees the muxed request (acceptable
//      at Fibonacci phi_8 rates, many orders slower than clk_fast).
//   3. c0_done / c1_done are gated by grant so only the active core
//      sees burst_done and exits its INHALE/EXHALE state.

`include "spu_arch_defines.vh"

module spu_sdram_arbiter (
    input  wire clk,
    input  wire rst_n,

    // Core 0 interface
    output wire                       c0_mem_ready,
    input  wire                       c0_mem_burst_rd,
    input  wire                       c0_mem_burst_wr,
    input  wire [`MEM_ADDR_WIDTH-1:0] c0_mem_addr,
    output wire [`MANIFOLD_WIDTH-1:0] c0_mem_rd_manifold,
    input  wire [`MANIFOLD_WIDTH-1:0] c0_mem_wr_manifold,
    output wire                       c0_mem_burst_done,

    // Core 1 interface
    output wire                       c1_mem_ready,
    input  wire                       c1_mem_burst_rd,
    input  wire                       c1_mem_burst_wr,
    input  wire [`MEM_ADDR_WIDTH-1:0] c1_mem_addr,
    output wire [`MANIFOLD_WIDTH-1:0] c1_mem_rd_manifold,
    input  wire [`MANIFOLD_WIDTH-1:0] c1_mem_wr_manifold,
    output wire                       c1_mem_burst_done,

    // SDRAM controller (single physical port)
    input  wire                       sdram_mem_ready,
    output wire                       sdram_mem_burst_rd,
    output wire                       sdram_mem_burst_wr,
    output wire [`MEM_ADDR_WIDTH-1:0] sdram_mem_addr,
    input  wire [`MANIFOLD_WIDTH-1:0] sdram_mem_rd_manifold,
    output wire [`MANIFOLD_WIDTH-1:0] sdram_mem_wr_manifold,
    input  wire                       sdram_mem_burst_done
);

    // ------------------------------------------------------------------ //
    // Grant register: 0 = core 0, 1 = core 1.                            //
    // Updated only when SDRAM is idle (sdram_mem_ready=1) so the grant   //
    // is locked for the full duration of any in-flight burst.            //
    // ------------------------------------------------------------------ //
    reg grant;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            grant <= 1'b0;
        else if (sdram_mem_ready) begin
            if      (c0_mem_burst_rd | c0_mem_burst_wr) grant <= 1'b0;
            else if (c1_mem_burst_rd | c1_mem_burst_wr) grant <= 1'b1;
        end
    end

    // ------------------------------------------------------------------ //
    // Bank-forced addresses.                                              //
    // MEM_ADDR_WIDTH is 24: addr[23:22] = bank[1:0].                    //
    // Core 0 → bank bit 23 forced 0 (banks 0-1, lower 16 MB).           //
    // Core 1 → bank bit 23 forced 1 (banks 2-3, upper 16 MB).           //
    // ------------------------------------------------------------------ //
    wire [`MEM_ADDR_WIDTH-1:0] c0_banked = {1'b0, c0_mem_addr[`MEM_ADDR_WIDTH-2:0]};
    wire [`MEM_ADDR_WIDTH-1:0] c1_banked = {1'b1, c1_mem_addr[`MEM_ADDR_WIDTH-2:0]};

    // ------------------------------------------------------------------ //
    // Mux: forward granted core's signals to SDRAM controller.           //
    // ------------------------------------------------------------------ //
    assign sdram_mem_burst_rd  = grant ? c1_mem_burst_rd  : c0_mem_burst_rd;
    assign sdram_mem_burst_wr  = grant ? c1_mem_burst_wr  : c0_mem_burst_wr;
    assign sdram_mem_addr      = grant ? c1_banked        : c0_banked;
    assign sdram_mem_wr_manifold = grant ? c1_mem_wr_manifold : c0_mem_wr_manifold;

    // ------------------------------------------------------------------ //
    // Read data: broadcast to both (only the granted core acts on it).   //
    // Done: routed only to granted core so only it exits INHALE/EXHALE.  //
    // ------------------------------------------------------------------ //
    assign c0_mem_rd_manifold = sdram_mem_rd_manifold;
    assign c1_mem_rd_manifold = sdram_mem_rd_manifold;

    assign c0_mem_burst_done = sdram_mem_burst_done & ~grant;
    assign c1_mem_burst_done = sdram_mem_burst_done &  grant;

    // ------------------------------------------------------------------ //
    // Ready: core 0 always sees SDRAM idle; core 1 yields to core 0.    //
    // ------------------------------------------------------------------ //
    assign c0_mem_ready = sdram_mem_ready;
    assign c1_mem_ready = sdram_mem_ready & ~(c0_mem_burst_rd | c0_mem_burst_wr);

endmodule
