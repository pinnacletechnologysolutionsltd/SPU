// uart_fixed_msg.v — Minimal test: fixed message, same UART as QLOD+HEX probe
module uart_fixed_msg (
    input  wire        sys_clk,
    output reg         uart_tx,
    output wire [2:0]  led
);
    reg [31:0] msg_timer = 0;
    reg [7:0]  tx_byte;
    reg        tx_busy = 0;
    reg [15:0] baud_cnt = 0;
    reg [3:0]  bit_cnt = 0;
    reg [3:0]  char_idx = 0;

    always @(posedge sys_clk) begin
        msg_timer <= msg_timer + 1;
        if (msg_timer == 49999999) msg_timer <= 0;
        if (tx_busy) begin
            baud_cnt <= baud_cnt + 1;
            if (baud_cnt == 16'd433) begin
                baud_cnt <= 0;
                bit_cnt <= bit_cnt + 1;
                if (bit_cnt < 8)
                    uart_tx <= tx_byte[bit_cnt];
                else if (bit_cnt == 8)
                    uart_tx <= 1'b1;
                else
                    tx_busy <= 0;
            end
        end else if (msg_timer == 49999999) begin
            case (char_idx)
                0: tx_byte <= "T";
                1: tx_byte <= "S";
                2: tx_byte <= "T";
                3: tx_byte <= 8'h0D;
                4: tx_byte <= 8'h0A;
                default: tx_byte <= " ";
            endcase
            uart_tx <= 1'b0;
            tx_busy <= 1;
            baud_cnt <= 0;
            bit_cnt <= 0;
            if (char_idx < 4) char_idx <= char_idx + 1;
            else char_idx <= 0;
        end
    end

    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = 0;
    assign led[2] = 0;
endmodule
