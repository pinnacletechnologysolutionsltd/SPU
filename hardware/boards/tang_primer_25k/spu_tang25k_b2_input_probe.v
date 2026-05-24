// Tang Primer 25K B2/J3 pin-14 input-only probe.
//
// Leaves B2 high-Z and reports the sampled pad level over UART. Use this with
// an external jumper from the B2 header pin to GND to verify the input buffer.

module spu_tang25k_b2_input_probe (
    input  wire sys_clk,
    output wire [2:0] led,
    output wire uart_tx,
    output wire uart_tx_telemetry,
    input  wire b2_probe
);
    localparam integer CLKS_PER_BIT = 434;        // 50 MHz / 115200
    localparam integer REPORT_TICKS = 12_500_000; // 250 ms

    reg [23:0] report_cnt = 24'd0;
    reg        emit_line = 1'b0;
    reg        b2_sample = 1'b0;
    reg        b2_latch = 1'b0;

    always @(posedge sys_clk) begin
        b2_sample <= b2_probe;
        emit_line <= 1'b0;

        if (report_cnt == REPORT_TICKS - 1) begin
            report_cnt <= 24'd0;
            b2_latch <= b2_sample;
            emit_line <= 1'b1;
        end else begin
            report_cnt <= report_cnt + 1'b1;
        end
    end

    // LEDs are active-low. LED0 on means the sampled B2 level is high.
    assign led = {2'b11, ~b2_latch};

    wire [31:0] report_word = {28'hB100000, 3'b000, b2_latch};

    function [7:0] hex_digit;
        input [3:0] value;
        begin
            hex_digit = (value < 4'd10) ? (8'h30 + value) : (8'h41 + value - 4'd10);
        end
    endfunction

    reg [3:0] msg_idx = 4'd0;
    reg [7:0] tx_byte = 8'h00;
    reg [9:0] tx_shift = 10'h3ff;
    reg [15:0] baud_cnt = 16'd0;
    reg [3:0] bit_cnt = 4'd0;
    reg tx_busy = 1'b0;
    reg line_pending = 1'b0;

    assign uart_tx = tx_shift[0];
    assign uart_tx_telemetry = tx_shift[0];

    always @* begin
        case (msg_idx)
            4'd0:  tx_byte = "M";
            4'd1:  tx_byte = ":";
            4'd2:  tx_byte = hex_digit(report_word[31:28]);
            4'd3:  tx_byte = hex_digit(report_word[27:24]);
            4'd4:  tx_byte = hex_digit(report_word[23:20]);
            4'd5:  tx_byte = hex_digit(report_word[19:16]);
            4'd6:  tx_byte = hex_digit(report_word[15:12]);
            4'd7:  tx_byte = hex_digit(report_word[11:8]);
            4'd8:  tx_byte = hex_digit(report_word[7:4]);
            4'd9:  tx_byte = hex_digit(report_word[3:0]);
            4'd10: tx_byte = " ";
            4'd11: tx_byte = "A";
            4'd12: tx_byte = ":";
            4'd13: tx_byte = "B";
            4'd14: tx_byte = 8'h0d;
            4'd15: tx_byte = 8'h0a;
            default: tx_byte = 8'h20;
        endcase
    end

    always @(posedge sys_clk) begin
        if (emit_line) begin
            line_pending <= 1'b1;
        end

        if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1'b1;
            end else begin
                baud_cnt <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (bit_cnt == 4'd9) begin
                    tx_busy <= 1'b0;
                    bit_cnt <= 4'd0;
                    if (msg_idx == 4'd15) begin
                        msg_idx <= 4'd0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                    end
                end else begin
                    bit_cnt <= bit_cnt + 1'b1;
                end
            end
        end else if (line_pending) begin
            tx_shift <= {1'b1, tx_byte, 1'b0};
            tx_busy <= 1'b1;
            baud_cnt <= 16'd0;
            bit_cnt <= 4'd0;
            if (msg_idx == 4'd15) begin
                line_pending <= 1'b0;
            end
        end
    end
endmodule
