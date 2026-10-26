// spu_t1d_diag_uart_tx.v -- independent fixed-record UART transmitter.
//
// This module is deliberately TX-only. It does not share the T1d receiver
// implementation and accepts a complete 128-bit record before transmission.
// Records are emitted as 16 bytes, 8N1, LSB first, at 115200 baud from the
// 25 MHz pixel clock (217 clocks per bit).
// CC0 1.0 Universal.

module spu_t1d_diag_uart_tx #(
    parameter integer BIT_CYCLES = 217
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [127:0] record_data,
    input  wire         record_valid,
    output wire         record_ready,
    output reg          tx
);

    reg [127:0] record_latched;
    reg         busy;
    reg [7:0]   bit_cycle;
    reg [3:0]   frame_bit;
    reg [3:0]   byte_index;

    assign record_ready = !busy;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            record_latched <= 128'd0;
            busy           <= 1'b0;
            bit_cycle      <= 8'd0;
            frame_bit      <= 4'd0;
            byte_index     <= 4'd0;
            tx             <= 1'b1;
        end else if (!busy) begin
            tx <= 1'b1;
            if (record_valid) begin
                record_latched <= record_data;
                busy           <= 1'b1;
                bit_cycle      <= 8'd0;
                frame_bit      <= 4'd0;
                byte_index     <= 4'd0;
                tx             <= 1'b0;
            end
        end else if (bit_cycle == BIT_CYCLES - 1) begin
            bit_cycle <= 8'd0;
            if (frame_bit == 4'd9) begin
                if (byte_index == 4'd15) begin
                    busy <= 1'b0;
                    tx   <= 1'b1;
                end else begin
                    byte_index <= byte_index + 4'd1;
                    frame_bit  <= 4'd0;
                    tx         <= 1'b0;
                end
            end else begin
                frame_bit <= frame_bit + 4'd1;
                if (frame_bit == 4'd8)
                    tx <= 1'b1;
                else
                    tx <= record_latched[(byte_index * 8) + frame_bit];
            end
        end else begin
            bit_cycle <= bit_cycle + 8'd1;
        end
    end

endmodule
