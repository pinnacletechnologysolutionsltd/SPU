// spu_uart_tx.v — minimal UART byte transmitter
// Sends one byte (start + 8 data + stop), asserts done pulse when idle.
module spu_uart_tx #(
    parameter CLK_HZ = 12000000,
    parameter BAUD   = 115200
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] data,
    input  wire       send,
    output reg        tx,
    output reg        busy,
    output reg        done
);
    localparam BIT_CYCLES = CLK_HZ / BAUD;

    reg [15:0] cycle_cnt;
    reg [3:0]  bit_idx;   // counts 10→0: 10 bits (start + 8 data + stop)
    reg [9:0]  shift_reg; // {stop=1, data[7:0], start=0} — shifted right each bit

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx        <= 1'b1;
            busy      <= 1'b0;
            done      <= 1'b0;
            cycle_cnt <= 16'd0;
            bit_idx   <= 4'd0;
            shift_reg <= 10'd0;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                if (send) begin
                    shift_reg <= {1'b1, data, 1'b0};
                    bit_idx   <= 4'd10;
                    cycle_cnt <= 16'd0;
                    busy      <= 1'b1;
                end
            end else begin
                if (cycle_cnt < BIT_CYCLES - 1) begin
                    cycle_cnt <= cycle_cnt + 16'd1;
                end else begin
                    cycle_cnt <= 16'd0;
                    if (bit_idx > 0) begin
                        tx        <= shift_reg[0];
                        shift_reg <= {1'b1, shift_reg[9:1]};
                        bit_idx   <= bit_idx - 4'd1;
                    end else begin
                        busy  <= 1'b0;
                        done  <= 1'b1;
                    end
                end
            end
        end
    end

endmodule
