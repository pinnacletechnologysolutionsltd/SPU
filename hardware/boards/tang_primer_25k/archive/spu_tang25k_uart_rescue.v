module spu_tang25k_uart_rescue (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam integer CLK_FREQ      = 50000000;
    localparam integer CLKS_PER_BIT  = 434;
    localparam integer LINE_INTERVAL = CLK_FREQ / 2;
    localparam integer MSG_LAST      = 8;

    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) begin
        blink_cnt <= blink_cnt + 1'b1;
    end

    assign led[0] = ~blink_cnt[24];
    assign led[1] = ~blink_cnt[23];
    assign led[2] = ~blink_cnt[22];

    function [7:0] msg_byte;
        input [3:0] idx;
        begin
            case (idx)
                4'd0: msg_byte = "U";
                4'd1: msg_byte = "A";
                4'd2: msg_byte = "R";
                4'd3: msg_byte = "T";
                4'd4: msg_byte = " ";
                4'd5: msg_byte = "O";
                4'd6: msg_byte = "K";
                4'd7: msg_byte = 8'h0D;
                4'd8: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits_remaining = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg [24:0] line_cnt = 25'd0;
    reg [3:0]  msg_idx = 4'd0;
    reg        tx_busy = 1'b0;

    assign uart_tx = tx_shift[0];

    always @(posedge sys_clk) begin
        if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1'b1;
            end else begin
                baud_cnt <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (tx_bits_remaining == 4'd1) begin
                    tx_busy <= 1'b0;
                    tx_bits_remaining <= 4'd0;
                    if (msg_idx == MSG_LAST) begin
                        msg_idx <= 4'd0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                    end
                end else begin
                    tx_bits_remaining <= tx_bits_remaining - 1'b1;
                end
            end
        end else if (msg_idx != 4'd0) begin
            tx_shift <= {1'b1, msg_byte(msg_idx), 1'b0};
            tx_bits_remaining <= 4'd10;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b1;
        end else if (line_cnt < LINE_INTERVAL - 1) begin
            line_cnt <= line_cnt + 1'b1;
            tx_shift <= 10'h3FF;
        end else begin
            line_cnt <= 25'd0;
            tx_shift <= {1'b1, msg_byte(4'd0), 1'b0};
            tx_bits_remaining <= 4'd10;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b1;
        end
    end
endmodule
