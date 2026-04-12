// spu_node_link.v (v2.0) — Governor↔Satellite Sync Protocol
// CC0 1.0 Universal.
//
// Handles the bidirectional sync between the SPU-13 Governor (Mother) and
// a single SPU-4 Satellite on the Artery bus.
//
// Receive path (Governor → Satellite or Satellite → Governor):
//   rx_frame[15]   = snap_alert  (Satellite reports snap-lock status)
//   rx_frame[14:7] = dissonance  (8-bit Davis Ratio deviation)
//   rx_frame[6:0]  = payload
//
// Transmit path (Governor → Satellite broadcast):
//   tx_frame[31:16] = prime_anchor[23:8]  (top 16 bits of Thomson prime)
//   tx_frame[15:8]  = Davis XOR tag       (integrity check for the anchor)
//   tx_frame[7:0]   = reserved (0x00)
//
// Davis XOR tag: XOR of all 4 bytes of tx_frame (tag chosen so full XOR=0).
//   tag = prime_anchor[23:16] ^ prime_anchor[15:8] ^ 8'h00 = anchor_hi^anchor_lo
//   Full XOR: anchor_hi ^ anchor_lo ^ tag ^ 0x00 = anchor_hi ^ anchor_lo ^ (anchor_hi^anchor_lo) = 0x00 ✓
//
// sync_alert logic:
//   Fires when SYNC_FAIL_THRESH consecutive rx frames have snap_alert=0.
//   Clears as soon as snap_alert=1 is seen.
//   This prevents spurious alerts from a single dropped frame.

`timescale 1ns/1ps

module spu_node_link #(
    parameter SYNC_FAIL_THRESH = 3   // consecutive failures before alert
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire [23:0] prime_anchor_in, // Thomson prime from laminar boot

    input  wire [15:0] rx_frame,        // [15] snap_alert | [14:7] dissonance | [6:0] payload
    output reg  [31:0] tx_frame,        // broadcast frame to satellite
    output reg         sync_alert,
    output wire [7:0]  satellite_dissonance
);

    assign satellite_dissonance = rx_frame[14:7];

    // ── Consecutive failure counter ──────────────────────────────────────
    reg [1:0] fail_cnt;   // saturates at SYNC_FAIL_THRESH (max 3, fits 2 bits)

    // ── Davis XOR integrity tag ──────────────────────────────────────────
    wire [7:0] anchor_hi;
    assign anchor_hi = prime_anchor_in[23:16];
    wire [7:0] anchor_lo;
    assign anchor_lo = prime_anchor_in[15:8];
    wire [7:0] davis_tag  = anchor_hi ^ anchor_lo;  // full-frame XOR = 0

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_frame   <= 32'h0;
            sync_alert <= 1'b0;
            fail_cnt   <= 2'd0;
        end else begin
            // ── TX: pack prime anchor with integrity tag ─────────────────
            tx_frame <= {prime_anchor_in[23:8], davis_tag, 8'h00};

            // ── RX: update consecutive failure counter ───────────────────
            if (rx_frame[15]) begin
                // snap_alert asserted — satellite is locked, clear counter
                fail_cnt   <= 2'd0;
                sync_alert <= 1'b0;
            end else begin
                // snap_alert absent — count consecutive misses
                if (fail_cnt < SYNC_FAIL_THRESH[1:0]) begin
                    fail_cnt <= fail_cnt + 2'd1;
                end
                // Assert sync_alert once threshold is reached (hold until cleared)
                if (fail_cnt >= SYNC_FAIL_THRESH[1:0] - 2'd1) begin
                    sync_alert <= 1'b1;
                end
            end
        end
    end

endmodule
