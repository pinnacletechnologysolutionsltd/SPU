`timescale 1ns / 1ps

// spu4_uart_rx_bitsync.v -- reusable bit-sampling UART RX core for SPU-4
// bench probes. Mirrors the TX engine's CLKS_PER_BIT baud-rate counter
// style already used by spu13_tang25k_spu4_som_edge_probe.v and
// spu13_tang25k_spu4_abi_probe.v (both TX-only), for the receive
// direction those probes don't need.
//
// 8N1, LSB-first -- matches every UART TX engine already used in this
// repo. No parity, no framing-error reporting beyond silent
// resynchronisation to IDLE on a bad start bit (a false-start glitch
// bails back to IDLE rather than framing garbage as a byte); a caller
// needing more builds on top of this core, not into it.
//
// Factored as its own module (unlike the fixed probe, which inlines its
// TX engine into the board-specific top file) because RX has none of that
// engine's "single-owner" contention concern, and standalone testability
// matters more here -- see spu4_uart_rx_bitsync_tb.v.

module spu4_uart_rx_bitsync #(
    parameter CLKS_PER_BIT = 434   // 115200 baud at 50 MHz
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx,             // async UART line, synchronised here
    output reg        rx_byte_valid,  // one-cycle pulse
    output reg [7:0]  rx_byte
);

    // Two-flop synchroniser for the async rx pin -- same discipline as the
    // reset synchronisers elsewhere in this repo (see spu4_customer_wrapper.v's
    // G6 note on the three-week outage a raw async input caused).
    reg rx_meta, rx_sync;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
        end else begin
            rx_meta <= rx;
            rx_sync <= rx_meta;
        end
    end

    localparam S_IDLE  = 2'd0;
    localparam S_START = 2'd1;
    localparam S_DATA  = 2'd2;
    localparam S_STOP  = 2'd3;

    reg [1:0]  state;
    reg [15:0] clk_cnt;
    reg [2:0]  bit_idx;
    reg [7:0]  shift;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state         <= S_IDLE;
            clk_cnt       <= 16'd0;
            bit_idx       <= 3'd0;
            shift         <= 8'd0;
            rx_byte_valid <= 1'b0;
            rx_byte       <= 8'd0;
        end else begin
            rx_byte_valid <= 1'b0;   // one-cycle pulse, default low
            case (state)
                S_IDLE: begin
                    clk_cnt <= 16'd0;
                    bit_idx <= 3'd0;
                    if (rx_sync == 1'b0) state <= S_START;
                end
                S_START: begin
                    // Sample at mid-start-bit; a glitch that isn't really a
                    // start bit bails back to IDLE rather than framing
                    // garbage as a byte.
                    if (clk_cnt < (CLKS_PER_BIT / 2) - 1) begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end else begin
                        clk_cnt <= 16'd0;
                        if (rx_sync == 1'b0) state <= S_DATA;
                        else                 state <= S_IDLE;
                    end
                end
                S_DATA: begin
                    // Entered at mid-start-bit; waiting one more full bit
                    // period lands the first sample at mid-bit-0, then
                    // every subsequent bit period lands mid-bit thereafter.
                    if (clk_cnt < CLKS_PER_BIT - 1) begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end else begin
                        clk_cnt <= 16'd0;
                        shift   <= {rx_sync, shift[7:1]};   // LSB first
                        if (bit_idx == 3'd7) begin
                            bit_idx <= 3'd0;
                            state   <= S_STOP;
                        end else begin
                            bit_idx <= bit_idx + 1'b1;
                        end
                    end
                end
                S_STOP: begin
                    // No level gating on the stop bit by design (see header)
                    // -- just wait out the period and latch.
                    if (clk_cnt < CLKS_PER_BIT - 1) begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end else begin
                        clk_cnt       <= 16'd0;
                        rx_byte       <= shift;
                        rx_byte_valid <= 1'b1;
                        state         <= S_IDLE;
                    end
                end
                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
