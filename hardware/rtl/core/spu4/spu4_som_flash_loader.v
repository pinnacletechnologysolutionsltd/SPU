`timescale 1ns / 1ps

// spu4_som_flash_loader.v -- hydrate spu4_som_edge's weight registers from
// external SPI flash at boot.
//
// This is the product path for the SPU-4 edge node: training happens once,
// offline, in tools/spu4_som_edge_trainer.py (bit-identical BMU selection to
// this module's own oracle, software/lib/spu4_som_edge_oracle.py -- NOT
// software/lib/rational_som.py, which is the unrelated seven-node SPU-13
// SOM's math); the trained weights are written
// to a $2 SPI flash chip (tools/rp2040_flash_pmod.py, the same PMOD path
// already proven for RPLU2's boot tables); the flash chip ships with the
// board. No host is present at runtime -- `start` pulsed once after reset is
// enough to bring spu4_som_edge's four nodes up to their trained state.
// Re-training means reprogramming the chip and resetting, not a live
// protocol -- see docs/SPU4_ABI.md's discussion of this tradeoff.
//
// Owns spu_flash_bridge.v (hardware/rtl/peripherals/storage/) as its single
// SPI transport, matching this repo's single-owner-engine convention -- see
// spu13_tang25k_spu4_abi_probe.v's UART engine comment. Do not share the
// flash bus with another consumer without redesigning this as an arbiter.
//
// ── Flash image layout, starting at FLASH_SPU4_SOM_BASE ──────────────────
// Node 0, feature 0: P_hi P_lo Q_hi Q_lo   (RationalSurd: P upper, Q lower,
// Node 0, feature 1: P_hi P_lo Q_hi Q_lo    each half big-endian on the wire)
// ...
// Node 0, feature NUM_FEATURES-1: P_hi P_lo Q_hi Q_lo
// Node 1, feature 0: ...
// ...
// Node 3, feature NUM_FEATURES-1: P_hi P_lo Q_hi Q_lo
//
// 4 nodes x NUM_FEATURES x 4 bytes, node-major then feature-ascending. This
// is a new convention (this is the first flash consumer on the SPU-4 side),
// chosen to read naturally byte-for-byte in a packer script -- it does NOT
// need to match spu4_som_edge's internal weight_data bit order; this module
// does that translation.

module spu4_som_flash_loader #(
    parameter integer NUM_FEATURES = 4,
    parameter integer WIDTH        = 16
) (
    input  wire        clk,
    input  wire        rst_n,

    // Pulse once to begin hydration. Ignored while busy. Re-triggerable
    // (bench/test convenience) once done -- a real boot sequence pulses it
    // exactly once.
    input  wire        start,
    output reg          busy,
    output reg          done,       // level, held until the next accepted start

    // ── Toward spu4_som_edge ──────────────────────────────────────────
    output wire                                  weight_we,
    output wire [1:0]                            weight_node,
    output wire [NUM_FEATURES * 2 * WIDTH - 1:0]  weight_data,

    // ── Physical SPI pins toward external flash ────────────────────────
    output wire        flash_sclk,
    output wire        flash_cs_n,
    output wire        flash_mosi,
    input  wire        flash_miso
);

`ifndef FLASH_PELL_BASE
`include "hardware/rtl/arch/spu_flash_map.vh"
`endif

    localparam integer FEATURE_W         = 2 * WIDTH;
    localparam integer NODE_W            = NUM_FEATURES * FEATURE_W;
    localparam integer BYTES_PER_FEATURE = FEATURE_W / 8;
    localparam integer BYTES_PER_NODE    = NUM_FEATURES * BYTES_PER_FEATURE;
    localparam integer TOTAL_BYTES       = 4 * BYTES_PER_NODE;

    localparam [23:0] FLASH_BASE_ADDR = `FLASH_SPU4_SOM_BASE;

    // ── SPI transport (single owner) ───────────────────────────────────
    reg         rd_trig;
    reg  [23:0] rd_addr;
    reg         burst;
    reg         rd_stop;
    wire [7:0]  rd_data;
    wire        rd_done;

    spu_flash_bridge u_flash (
        .clk(clk), .rst_n(rst_n),
        .rd_trig(rd_trig), .rd_addr(rd_addr), .burst(burst), .rd_stop(rd_stop),
        .rd_data(rd_data), .rd_done(rd_done),
        .flash_sclk(flash_sclk), .flash_cs_n(flash_cs_n),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    // ── Assembly state ───────────────────────────────────────────────
    localparam S_IDLE    = 3'd0;
    localparam S_TRIGGER = 3'd1;
    localparam S_COLLECT = 3'd2;
    localparam S_COMMIT  = 3'd3;
    localparam S_DONE    = 3'd4;

    reg [2:0]  state;
    reg [15:0] byte_idx;                 // global byte count, for rd_stop timing
    reg [7:0]  byte_in_feature;          // 0..BYTES_PER_FEATURE-1
    reg [7:0]  feature_idx;              // 0..NUM_FEATURES-1
    reg [1:0]  node_idx;

    reg [FEATURE_W-1:0] feat_acc;        // current feature, MSB-first shift-in
    reg [NODE_W-1:0]    node_acc;        // assembled node word

    // The byte just clocked in this cycle, folded into feat_acc, computed
    // combinationally so it can be written into node_acc THE SAME CYCLE it
    // completes -- feat_acc itself only reflects it one cycle later (NBA).
    wire [FEATURE_W-1:0] feat_acc_next = {feat_acc[FEATURE_W-9:0], rd_data};

    assign weight_we    = (state == S_COMMIT);
    assign weight_node  = node_idx;
    assign weight_data  = node_acc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state           <= S_IDLE;
            busy            <= 1'b0;
            done            <= 1'b0;
            rd_trig         <= 1'b0;
            rd_addr         <= 24'h0;
            burst           <= 1'b0;
            rd_stop         <= 1'b0;
            byte_idx        <= 16'd0;
            byte_in_feature <= 8'd0;
            feature_idx     <= 8'd0;
            node_idx        <= 2'd0;
            feat_acc        <= {FEATURE_W{1'b0}};
            node_acc        <= {NODE_W{1'b0}};
        end else begin
            rd_trig <= 1'b0;             // one-cycle pulse, default low

            case (state)
                S_IDLE, S_DONE: begin
                    if (start) begin
                        busy            <= 1'b1;
                        done            <= 1'b0;
                        rd_addr         <= FLASH_BASE_ADDR;
                        burst           <= 1'b1;
                        rd_trig         <= 1'b1;
                        rd_stop         <= 1'b0;
                        byte_idx        <= 16'd0;
                        byte_in_feature <= 8'd0;
                        feature_idx     <= 8'd0;
                        node_idx        <= 2'd0;
                        state           <= S_TRIGGER;
                    end
                end

                // One cycle for rd_trig to register in spu_flash_bridge
                // before the first rd_done can possibly arrive.
                S_TRIGGER: state <= S_COLLECT;

                S_COLLECT: begin
                    if (rd_done) begin
                        feat_acc <= feat_acc_next;
                        byte_idx <= byte_idx + 16'd1;

                        // Assert rd_stop while receiving the LAST desired
                        // byte -- held for the whole byte, not a single-
                        // cycle pulse, so it is set well before that byte's
                        // internal bit_cnt reaches 0 inside spu_flash_bridge.
                        if (byte_idx == TOTAL_BYTES - 1)
                            rd_stop <= 1'b1;

                        if (byte_in_feature == BYTES_PER_FEATURE - 1) begin
                            // Last byte of this feature: feat_acc_next is
                            // the complete feature word. Land it in node_acc.
                            node_acc[(feature_idx * FEATURE_W) +: FEATURE_W]
                                <= feat_acc_next;
                            byte_in_feature <= 8'd0;

                            if (feature_idx == NUM_FEATURES - 1) begin
                                // Last feature of this node too: node_acc
                                // will be complete one cycle from now.
                                feature_idx <= 8'd0;
                                state       <= S_COMMIT;
                            end else begin
                                feature_idx <= feature_idx + 8'd1;
                            end
                        end else begin
                            byte_in_feature <= byte_in_feature + 8'd1;
                        end
                    end
                end

                // node_acc is now valid (the write that completed it landed
                // last cycle). weight_we/weight_node/weight_data are driven
                // combinationally from state/node_idx/node_acc above.
                S_COMMIT: begin
                    if (node_idx == 2'd3) begin
                        burst   <= 1'b0;
                        rd_stop <= 1'b0;
                        busy    <= 1'b0;
                        done    <= 1'b1;
                        state   <= S_DONE;
                    end else begin
                        node_idx <= node_idx + 2'd1;
                        state    <= S_COLLECT;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
