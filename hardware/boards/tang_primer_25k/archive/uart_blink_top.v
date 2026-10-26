// uart_blink_top.v — Minimal UART + LED test for Tang Primer 25K
module uart_blink_top (
    input  wire        sys_clk,
    output reg         uart_tx,
    output wire [2:0]  led
);
    // UART: send "SPU\n" every ~1 second at 115200
    localparam CLKS_PER_BIT = 50000000 / 115200;
    localparam MSG_PERIOD   = 50000000;  // 1 Hz

    reg [31:0] msg_timer = 0;
    reg        send_trigger = 0;
    always @(posedge sys_clk) begin
        msg_timer <= msg_timer + 1;
        send_trigger <= 0;
        if (msg_timer == MSG_PERIOD - 1) begin
            msg_timer <= 0;
            send_trigger <= 1;
        end
    end

    reg [7:0]  tx_byte;
    reg        tx_busy = 0;
    reg [15:0] baud_cnt = 0;
    reg [3:0]  bit_cnt = 0;
    reg [3:0]  char_idx = 0;

    always @(posedge sys_clk) begin
        if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1;
            end else begin
                baud_cnt <= 0;
                uart_tx <= (bit_cnt < 8) ? tx_byte[bit_cnt] : 1'b1;
                if (bit_cnt == 9) begin
                    tx_busy <= 0;
                    bit_cnt <= 0;
                    if (char_idx == 4) char_idx <= 0;
                    else char_idx <= char_idx + 1;
                end else begin
                    bit_cnt <= bit_cnt + 1;
                end
            end
        end else if (send_trigger) begin
            case (char_idx)
                0: tx_byte <= "S";
                1: tx_byte <= "P";
                2: tx_byte <= "U";
                3: tx_byte <= 8'h0D;  // CR
                4: tx_byte <= 8'h0A;  // LF
            endcase
            uart_tx <= 1'b0;  // start bit
            tx_busy <= 1;
            baud_cnt <= 0;
            bit_cnt <= 0;
        end
    end

    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~blink[23];
    assign led[2] = ~blink[22];
endmodule
