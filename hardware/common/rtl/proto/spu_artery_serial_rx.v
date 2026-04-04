// spu_artery_serial_rx.v (v1.0)
// Receives one 11-byte Artery serial frame from UART 8N1.
//
// Frame layout (see spu_artery_serial_tx.v for full spec).
// Validation: byte[0] must be 0xAA AND XOR of all 11 bytes must equal 0.
//
// rx_valid pulses for exactly 1 cycle when a good frame is decoded.
// rx_error pulses for exactly 1 cycle on checksum mismatch or framing fault.
// Partial frames (framing error mid-frame) reset byte_cnt and wait for the
// next 0xAA-aligned start.
//
// Sampling point: CLK_PER_BIT/2 cycles after start-bit falling edge (middle
// of start bit), then CLK_PER_BIT cycles between each subsequent sample.
// At CLK_PER_BIT=26 (≈ 923 kbaud) the jitter budget is ±13 cycles = ±541 ns.

module spu_artery_serial_rx #(
    parameter CLK_PER_BIT = 26
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        rx,          // UART RX line (idle high)
    output reg  [2:0]  rx_node_id,  // node address from last valid frame
    output reg  [63:0] rx_chord,    // 64-bit chord from last valid frame
    output reg         rx_valid,    // 1-cycle pulse: new frame decoded OK
    output reg         rx_error     // 1-cycle pulse: checksum / framing fault
);

    // 2-stage synchroniser for async RX line
    reg [1:0] rx_sync;
    wire rx_s    =  rx_sync[1];           // synchronised rx
    wire rx_fall = (rx_sync == 2'b10);    // falling edge = start bit

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) rx_sync <= 2'b11;   // idle high
        else        rx_sync <= {rx_sync[0], rx};
    end

    localparam IDLE  = 2'd0;
    localparam START = 2'd1;  // half-bit wait to align to middle of start bit
    localparam DATA  = 2'd2;  // collect 8 data bits
    localparam STOP  = 2'd3;  // verify stop bit, commit byte

    reg [1:0]  state;
    reg [5:0]  clk_cnt;    // bit-period counter
    reg [2:0]  bit_cnt;    // data bit index 0–7
    reg [3:0]  byte_cnt;   // frame byte index 0–10
    reg [7:0]  shift_reg;  // shift register for current byte (LSB first)
    reg [7:0]  frame [0:10];
    reg [7:0]  rx_xor;     // running XOR of bytes received so far

    integer k;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            clk_cnt    <= 6'd0;
            bit_cnt    <= 3'd0;
            byte_cnt   <= 4'd0;
            shift_reg  <= 8'h0;
            rx_xor     <= 8'h0;
            rx_valid   <= 1'b0;
            rx_error   <= 1'b0;
            rx_node_id <= 3'h0;
            rx_chord   <= 64'h0;
            for (k = 0; k < 11; k = k + 1) frame[k] <= 8'h0;
        end else begin
            rx_valid <= 1'b0;   // default: deasserted every cycle
            rx_error <= 1'b0;

            case (state)

                IDLE: begin
                    if (rx_fall) begin
                        clk_cnt <= 6'd0;
                        // Reset XOR accumulator at the start of each new frame
                        if (byte_cnt == 4'd0) rx_xor <= 8'h0;
                        state <= START;
                    end
                end

                // Wait CLK_PER_BIT/2 cycles to land in the middle of the start bit
                START: begin
                    if (clk_cnt < (CLK_PER_BIT / 2) - 1) begin
                        clk_cnt <= clk_cnt + 6'd1;
                    end else begin
                        clk_cnt <= 6'd0;
                        if (!rx_s) begin
                            // Valid start bit confirmed
                            bit_cnt <= 3'd0;
                            state   <= DATA;
                        end else begin
                            // False start — discard and resync
                            byte_cnt <= 4'd0;
                            rx_xor   <= 8'h0;
                            state    <= IDLE;
                        end
                    end
                end

                // Sample each data bit at the centre of its bit period
                DATA: begin
                    if (clk_cnt < CLK_PER_BIT - 1) begin
                        clk_cnt <= clk_cnt + 6'd1;
                    end else begin
                        clk_cnt   <= 6'd0;
                        shift_reg <= {rx_s, shift_reg[7:1]};  // LSB-first UART
                        if (bit_cnt == 3'd7) begin
                            bit_cnt <= 3'd0;
                            state   <= STOP;
                        end else begin
                            bit_cnt <= bit_cnt + 3'd1;
                        end
                    end
                end

                // Verify stop bit, commit byte to frame buffer
                STOP: begin
                    if (clk_cnt < CLK_PER_BIT - 1) begin
                        clk_cnt <= clk_cnt + 6'd1;
                    end else begin
                        clk_cnt <= 6'd0;

                        if (rx_s) begin
                            // Valid stop bit
                            frame[byte_cnt] <= shift_reg;
                            rx_xor          <= rx_xor ^ shift_reg;

                            if (byte_cnt == 4'd10) begin
                                // Complete frame received — validate
                                byte_cnt <= 4'd0;
                                state    <= IDLE;

                                // frame[0] was stored 10 bytes ago; rx_xor is
                                // bytes 0–9; shift_reg is byte 10.
                                // XOR of all 11 bytes must be 0.
                                if (frame[0] == 8'hAA &&
                                    (rx_xor ^ shift_reg) == 8'h0) begin
                                    rx_valid   <= 1'b1;
                                    rx_node_id <= frame[1][2:0];
                                    rx_chord   <= {frame[2], frame[3],
                                                   frame[4], frame[5],
                                                   frame[6], frame[7],
                                                   frame[8], frame[9]};
                                end else begin
                                    rx_error <= 1'b1;
                                end
                            end else begin
                                byte_cnt <= byte_cnt + 4'd1;
                                state    <= IDLE;  // wait for next start bit
                            end
                        end else begin
                            // Framing error — resync from byte 0
                            byte_cnt <= 4'd0;
                            rx_xor   <= 8'h0;
                            state    <= IDLE;
                            rx_error <= 1'b1;
                        end
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
