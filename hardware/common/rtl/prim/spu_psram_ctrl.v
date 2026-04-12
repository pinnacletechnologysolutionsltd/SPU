// Minimal PSRAM controller stub used for synthesis/triage
`timescale 1ns / 1ps
module spu_psram_ctrl (
    input  wire         clk,
    input  wire         reset,
    input  wire         rd_en,
    input  wire         wr_en,
    input  wire [22:0]  addr,
    input  wire [15:0]  wr_data,
    output reg  [15:0]  rd_data,
    output wire         ready,
    output wire         init_done,
    // Burst/manifold interface (simulation-friendly)
    input  wire         burst_rd,
    input  wire         burst_wr,
    input  wire [831:0] manifold_wr_data,
    output reg  [831:0] manifold_rd_data,
    output wire         burst_done,
    output wire         psram_ce_n,
    output wire         psram_clk,
    inout  wire [3:0]   psram_dq
);

assign ready = 1'b1;       // always ready in stub
assign init_done = 1'b1;   // pretend init completed
assign psram_ce_n = 1'b1;  // inactive
assign psram_clk = clk;    // mirror clock for safety

// Tri-state bus on stub
assign psram_dq = 4'bz;

always @(posedge clk or posedge reset) begin
    if (reset) rd_data <= 16'h0000;
    else rd_data <= 16'h0000;
end

endmodule
