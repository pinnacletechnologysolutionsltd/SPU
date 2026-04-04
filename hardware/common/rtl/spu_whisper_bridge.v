// spu_whisper_bridge.v (v1.0)
// Bridges Whisper PWI frame events to UART bytes for RP2350 monitoring.
//
// Each strike_pulse triggers a 4-byte UART packet:
//   Byte 0: 0xAA  (start marker)
//   Byte 1: {3'b0, whisper_frame[12:8]}  (high 5 bits, zero-padded)
//   Byte 2: whisper_frame[7:0]           (low 8 bits)
//   Byte 3: byte1 ^ byte2                (XOR integrity check)
//
// Caller asserts strike_pulse for exactly one cycle when a new Whisper
// frame is available. uart_tx_en strobes once per byte sent.

module spu_whisper_bridge (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [12:0] whisper_frame,  // packed Whisper payload
    input  wire        strike_pulse,   // one-cycle strobe: new frame ready
    output reg  [7:0]  uart_tx_byte,
    output reg         uart_tx_en
);

    localparam IDLE = 2'd0;
    localparam SEND = 2'd1;
    localparam WAIT = 2'd2;

    reg [1:0] state;
    reg [1:0] byte_idx;
    reg [7:0] pkt [0:3];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            uart_tx_byte <= 8'h0;
            uart_tx_en   <= 1'b0;
            byte_idx     <= 2'd0;
        end else begin
            uart_tx_en <= 1'b0;

            case (state)
                IDLE: begin
                    if (strike_pulse) begin
                        pkt[0]   <= 8'hAA;
                        pkt[1]   <= {3'b000, whisper_frame[12:8]};
                        pkt[2]   <= whisper_frame[7:0];
                        pkt[3]   <= {3'b000, whisper_frame[12:8]} ^ whisper_frame[7:0];
                        byte_idx <= 2'd0;
                        state    <= SEND;
                    end
                end

                SEND: begin
                    uart_tx_byte <= pkt[byte_idx];
                    uart_tx_en   <= 1'b1;
                    state        <= WAIT;
                end

                WAIT: begin
                    if (byte_idx == 2'd3) begin
                        byte_idx <= 2'd0;
                        state    <= IDLE;
                    end else begin
                        byte_idx <= byte_idx + 2'd1;
                        state    <= SEND;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
