`timescale 1ns / 1ps

// spu13_multi_port_regfile.v — 4-Read, 2-Write Multi-Port Register File
//
// Dual-cluster architecture: ALU Cluster Alpha (streaming) and
// ALU Cluster Beta (Conjugate Reduction Tower, F_{p^4} inversion).
//
// Each cluster gets 2 read ports + 1 write port. R0 is hardwired to zero.
// Combinational write-forwarding bypass prevents stale reads when one
// cluster writes and the other reads the same register in the same cycle.
//
// Optimised for FPGA: 16 × 32-bit registers, async reads via LUT mux trees,
// priority-arbitrated synchronous writes, no BRAM (fits in distributed RAM).

module spu13_multi_port_regfile (
    input wire         clk,
    input wire         rst_n,

    // ── ALU Cluster Alpha (Streaming operations) ───────────────────
    input  wire [3:0]  alpha_srcA_addr,
    input  wire [3:0]  alpha_srcB_addr,
    output wire [31:0] alpha_srcA_data,
    output wire [31:0] alpha_srcB_data,
    input  wire [3:0]  alpha_dest_addr,
    input  wire [31:0] alpha_dest_data,
    input  wire        alpha_write_en,

    // ── ALU Cluster Beta (Inversion tower) ─────────────────────────
    input  wire [3:0]  beta_srcA_addr,
    input  wire [3:0]  beta_srcB_addr,
    output wire [31:0] beta_srcA_data,
    output wire [31:0] beta_srcB_data,
    input  wire [3:0]  beta_dest_addr,
    input  wire [31:0] beta_dest_data,
    input  wire        beta_write_en
);

    // 16 × 32-bit register array
    reg [31:0] registers [0:15];
    integer k;

    // ── Asynchronous combinational read ports ───────────────────────
    // R0 is hardwired to zero (clean/reset vector)
    wire [31:0] alpha_srcA_raw = (alpha_srcA_addr == 4'd0) ? 32'd0 : registers[alpha_srcA_addr];
    wire [31:0] alpha_srcB_raw = (alpha_srcB_addr == 4'd0) ? 32'd0 : registers[alpha_srcB_addr];
    wire [31:0] beta_srcA_raw  = (beta_srcA_addr  == 4'd0) ? 32'd0 : registers[beta_srcA_addr];
    wire [31:0] beta_srcB_raw  = (beta_srcB_addr  == 4'd0) ? 32'd0 : registers[beta_srcB_addr];

    // ── Combinational write-forwarding bypass ───────────────────────
    // If a write is happening this cycle to the same register being read,
    // forward the write data directly instead of reading the old value.
    //
    // Cluster Alpha forwarding checks:
    //   1. Is Alpha writing to the same register that Alpha srcA reads?
    //   2. Is Beta  writing to the same register that Alpha srcA reads?
    wire alpha_srcA_bypass_alpha = alpha_write_en && (alpha_dest_addr == alpha_srcA_addr) && (alpha_srcA_addr != 4'd0);
    wire alpha_srcA_bypass_beta  = beta_write_en  && (beta_dest_addr  == alpha_srcA_addr) && (alpha_srcA_addr != 4'd0);
    wire alpha_srcB_bypass_alpha = alpha_write_en && (alpha_dest_addr == alpha_srcB_addr) && (alpha_srcB_addr != 4'd0);
    wire alpha_srcB_bypass_beta  = beta_write_en  && (beta_dest_addr  == alpha_srcB_addr) && (alpha_srcB_addr != 4'd0);

    // Cluster Beta forwarding checks:
    wire beta_srcA_bypass_alpha  = alpha_write_en && (alpha_dest_addr == beta_srcA_addr)  && (beta_srcA_addr  != 4'd0);
    wire beta_srcA_bypass_beta   = beta_write_en  && (beta_dest_addr  == beta_srcA_addr)  && (beta_srcA_addr  != 4'd0);
    wire beta_srcB_bypass_alpha  = alpha_write_en && (alpha_dest_addr == beta_srcB_addr)  && (beta_srcB_addr  != 4'd0);
    wire beta_srcB_bypass_beta   = beta_write_en  && (beta_dest_addr  == beta_srcB_addr)  && (beta_srcB_addr  != 4'd0);

    // Priority: Alpha write overrides Beta write for same-dest collision,
    // but the lookahead hazard unit guarantees this never happens.
    assign alpha_srcA_data = alpha_srcA_bypass_alpha ? alpha_dest_data :
                             alpha_srcA_bypass_beta  ? beta_dest_data  :
                             alpha_srcA_raw;

    assign alpha_srcB_data = alpha_srcB_bypass_alpha ? alpha_dest_data :
                             alpha_srcB_bypass_beta  ? beta_dest_data  :
                             alpha_srcB_raw;

    assign beta_srcA_data  = beta_srcA_bypass_alpha  ? alpha_dest_data :
                             beta_srcA_bypass_beta   ? beta_dest_data  :
                             beta_srcA_raw;

    assign beta_srcB_data  = beta_srcB_bypass_alpha  ? alpha_dest_data :
                             beta_srcB_bypass_beta   ? beta_dest_data  :
                             beta_srcB_raw;

    // ── Synchronous dual-write datapath ─────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (k = 0; k < 16; k = k + 1) begin
                registers[k] <= 32'd0;
            end
        end else begin
            // Priority: Alpha writes first, then Beta.
            // Hazard unit guarantees dest addresses never collide.
            if (alpha_write_en && (alpha_dest_addr != 4'd0)) begin
                registers[alpha_dest_addr] <= alpha_dest_data;
            end
            if (beta_write_en && (beta_dest_addr != 4'd0)) begin
                registers[beta_dest_addr] <= beta_dest_data;
            end
        end
    end

endmodule
