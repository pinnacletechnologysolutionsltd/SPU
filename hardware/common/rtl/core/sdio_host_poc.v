// SDIO host PoC (simplified)
// - PoC scaffolding: fills an internal 512-byte block with a deterministic
//   test pattern when start_read is asserted, toggles sd_clk during the
//   operation and exposes a block checksum for verification.
// - NOTE: This is *not* a full SD/SDIO implementation. It's a PoC scaffold
//   for integration tests and TB development; full spec-compliant SDIO RTL
//   will follow in fpga-sdio-host workstream.

module sdio_host_poc (
    input  wire         clk,
    input  wire         rst_n,

    // Control
    input  wire         start_read,   // pulse to start reading one block
    input  wire [31:0]  lba,
    output reg          busy,
    output reg          done,
    output reg          error,

    // SD interface (host side) - PoC: tri-state-capable ports
    output reg          sd_clk,
    inout  wire         sd_cmd,
    inout  wire [3:0]   sd_dat,

    // Observability: simple block checksum of the last-read block
    output reg [31:0]   block_sum
);

localparam BLOCK_BYTES = 512;

// Internal BRAM (byte-addressable)
reg [7:0] mem [0:BLOCK_BYTES-1];
reg [9:0] idx; // enough for 512

// Simple FSM
localparam IDLE  = 2'd0;
localparam START = 2'd1;
localparam READ  = 2'd2;
localparam FIN   = 2'd3;
reg [1:0] state;

// Tri-state drivers (PoC: we drive CMD/DAT lines when busy to give visible activity)
reg sd_cmd_oe;
reg sd_cmd_out;
reg [3:0] sd_dat_oe;
reg [3:0] sd_dat_out;

assign sd_cmd = sd_cmd_oe ? sd_cmd_out : 1'bz;
genvar gi;
generate
  for (gi = 0; gi < 4; gi = gi + 1) begin : DAT_TRI
    assign sd_dat[gi] = sd_dat_oe[gi] ? sd_dat_out[gi] : 1'bz;
  end
endgenerate

// PoC behaviour: fill memory with pattern mem[i] = i[7:0], accumulate sum
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        busy <= 1'b0;
        done <= 1'b0;
        error <= 1'b0;
        sd_clk <= 1'b0;
        sd_cmd_oe <= 1'b0;
        sd_cmd_out <= 1'b0;
        sd_dat_oe <= 4'b0000;
        sd_dat_out <= 4'b0000;
        idx <= 10'd0;
        block_sum <= 32'd0;
        state <= IDLE;
    end else begin
        case (state)
            IDLE: begin
                done <= 1'b0;
                block_sum <= 32'd0;
                if (start_read && !busy) begin
                    busy <= 1'b1;
                    error <= 1'b0;
                    idx <= 10'd0;
                    sd_cmd_oe <= 1'b1;
                    sd_cmd_out <= 1'b0;
                    sd_dat_oe <= 4'b1111; // drive dat lines for visible activity
                    sd_dat_out <= 4'b0000;
                    state <= START;
                end
            end
            START: begin
                // simple kickoff: toggle clock once
                sd_clk <= ~sd_clk;
                state <= READ;
            end
            READ: begin
                // emulate reading a 512-byte block by writing a deterministic pattern
                mem[idx] <= idx[7:0];
                block_sum <= block_sum + idx[7:0];
                // toggle sd clock for visibility
                sd_clk <= ~sd_clk;
                idx <= idx + 1;
                if (idx == (BLOCK_BYTES - 1)) begin
                    state <= FIN;
                end
            end
            FIN: begin
                busy <= 1'b0;
                done <= 1'b1;
                sd_cmd_oe <= 1'b0;
                sd_dat_oe <= 4'b0000;
                state <= IDLE;
            end
            default: state <= IDLE;
        endcase
    end
end

endmodule
