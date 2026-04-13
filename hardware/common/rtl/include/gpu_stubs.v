// GPU-related stubs trimmed: rational_sine_rom and rational_sine_rom_q32 are provided by
// hardware/common/rtl/gpu/rational_sine_rom.v and hardware/common/rtl/gpu/rational_sine_rom_q32.v
`timescale 1ns/1ps

// retain DDR3 bridge stub for triage
module spu_mem_bridge_ddr3(
    input  wire clk,
    input  wire reset,
    output wire mem_ready,
    output wire mem_burst_rd,
    output wire mem_burst_wr,
    output wire [31:0] mem_addr,
    output wire [831:0] mem_rd_manifold,
    output wire [831:0] mem_wr_manifold,
    output wire mem_burst_done,
    output wire ddr3_ck_p,
    output wire ddr3_ck_n,
    output wire ddr3_cke,
    output wire ddr3_cs_n,
    output wire ddr3_ras_n,
    output wire ddr3_cas_n,
    output wire ddr3_we_n,
    output wire ddr3_odt,
    output wire ddr3_reset_n,
    output wire [2:0] ddr3_ba,
    output wire [13:0] ddr3_addr,
    inout  wire [15:0] ddr3_dq,
    inout  wire [1:0]  ddr3_dqs_p,
    inout  wire [1:0]  ddr3_dqs_n,
    output wire [1:0]  ddr3_dm
);
    assign mem_ready = 1'b1;
    assign mem_burst_rd = 1'b0;
    assign mem_burst_wr = 1'b0;
    assign mem_addr = 32'h0;
    assign mem_rd_manifold = {832{1'b0}};
    assign mem_wr_manifold = {832{1'b0}};
    assign mem_burst_done = 1'b0;
    assign ddr3_ck_p = 1'b0; assign ddr3_ck_n = 1'b1;
    assign ddr3_cke = 1'b0; assign ddr3_cs_n = 1'b1;
    assign ddr3_ras_n = 1'b1; assign ddr3_cas_n = 1'b1; assign ddr3_we_n = 1'b1;
    assign ddr3_odt = 1'b0; assign ddr3_reset_n = 1'b1;
    assign ddr3_ba = 3'b000; assign ddr3_addr = 14'h0; assign ddr3_dm = 2'b00;
endmodule
