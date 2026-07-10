// spu13_tang25k_irotc_probe_tb.v — IROTC Engine Probe Testbench
//
// Instantiates the probe top, monitors UART TX for the expected
// PASS line, and decodes it bit-for-bit to verify the full
// golden-vector sequence completes correctly.

`timescale 1ns/1ps

module spu13_tang25k_irotc_probe_tb;
    reg clk = 0;
    wire [2:0] led;
    wire uart_tx;

    // CLK_FREQ shrunk so the 0.5 s boot settle + 0.2 s line gap become
    // ~140k cycles and the real UART line is decodable inside the 5 s
    // suite budget. CLKS_PER_BIT is independent (fixed 434).
    spu13_tang25k_irotc_probe #(.CLK_FREQ(200000)) dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    always #10 clk = ~clk;  // 50 MHz

    // ── UART decoder (8N1, 115200 baud) ────────────────────────────
    localparam CLKS_PER_BIT = 434;

    reg [7:0] rx_char = 0;
    reg       rx_valid = 0;
    reg [3:0] rx_bit_idx = 0;   // 0..9: start + 8 data + stop
    reg [15:0] rx_timer = 0;
    reg        rx_active = 0;
    reg        rx_prev = 1;
    reg [7:0]  rx_shift = 0;

    // Accumulate the output line as ASCII
    reg [7:0] line_chars [0:13];
    reg [3:0] line_idx = 0;

    always @(posedge clk) begin
        rx_prev <= uart_tx;
        rx_valid <= 0;

        if (!rx_active && uart_tx == 0 && rx_prev == 1) begin
            // Start bit detected
            rx_active <= 1;
            rx_timer <= CLKS_PER_BIT / 2;  // sample mid-bit
            rx_bit_idx <= 0;
            rx_shift <= 0;
        end

        if (rx_active) begin
            if (rx_timer == 0) begin
                // Sample at mid-bit
                if (rx_bit_idx == 0) begin
                    // Start bit — verify
                    if (uart_tx != 0) rx_active <= 0;
                end else if (rx_bit_idx <= 8) begin
                    // Data bit
                    rx_shift <= {uart_tx, rx_shift[7:1]};
                end else begin
                    // Stop bit — character complete
                    rx_valid <= 1;
                    rx_char <= rx_shift;
                    rx_active <= 0;
                end
                rx_bit_idx <= rx_bit_idx + 1;
                rx_timer <= CLKS_PER_BIT - 1;
            end else begin
                rx_timer <= rx_timer - 1;
            end
        end
    end

    // Capture line characters
    always @(posedge clk) begin
        if (rx_valid) begin
            line_chars[line_idx] <= rx_char;
            if (rx_char == 8'h0A || line_idx == 13)  // LF = end of line
                line_idx <= 0;
            else if (line_idx < 13)
                line_idx <= line_idx + 1;
        end
    end

    // ── Main test — wait for UART output ───────────────────────────
    reg [7:0] actual_line [0:13];
    integer i;
    reg pass_seen = 0;
    reg fail_seen = 0;
    reg line_done = 0;

    always @(posedge clk) begin
        if (rx_valid && rx_char == 8'h0A) begin
            line_done <= 1;
            for (i = 0; i < 14; i = i + 1)
                actual_line[i] = line_chars[i];

            if (line_chars[0] == "I" && line_chars[1] == "R" &&
                line_chars[2] == "O" && line_chars[3] == "T" &&
                line_chars[4] == "C" && line_chars[5] == ":") begin
                if (line_chars[6] == "P")     pass_seen <= 1;
                else if (line_chars[6] == "F") fail_seen <= 1;
            end
        end
    end

    localparam TIMEOUT = 10000000;  // 10M cycles = 200ms at 50MHz

    integer cyc = 0;
    always @(posedge clk) begin
        cyc <= cyc + 1;
        if (cyc == TIMEOUT) begin
            $display("FAIL: timeout (%0d cycles) — no UART line received", TIMEOUT);
            $display("  test_state=%0d led=%b", dut.test_state, led);
            $finish;
        end
        if (pass_seen) begin
            // Belt and braces: the decoded 'P' must agree with the FSM
            // state and a clean error code (E=00 on the wire).
            if (dut.test_state !== 4'd14 || dut.err_code !== 8'd0) begin
                $display("FAIL: UART said P but FSM state=%0d err=%02h",
                         dut.test_state, dut.err_code);
                $finish;
            end
            $display("IROTC ENGINE PROBE: PASS");
            $display("  UART output: %s%s%s%s%s%s%s%s%s%s%s%s%s%s",
                actual_line[0], actual_line[1], actual_line[2], actual_line[3],
                actual_line[4], actual_line[5], actual_line[6], actual_line[7],
                actual_line[8], actual_line[9], actual_line[10], actual_line[11],
                actual_line[12], actual_line[13]);
            $finish;
        end
        if (fail_seen) begin
            $display("FAIL: probe reported failure");
            $display("  UART output: %s%s%s%s%s%s%s%s%s%s%s%s%s%s",
                actual_line[0], actual_line[1], actual_line[2], actual_line[3],
                actual_line[4], actual_line[5], actual_line[6], actual_line[7],
                actual_line[8], actual_line[9], actual_line[10], actual_line[11],
                actual_line[12], actual_line[13]);
            $finish;
        end
    end
endmodule
