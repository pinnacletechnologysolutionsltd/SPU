// spu_artery_serial_tx.v (v1.0)
// Transmits one 11-byte Artery serial frame over UART 8N1.
//
// Frame layout (MSB-first, big-endian chord):
//   [0] 0xAA          start marker
//   [1] {5'b0,node_id} satellite address 0–7
//   [2] chord[63:56]  \
//   [3] chord[55:48]   |
//   [4] chord[47:40]   |  64-bit manifold chord
//   [5] chord[39:32]   |
//   [6] chord[31:24]   |
//   [7] chord[23:16]   |
//   [8] chord[15:8]    |
//   [9] chord[7:0]    /
//  [10] XOR of bytes 0–9  (integrity check; XOR of all 11 bytes == 0)
//
// Each byte is UART 8N1: 1 start + 8 data (LSB first) + 1 stop = 10 bits.
// Total frame: 11 × 10 × CLK_PER_BIT clocks  (26 → 2860 clocks ≈ 119 µs @ 24 MHz)
//
// send is a 1-cycle strobe. A new send while busy is silently ignored.

module spu_artery_serial_tx #(
    parameter CLK_PER_BIT = 26   // 24 MHz / 26 ≈ 923 kbaud
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [2:0]  node_id,   // satellite address 0–7
    input  wire [63:0] chord,     // 64-bit manifold chord
    input  wire        send,      // 1-cycle strobe: load and begin TX
    output reg         tx,        // UART TX (idle high)
    output reg         busy       // high for entire frame duration
);

    localparam IDLE = 1'b0;
    localparam SEND = 1'b1;

    reg        state;
    reg [7:0]  pkt [0:10];    // 11-byte packet buffer
    reg [3:0]  byte_cnt;      // 0–10: current byte
    reg [3:0]  bit_cnt;       // 0=start 1–8=data 9=stop
    reg [5:0]  clk_cnt;       // 0..CLK_PER_BIT-1
    reg [7:0]  cur_byte;      // byte currently being clocked out

    integer k;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= IDLE;
            tx       <= 1'b1;
            busy     <= 1'b0;
            byte_cnt <= 4'd0;
            bit_cnt  <= 4'd0;
            clk_cnt  <= 6'd0;
            cur_byte <= 8'h0;
            for (k = 0; k < 11; k = k + 1) pkt[k] <= 8'h0;
        end else begin
            case (state)

                IDLE: begin
                    tx   <= 1'b1;
                    busy <= 1'b0;
                    if (send) begin
                        pkt[0]  <= 8'hAA;
                        pkt[1]  <= {5'b0, node_id};
                        pkt[2]  <= chord[63:56];
                        pkt[3]  <= chord[55:48];
                        pkt[4]  <= chord[47:40];
                        pkt[5]  <= chord[39:32];
                        pkt[6]  <= chord[31:24];
                        pkt[7]  <= chord[23:16];
                        pkt[8]  <= chord[15:8];
                        pkt[9]  <= chord[7:0];
                        pkt[10] <= 8'hAA ^ {5'b0, node_id}
                                 ^ chord[63:56] ^ chord[55:48] ^ chord[47:40]
                                 ^ chord[39:32] ^ chord[31:24] ^ chord[23:16]
                                 ^ chord[15:8]  ^ chord[7:0];
                        byte_cnt <= 4'd0;
                        bit_cnt  <= 4'd0;
                        clk_cnt  <= 6'd0;
                        cur_byte <= 8'hAA;   // pkt[0]
                        tx       <= 1'b0;    // start bit of byte 0
                        busy     <= 1'b1;
                        state    <= SEND;
                    end
                end

                SEND: begin
                    if (clk_cnt < CLK_PER_BIT - 1) begin
                        clk_cnt <= clk_cnt + 6'd1;
                    end else begin
                        clk_cnt <= 6'd0;

                        if (bit_cnt == 4'd9) begin
                            // Stop bit just finished
                            if (byte_cnt == 4'd10) begin
                                // All 11 bytes sent
                                state <= IDLE;
                                tx    <= 1'b1;
                                busy  <= 1'b0;
                            end else begin
                                // Advance to next byte; drive its start bit
                                byte_cnt <= byte_cnt + 4'd1;
                                bit_cnt  <= 4'd0;
                                cur_byte <= pkt[byte_cnt + 4'd1]; // pre-load using old byte_cnt
                                tx       <= 1'b0;  // start bit
                            end
                        end else begin
                            // Advance to next bit and drive tx
                            bit_cnt <= bit_cnt + 4'd1;
                            case (bit_cnt + 4'd1)
                                4'd1: tx <= cur_byte[0];
                                4'd2: tx <= cur_byte[1];
                                4'd3: tx <= cur_byte[2];
                                4'd4: tx <= cur_byte[3];
                                4'd5: tx <= cur_byte[4];
                                4'd6: tx <= cur_byte[5];
                                4'd7: tx <= cur_byte[6];
                                4'd8: tx <= cur_byte[7];
                                4'd9: tx <= 1'b1;    // stop bit
                                default: tx <= 1'b1;
                            endcase
                        end
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
