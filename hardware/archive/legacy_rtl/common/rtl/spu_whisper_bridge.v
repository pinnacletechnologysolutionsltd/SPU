// spu_whisper_bridge.v (v2.0)
// Bridges Whisper PWI frame events to UART bytes for RP2350 monitoring.
//
// Two output modes:
//
// NORMAL (strike_pulse):
//   4-byte packet: [0xAA][frame_hi][frame_lo][frame_hi^frame_lo]
//
// SNAP (snap_req strobe):
//   Dumps the full 832-bit manifold as 13 × 8-byte framed surd packets:
//     [0xFE][axis:8][0x00][A[31:24]][A[23:16]][B[31:24]][B[23:16]][CRC:8]
//   CRC = XOR of all 8 bytes (so XOR of complete packet == 0x00).
//   13 × 8 = 104 bytes total — forensic state dump for Arch Linux terminal.
//   snap_req is ignored while a snap is already in progress.
//
// uart_tx_en strobes for exactly one cycle per byte sent.

`timescale 1ns/1ps

module spu_whisper_bridge (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [12:0]  whisper_frame,    // packed Whisper payload
    input  wire         strike_pulse,     // one-cycle strobe: new Whisper frame
    input  wire         snap_req,         // one-cycle strobe: dump full manifold
    input  wire [831:0] manifold_state,   // live 832-bit manifold (13 × 64-bit)
    output reg  [7:0]   uart_tx_byte,
    output reg          uart_tx_en,
    output reg          snap_busy         // 1 while snap dump is in progress
);

    localparam IDLE      = 3'd0;
    localparam SEND      = 3'd1;
    localparam WAIT      = 3'd2;
    localparam SNAP_LOAD = 3'd3;  // load next axis packet then go to SEND

    reg [2:0]  state;
    reg [3:0]  pkt_len;    // 4 for whisper, 8 for snap (needs 4 bits to hold 8)
    reg [7:0]  pkt [0:7];  // 8-byte packet buffer
    reg [2:0]  byte_idx;

    // Snap-dump tracking
    reg [3:0]  snap_axis;        // 0..12
    reg [831:0] snap_latch;      // latched at snap_req to freeze manifold

    // Extract one 64-bit axis from the latched snapshot
    // Format: {A[31:0], B[31:0]}
    wire [63:0] cur_axis;
    assign cur_axis = snap_latch[snap_axis*64 +: 64];
    wire [31:0] cur_A;
    assign cur_A = cur_axis[63:32];
    wire [31:0] cur_B;
    assign cur_B = cur_axis[31:0];

    // CRC = XOR of all 8 bytes of the snap packet (so full packet XOR == 0)
    wire [7:0] snap_crc  = 8'hFE ^ {4'b0, snap_axis} ^ 8'h00
                         ^ cur_A[31:24] ^ cur_A[23:16]
                         ^ cur_B[31:24] ^ cur_B[23:16];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            uart_tx_byte <= 8'h0;
            uart_tx_en   <= 1'b0;
            byte_idx     <= 3'd0;
            snap_axis    <= 4'd0;
            snap_busy    <= 1'b0;
        end else begin
            uart_tx_en <= 1'b0;

            case (state)
                IDLE: begin
                    if (snap_req) begin
                        // Snap takes priority — freeze manifold, load axis 0
                        snap_latch <= manifold_state;
                        snap_axis  <= 4'd0;
                        snap_busy  <= 1'b1;
                        state      <= SNAP_LOAD;
                    end else if (strike_pulse) begin
                        pkt[0]   <= 8'hAA;
                        pkt[1]   <= {3'b000, whisper_frame[12:8]};
                        pkt[2]   <= whisper_frame[7:0];
                        pkt[3]   <= {3'b000, whisper_frame[12:8]} ^ whisper_frame[7:0];
                        pkt_len  <= 4'd4;
                        byte_idx <= 3'd0;
                        state    <= SEND;
                    end
                end

                SNAP_LOAD: begin
                    // Build 8-byte framed surd packet for snap_axis
                    pkt[0]   <= 8'hFE;
                    pkt[1]   <= {4'b0, snap_axis};
                    pkt[2]   <= 8'h00;
                    pkt[3]   <= cur_A[31:24];
                    pkt[4]   <= cur_A[23:16];
                    pkt[5]   <= cur_B[31:24];
                    pkt[6]   <= cur_B[23:16];
                    pkt[7]   <= snap_crc;
                    pkt_len  <= 4'd8;
                    byte_idx <= 3'd0;
                    state    <= SEND;
                end

                SEND: begin
                    uart_tx_byte <= pkt[byte_idx];
                    uart_tx_en   <= 1'b1;
                    state        <= WAIT;
                end

                WAIT: begin
                    if (byte_idx == pkt_len - 4'd1) begin
                        // Packet complete
                        byte_idx <= 3'd0;
                        if (snap_busy) begin
                            if (snap_axis == 4'd12) begin
                                // All 13 axes sent
                                snap_busy <= 1'b0;
                                state     <= IDLE;
                            end else begin
                                snap_axis <= snap_axis + 4'd1;
                                state     <= SNAP_LOAD;
                            end
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        byte_idx <= byte_idx + 3'd1;
                        state    <= SEND;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
