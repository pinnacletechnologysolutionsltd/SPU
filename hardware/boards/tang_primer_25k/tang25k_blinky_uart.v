// tang25k_blinky_uart.v -- bench sanity probe, no core logic.
//
// Three LEDs blink at ~1.5/3/6 Hz and the UART repeats "BLINK\r\n" at
// 115200 baud roughly three times a second. Isolates the board path
// (bitstream load, clock, LED pins, C3->BL616 UART) from all SPU RTL.

module tang25k_blinky_uart (
    input  wire       sys_clk,   // 50 MHz crystal (E2)
    output wire [2:0] led,       // active-low (L6/E8/D7)
    output wire       uart_tx    // C3 -> BL616 USB-CDC
);
    localparam CLKS_PER_BIT = 434;   // 115200 baud at 50 MHz
    localparam MSG_LEN = 7;

    reg [25:0] cnt = 26'd0;
    always @(posedge sys_clk) cnt <= cnt + 1'b1;
    assign led = ~{cnt[23], cnt[24], cnt[25]};   // three distinct rates

    function [7:0] ch;
        input [2:0] i;
        begin
            case (i)
                3'd0: ch = "B";
                3'd1: ch = "L";
                3'd2: ch = "I";
                3'd3: ch = "N";
                3'd4: ch = "K";
                3'd5: ch = 8'h0D;
                default: ch = 8'h0A;
            endcase
        end
    endfunction

    reg [9:0]  shifter = 10'h3FF;   // idle high
    reg [3:0]  bitn = 4'd0;
    reg [15:0] baud = 16'd0;
    reg [2:0]  msg_idx = 3'd0;
    reg        sending = 1'b0;
    reg [23:0] gap = 24'd0;

    assign uart_tx = shifter[0];

    always @(posedge sys_clk) begin
        if (sending) begin
            if (baud == CLKS_PER_BIT - 1) begin
                baud <= 16'd0;
                shifter <= {1'b1, shifter[9:1]};
                if (bitn == 4'd9) begin
                    bitn <= 4'd0;
                    if (msg_idx == MSG_LEN - 1) begin
                        msg_idx <= 3'd0;
                        sending <= 1'b0;
                        gap <= 24'd0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                        shifter <= {1'b1, ch(msg_idx + 3'd1), 1'b0};
                    end
                end else begin
                    bitn <= bitn + 1'b1;
                end
            end else begin
                baud <= baud + 1'b1;
            end
        end else if (gap == 24'hFFFFFF) begin   // ~0.3 s between lines
            sending <= 1'b1;
            baud <= 16'd0;
            bitn <= 4'd0;
            shifter <= {1'b1, ch(3'd0), 1'b0};  // start bit + "B"
        end else begin
            gap <= gap + 1'b1;
        end
    end

endmodule
