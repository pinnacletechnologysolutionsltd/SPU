// spu_uart_bridge.v — UART → SovereignBus Bridge  v1.1
// Receives 6-byte frames: [CMD][ADDR][DATA3][DATA2][DATA1][DATA0]
// CMD 0x00 = WRITE, 0x80 = READ.
// Parameterised for any CLK_FREQ / BAUD_RATE combination.
// Fix over archive v1.2: correct bit-timer width for 27 MHz / 921600 baud.

`default_nettype none

module spu_uart_bridge #(
    parameter CLK_FREQ  = 27_000_000,
    parameter BAUD_RATE = 921_600
)(
    input  wire        clk,
    input  wire        reset,
    input  wire        uart_rx,

    // SovereignBus master
    output reg  [7:0]  bus_addr,
    output reg  [31:0] bus_data,
    output reg         bus_wen,
    output reg         bus_ren,
    input  wire        bus_ready
);

    // Bit period in clocks (ceiling)
    localparam BIT_CYCLES = (CLK_FREQ + BAUD_RATE - 1) / BAUD_RATE;
    // Timer wide enough for worst case (921600@27MHz = 30 cycles)
    localparam TIMER_W = 8;

    localparam S_IDLE     = 3'd0;
    localparam S_START    = 3'd1;
    localparam S_DATA     = 3'd2;
    localparam S_STOP     = 3'd3;
    localparam S_DISPATCH = 3'd4;
    // Mid-frame inter-byte wait: like S_IDLE but byte_cnt is NOT reset
    localparam S_NEXT     = 3'd5;

    reg [2:0]  state;
    reg [3:0]  bit_cnt;
    reg [2:0]  byte_cnt;
    reg [7:0]  cur_byte;
    reg [TIMER_W-1:0] timer;
    reg [7:0]  frame [0:5];  // CMD, ADDR, D[0]…D[3]

    integer k;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state    <= S_IDLE;
            bit_cnt  <= 0;
            byte_cnt <= 0;
            timer    <= 0;
            bus_wen  <= 0;
            bus_ren  <= 0;
            bus_addr <= 0;
            bus_data <= 0;
        end else begin
            bus_wen <= 0;
            bus_ren <= 0;

            case (state)
                S_IDLE: begin
                    if (!uart_rx) begin          // start bit detected (low)
                        timer    <= 0;
                        byte_cnt <= 0;
                        state    <= S_START;
                    end
                end

                S_START: begin
                    timer <= timer + 1'b1;
                    if (timer == BIT_CYCLES / 2 - 1) begin
                        if (!uart_rx) begin       // still low = valid start bit
                            state   <= S_DATA;
                            bit_cnt <= 0;
                            timer   <= 0;
                        end else
                            state <= S_IDLE;      // glitch
                    end
                end

                S_DATA: begin
                    timer <= timer + 1'b1;
                    if (timer == BIT_CYCLES - 1) begin
                        timer              <= 0;
                        cur_byte[bit_cnt]  <= uart_rx;
                        if (bit_cnt == 3'd7) begin
                            bit_cnt <= 0;
                            state   <= S_STOP;
                        end else
                            bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                S_STOP: begin
                    timer <= timer + 1'b1;
                    if (timer == BIT_CYCLES - 1) begin
                        timer <= 0;
                        if (uart_rx) begin                // valid stop bit
                            frame[byte_cnt] <= cur_byte;
                            if (byte_cnt == 3'd5)
                                state <= S_DISPATCH;
                            else begin
                                byte_cnt <= byte_cnt + 1'b1;
                                state    <= S_NEXT;       // wait for next byte start
                            end
                        end else
                            state <= S_IDLE;              // framing error → abort frame
                    end
                end

                // Wait for next byte's start bit without resetting byte_cnt
                S_NEXT: begin
                    if (!uart_rx) begin
                        timer   <= 0;
                        state   <= S_START;
                    end
                end

                S_DISPATCH: begin
                    bus_addr <= frame[1];
                    bus_data <= {frame[5], frame[4], frame[3], frame[2]};
                    case (frame[0])
                        8'h00: bus_wen <= 1'b1;
                        8'h80: bus_ren <= 1'b1;
                    endcase
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
`default_nettype wire
