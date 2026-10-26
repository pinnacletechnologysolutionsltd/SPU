// spu_uart_rx.v — minimal UART byte receiver (simulation-friendly)
//
// After detecting start-bit falling edge, samples at centre of each bit
// (BIT_CYCLES/2 offset, then BIT_CYCLES spacing). Checks stop bit.
module spu_uart_rx #(
    parameter CLK_HZ = 12000000,
    parameter BAUD   = 115200
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx,
    output reg  [7:0] data,
    output reg        valid,
    output reg        frame_err
);
    localparam BIT_CYCLES  = CLK_HZ / BAUD;
    localparam HALF_BIT    = BIT_CYCLES / 2;

    // Synchroniser
    reg rx_s1, rx_s2;
    always @(posedge clk) begin
        rx_s1 <= rx;
        rx_s2 <= rx_s1;
    end

    localparam S_IDLE  = 2'd0;
    localparam S_START = 2'd1;
    localparam S_DATA  = 2'd2;
    localparam S_STOP  = 2'd3;

    reg [1:0]  state;
    reg [15:0] bit_cnt;
    reg [2:0]  data_bit;
    reg [7:0]  shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data      <= 8'd0;
            valid     <= 1'b0;
            frame_err <= 1'b0;
            state     <= S_IDLE;
            bit_cnt   <= 16'd0;
            data_bit  <= 3'd0;
            shift_reg <= 8'd0;
        end else begin
            valid     <= 1'b0;
            frame_err <= 1'b0;

            case (state)
                S_IDLE: begin
                    if (!rx_s2) begin
                        state    <= S_START;
                        bit_cnt  <= 16'd0;
                        data_bit <= 3'd0;
                    end
                end

                S_START: begin
                    // Wait until centre of start bit (half bit period)
                    if (bit_cnt == HALF_BIT - 1) begin
                        bit_cnt <= 16'd0;
                        state   <= S_DATA;
                    end else begin
                        bit_cnt <= bit_cnt + 16'd1;
                    end
                end

                S_DATA: begin
                    if (bit_cnt == BIT_CYCLES - 1) begin
                        bit_cnt   <= 16'd0;
                        shift_reg <= {rx_s2, shift_reg[7:1]};
                        if (data_bit == 3'd7) begin
                            state <= S_STOP;
                        end else begin
                            data_bit <= data_bit + 3'd1;
                        end
                    end else begin
                        bit_cnt <= bit_cnt + 16'd1;
                    end
                end

                S_STOP: begin
                    if (bit_cnt == BIT_CYCLES - 1) begin
                        if (rx_s2) begin
                            data  <= shift_reg;
                            valid <= 1'b1;
                        end else begin
                            frame_err <= 1'b1;
                        end
                        state <= S_IDLE;
                    end else begin
                        bit_cnt <= bit_cnt + 16'd1;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
