// spu_manifold_persist.v — Manifold SDRAM Save/Restore (v1.0)
//
// Saves/restores the 832-bit manifold to SDRAM at fixed addresses.
// Designed to sit between spu13_core and spu_mem_bridge_sdram.
//
// Protocol:
//   save_pulse  → FSM captures manifold_out, issues mem_burst_wr, pulses done
//   load_pulse  → FSM issues mem_burst_rd, drives manifold_in, pulses done
//
// Address map (52 words × 16-bit per burst):
//   SAVE_ADDR  = 0x000000  (manifold slot 0)
//   SAVE_ADDR2 = 0x000034  (manifold slot 1, for checkpoint rollback)
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"

module spu_manifold_persist #(
    parameter [23:0] SAVE_ADDR  = 24'h000000,
    parameter [23:0] SAVE_ADDR2 = 24'h000034    // 52 words offset
)(
    input  wire        clk,
    input  wire        rst_n,

    // ── Control ──────────────────────────────────────────────
    input  wire        save_pulse,     // one-cycle pulse to save
    input  wire        load_pulse,     // one-cycle pulse to restore
    output reg         persist_done,   // pulses when operation completes
    output reg         persist_error,  // pulses if bridge not ready

    // ── Manifold data (from/to spu13_core) ───────────────────
    input  wire [`MANIFOLD_WIDTH-1:0] manifold_out,
    output reg  [`MANIFOLD_WIDTH-1:0] manifold_in,

    // ── SDRAM bridge interface ───────────────────────────────
    input  wire        mem_ready,
    output reg         mem_burst_rd,
    output reg         mem_burst_wr,
    output reg  [23:0] mem_addr,
    input  wire [`MANIFOLD_WIDTH-1:0] mem_rd_manifold,
    output reg  [`MANIFOLD_WIDTH-1:0] mem_wr_manifold,
    input  wire        mem_burst_done
);

    // ── FSM ──────────────────────────────────────────────────
    localparam S_IDLE  = 0;
    localparam S_SAVE  = 1;   // issue burst write, wait for done
    localparam S_LOAD  = 2;   // issue burst read, wait for done
    localparam S_WAIT  = 3;   // wait for mem_burst_done

    reg [1:0] state;
    reg       is_save;  // 1 = save, 0 = load

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state         <= S_IDLE;
            persist_done  <= 0;
            persist_error <= 0;
            manifold_in   <= 0;
            mem_burst_rd  <= 0;
            mem_burst_wr  <= 0;
            mem_addr      <= 0;
            mem_wr_manifold <= 0;
            is_save       <= 0;
        end else begin
            persist_done  <= 0;
            persist_error <= 0;
            mem_burst_rd  <= 0;
            mem_burst_wr  <= 0;

            case (state)
                S_IDLE: begin
                    if (save_pulse) begin
                        if (!mem_ready) begin
                            persist_error <= 1;
                            persist_done  <= 1;
                        end else begin
                            mem_wr_manifold <= manifold_out;
                            mem_addr        <= SAVE_ADDR;
                            mem_burst_wr    <= 1;
                            is_save         <= 1;
                            state           <= S_WAIT;
                        end
                    end else if (load_pulse) begin
                        if (!mem_ready) begin
                            persist_error <= 1;
                            persist_done  <= 1;
                        end else begin
                            mem_addr       <= SAVE_ADDR;
                            mem_burst_rd   <= 1;
                            is_save        <= 0;
                            state          <= S_WAIT;
                        end
                    end
                end

                S_WAIT: begin
                    if (mem_burst_done) begin
                        if (!is_save) begin
                            manifold_in <= mem_rd_manifold;
                        end
                        persist_done <= 1;
                        state <= S_IDLE;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
