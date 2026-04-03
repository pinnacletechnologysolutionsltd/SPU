// spu_smoke_uart.v — SPU-13 iCEsugar Level 1 Smoke Test
// Target : iCEsugar v1.5 (iCE40UP5K-SG48)
// Purpose: Send "SPU-13 LAMINAR\r\n" over UART at 115200 baud after reset.
//          UART TX is routed via the Type-C CH552 USB bridge.
//
// If you see the string in a terminal (picocom / minicom / screen) the
// UART bridge is alive and the FPGA fabric is executing correctly.
// The RGB LED mirrors UART activity (blue=idle, green=transmitting).

`default_nettype none

module spu_smoke_uart (
    input  wire clk,       // 12 MHz
    output wire uart_tx,
    output wire LED_R,
    output wire LED_G,
    output wire LED_B
);

    // -------------------------------------------------------------------
    // Baud clock divider: 12_000_000 / 115200 ≈ 104 cycles per bit
    // -------------------------------------------------------------------
    localparam BAUD_DIV = 104;

    // Message: "SPU-13 LAMINAR\r\n" (17 bytes)
    localparam MSG_LEN = 17;
    reg [7:0] msg [0:MSG_LEN-1];
    initial begin
        msg[0]  = 8'h53; // S
        msg[1]  = 8'h50; // P
        msg[2]  = 8'h55; // U
        msg[3]  = 8'h2D; // -
        msg[4]  = 8'h31; // 1
        msg[5]  = 8'h33; // 3
        msg[6]  = 8'h20; // space
        msg[7]  = 8'h4C; // L
        msg[8]  = 8'h41; // A
        msg[9]  = 8'h4D; // M
        msg[10] = 8'h49; // I
        msg[11] = 8'h4E; // N
        msg[12] = 8'h41; // A
        msg[13] = 8'h52; // R
        msg[14] = 8'h0D; // CR
        msg[15] = 8'h0A; // LF
        msg[16] = 8'h00; // null sentinel
    end

    // -------------------------------------------------------------------
    // State machine: wait 1 s, transmit, wait 1 s, repeat
    // -------------------------------------------------------------------
    localparam PAUSE_CYCLES = 12_000_000; // 1 second pause

    reg [23:0] pause_cnt  = 0;
    reg [3:0]  msg_idx    = 0;
    reg [3:0]  bit_idx    = 0;   // 0=start, 1-8=data, 9=stop
    reg [6:0]  baud_cnt   = 0;
    reg        tx_reg     = 1'b1;
    reg        transmit   = 1'b0;

    // UART TX shift register
    reg [9:0]  shift;

    always @(posedge clk) begin
        if (!transmit) begin
            // Pause between messages
            if (pause_cnt == PAUSE_CYCLES - 1) begin
                pause_cnt <= 0;
                msg_idx   <= 0;
                transmit  <= 1'b1;
                // Load first byte frame: {stop, data[7:0], start}
                shift     <= {1'b1, msg[0], 1'b0};
                bit_idx   <= 0;
                baud_cnt  <= 0;
            end else begin
                pause_cnt <= pause_cnt + 1;
                tx_reg    <= 1'b1;  // idle high
            end
        end else begin
            if (baud_cnt == BAUD_DIV - 1) begin
                baud_cnt <= 0;
                tx_reg   <= shift[0];
                shift    <= {1'b1, shift[9:1]};  // shift right
                if (bit_idx == 9) begin
                    // Frame done
                    bit_idx <= 0;
                    if (msg_idx == MSG_LEN - 1) begin
                        transmit <= 1'b0;  // message done
                        pause_cnt <= 0;
                    end else begin
                        msg_idx <= msg_idx + 1;
                        shift   <= {1'b1, msg[msg_idx + 1], 1'b0};
                    end
                end else begin
                    bit_idx <= bit_idx + 1;
                end
            end else begin
                baud_cnt <= baud_cnt + 1;
            end
        end
    end

    assign uart_tx = tx_reg;

    // -------------------------------------------------------------------
    // RGB: Blue=idle, Green=transmitting
    // -------------------------------------------------------------------
    SB_RGBA_DRV #(
        .CURRENT_MODE ("0b0"),
        .RGB0_CURRENT ("0b000001"),
        .RGB1_CURRENT ("0b000001"),
        .RGB2_CURRENT ("0b000001")
    ) u_rgb (
        .CURREN   (1'b1),
        .RGBLEDEN (1'b1),
        .RGB0PWM  (1'b0),           // Red off
        .RGB1PWM  (transmit),       // Green when TX active
        .RGB2PWM  (!transmit),      // Blue when idle
        .RGB0     (LED_R),
        .RGB1     (LED_G),
        .RGB2     (LED_B)
    );

endmodule
