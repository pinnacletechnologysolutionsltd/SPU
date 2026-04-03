// SPU-13 Universal UART Transmitter (v3.3.87)
// Implementation: 64-bit Laminar Frame Transmission.
// Objective: Stream [Header][Payload][Footer] bit-exactly to the host.

module surd_uart_tx #(
    parameter CLK_HZ = 12000000,
    parameter BAUD   = 115200
)(
    input  wire        clk,
    input  wire        reset,
    input  wire [63:0] data_in, // Expanded to 64-bit Laminar Frame
    input  wire        start,
    output reg         tx,
    output reg         ready
);

    localparam BIT_PERIOD = CLK_HZ / BAUD;
    localparam IDLE=0, START=1, DATA=2, STOP=3;

    reg [3:0]  state;
    reg [31:0] clk_cnt;
    reg [5:0]  bit_cnt; // 0-63 bits
    reg [63:0] shift_reg;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            tx <= 1'b1;
            ready <= 1'b1;
            clk_cnt <= 0;
            bit_cnt <= 0;
        end else begin
            case (state)
                IDLE: begin
                    ready <= 1'b1;
                    tx <= 1'b1;
                    if (start) begin
                        shift_reg <= data_in;
                        state <= START;
                        ready <= 1'b0;
                        clk_cnt <= 0;
                    end
                end

                START: begin
                    tx <= 1'b0;
                    if (clk_cnt == BIT_PERIOD - 1) begin
                        clk_cnt <= 0;
                        state <= DATA;
                        bit_cnt <= 0;
                    end else begin
                        clk_cnt <= clk_cnt + 1;
                    end
                end

                DATA: begin
                    tx <= shift_reg[0];
                    if (clk_cnt == BIT_PERIOD - 1) begin
                        clk_cnt <= 0;
                        if (bit_cnt == 63) begin
                            state <= STOP;
                        end else begin
                            shift_reg <= shift_reg >> 1;
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 1;
                    end
                end

                STOP: begin
                    tx <= 1'b1;
                    if (clk_cnt == BIT_PERIOD - 1) begin
                        clk_cnt <= 0;
                        state <= IDLE;
                    end else begin
                        clk_cnt <= clk_cnt + 1;
                    end
                end
            endcase
        end
    end

endmodule
