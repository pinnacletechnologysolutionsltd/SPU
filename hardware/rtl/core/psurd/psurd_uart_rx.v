// psurd_uart_rx.v — 8N1 UART receiver for the v0.3 RTL-0B loader (same ports/parameters as spu_uart_rx).
// Written under RTL-0B decision D2 because the shared spu_uart_rx failed gate B1 (no start-bit re-check:
// a sub-half-bit idle glitch yields a spurious 0xFF; no wait for mark after a framing error: a bad stop bit
// or a break misframes the following bytes). This receiver:
//  - synchronizes rx through two flops;
//  - arms only after seeing the line high (mark), and starts only on a falling edge while armed;
//  - re-checks the line at the centre of the start bit and drops the frame if it is high (glitch);
//  - samples 8 data bits LSB first at bit centres and checks the stop bit;
//  - after a frame, a new start needs a fresh falling edge (high sample, then low), so a bad stop bit
//    or a break gives one frame_err and nothing more until the line returns to mark. `armed` covers
//    reset with the line already low (no edge is invented from the reset value of rx_prev).
module psurd_uart_rx #(
    parameter CLK_HZ = 25000000,
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
    localparam S_IDLE = 2'd0, S_START = 2'd1, S_DATA = 2'd2, S_STOP = 2'd3;
    (* ASYNC_REG = "TRUE" *) reg rx_s1, rx_s2;   // two-flop synchronizer: marked so the tools place and analyse it as one
    reg rx_prev, armed;
    reg [1:0] state;
    reg [15:0] bit_cnt;
    reg [2:0] data_bit;
    reg [7:0] shift_reg;
    always @(posedge clk) begin rx_s1 <= rx; rx_s2 <= rx_s1; end
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data <= 8'd0; valid <= 1'b0; frame_err <= 1'b0; state <= S_IDLE; bit_cnt <= 16'd0;
            data_bit <= 3'd0; shift_reg <= 8'd0; rx_prev <= 1'b1; armed <= 1'b0;
        end else begin
            valid <= 1'b0; frame_err <= 1'b0; rx_prev <= rx_s2;
            case (state)
                S_IDLE: begin
                    if (rx_s2) armed <= 1'b1;                              // mark seen
                    else if (armed && rx_prev) begin                       // falling edge while armed
                        state <= S_START; bit_cnt <= 16'd0; data_bit <= 3'd0;
                    end
                end
                S_START: if (bit_cnt == HALF_BIT - 1) begin
                             bit_cnt <= 16'd0;
                             if (rx_s2) state <= S_IDLE;                   // glitch: line already high at mid-start
                             else state <= S_DATA;
                         end else bit_cnt <= bit_cnt + 16'd1;
                S_DATA: if (bit_cnt == BIT_CYCLES - 1) begin
                            bit_cnt <= 16'd0; shift_reg <= {rx_s2, shift_reg[7:1]};
                            if (data_bit == 3'd7) state <= S_STOP; else data_bit <= data_bit + 3'd1;
                        end else bit_cnt <= bit_cnt + 16'd1;
                S_STOP: if (bit_cnt == BIT_CYCLES - 1) begin
                            if (rx_s2) begin data <= shift_reg; valid <= 1'b1; end
                            else frame_err <= 1'b1;
                            state <= S_IDLE;                                // next start needs a falling edge
                        end else bit_cnt <= bit_cnt + 16'd1;
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
