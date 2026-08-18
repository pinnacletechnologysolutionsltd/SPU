`timescale 1ns / 1ps

// spu4_uart_rx_bitsync_tb.v -- standalone RX-only test for
// spu4_uart_rx_bitsync.v, no wrapper/probe dependency. Bit-bangs bytes
// onto `rx` at CLKS_PER_BIT timing and checks the decoded rx_byte/
// rx_byte_valid pulses, including back-to-back bytes with no idle gap and
// a false-start glitch that must NOT be framed as a byte.

module spu4_uart_rx_bitsync_tb;

    localparam integer CLKS_PER_BIT = 8;  // small value, fast sim only

    reg clk = 0, rst_n = 0, rx = 1;
    wire rx_byte_valid;
    wire [7:0] rx_byte;

    spu4_uart_rx_bitsync #(.CLKS_PER_BIT(CLKS_PER_BIT)) dut (
        .clk(clk), .rst_n(rst_n), .rx(rx),
        .rx_byte_valid(rx_byte_valid), .rx_byte(rx_byte)
    );

    always #10 clk = ~clk;

    integer pass = 0, fail = 0;
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // Capture every decoded byte in arrival order.
    reg [7:0] captured [0:15];
    integer   captured_n = 0;
    always @(posedge clk) begin
        if (rx_byte_valid) begin
            captured[captured_n] = rx_byte;
            captured_n = captured_n + 1;
        end
    end

    task send_byte;
        input [7:0] b;
        integer i;
        begin
            rx = 1'b0;                                    // start bit
            repeat (CLKS_PER_BIT) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin
                rx = b[i];                                // LSB first
                repeat (CLKS_PER_BIT) @(posedge clk);
            end
            rx = 1'b1;                                     // stop bit
            repeat (CLKS_PER_BIT) @(posedge clk);
        end
    endtask

    integer before_n;

    initial begin
        #100 rst_n = 1; repeat (4) @(posedge clk);

        // ── Single bytes, including all-zero and all-one edge patterns ───
        before_n = captured_n;
        send_byte(8'h00);
        repeat (2) @(posedge clk);
        if (captured_n == before_n + 1 && captured[before_n] === 8'h00)
            ok("0x00 decoded");
        else bad("0x00 decode mismatch");

        before_n = captured_n;
        send_byte(8'hFF);
        repeat (2) @(posedge clk);
        if (captured_n == before_n + 1 && captured[before_n] === 8'hFF)
            ok("0xFF decoded");
        else bad("0xFF decode mismatch");

        before_n = captured_n;
        send_byte(8'h55);   // 01010101
        repeat (2) @(posedge clk);
        if (captured_n == before_n + 1 && captured[before_n] === 8'h55)
            ok("0x55 decoded");
        else bad("0x55 decode mismatch");

        before_n = captured_n;
        send_byte("Q");     // 0x51, the interactive probe's query lead byte
        repeat (2) @(posedge clk);
        if (captured_n == before_n + 1 && captured[before_n] === "Q")
            ok("'Q' (0x51) decoded");
        else bad("'Q' decode mismatch");

        // ── Back-to-back bytes, no idle gap between stop and next start ──
        before_n = captured_n;
        send_byte(8'hA5);
        send_byte(8'h3C);
        repeat (2) @(posedge clk);
        if (captured_n == before_n + 2 &&
            captured[before_n]   === 8'hA5 &&
            captured[before_n+1] === 8'h3C)
            ok("back-to-back bytes both decoded correctly");
        else bad("back-to-back byte decode mismatch");

        // ── False start: a low pulse shorter than half a bit period must
        // NOT be framed as a start bit. ───────────────────────────────────
        before_n = captured_n;
        rx = 1'b0;
        repeat (CLKS_PER_BIT / 4) @(posedge clk);   // well under CLKS_PER_BIT/2
        rx = 1'b1;
        repeat (4 * CLKS_PER_BIT) @(posedge clk);   // let it settle, well past a byte
        if (captured_n == before_n)
            ok("false-start glitch produced no spurious byte");
        else bad("false-start glitch was mis-framed as a byte");

        // Confirm the core still works after recovering from the glitch.
        before_n = captured_n;
        send_byte(8'h7E);
        repeat (2) @(posedge clk);
        if (captured_n == before_n + 1 && captured[before_n] === 8'h7E)
            ok("core recovers and decodes correctly after a glitch");
        else bad("core did not recover after a glitch");

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else            $display("FAIL");
        $finish;
    end

    initial begin
        #200_000;
        $display("FAIL: timeout");
        $display("FAIL");
        $finish;
    end

endmodule
