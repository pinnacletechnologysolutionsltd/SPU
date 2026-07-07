`timescale 1ns / 1ps

// spu_a7_som_probe_tb.v -- A7 SOM/BMU probe: golden UART line check.
//
// Runs the board probe with fast timing parameters, decodes the UART
// stream, and asserts the line is exactly "SOM:P T:2 B:6 E:00\r\n" --
// the same golden fixture output the Tang 25K silicon run produced.
// Also checks the PASS/FAIL LEDs agree with the decoded line.

module spu_a7_som_probe_tb;

    localparam CLKS_PER_BIT = 8;      // fast baud for simulation
    localparam START_DELAY  = 64;
    localparam LINE_PERIOD  = 4000;
    localparam LINE_LEN     = 20;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    spu_a7_som_probe_top #(
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .START_DELAY(START_DELAY),
        .LINE_PERIOD(LINE_PERIOD)
    ) u_dut (
        .sys_clk(clk),
        .rst_n(rst_n),
        .led(led),
        .uart_tx(uart_tx)
    );

    always #5 clk = ~clk;

    // ── UART receiver (8N1, CLKS_PER_BIT clocks per bit) ─────────────
    reg [7:0] line_buf [0:LINE_LEN-1];
    integer   line_pos = 0;
    integer   lines_seen = 0;
    reg [7:0] rx_byte;
    integer   b;

    task uart_rx_byte;
        begin
            @(negedge uart_tx);                       // start bit edge
            repeat (CLKS_PER_BIT / 2) @(posedge clk); // centre of start bit
            for (b = 0; b < 8; b = b + 1) begin
                repeat (CLKS_PER_BIT) @(posedge clk);
                rx_byte[b] = uart_tx;
            end
            repeat (CLKS_PER_BIT) @(posedge clk);     // stop bit
        end
    endtask

    // Expected golden line (matches Tang 25K silicon output).
    reg [7:0] expect_line [0:LINE_LEN-1];
    initial begin
        expect_line[0]="S"; expect_line[1]="O"; expect_line[2]="M";
        expect_line[3]=":"; expect_line[4]="P"; expect_line[5]=" ";
        expect_line[6]="T"; expect_line[7]=":"; expect_line[8]="2";
        expect_line[9]=" "; expect_line[10]="B"; expect_line[11]=":";
        expect_line[12]="6"; expect_line[13]=" "; expect_line[14]="E";
        expect_line[15]=":"; expect_line[16]="0"; expect_line[17]="0";
        expect_line[18]=8'h0D; expect_line[19]=8'h0A;
    end

    integer errors = 0;
    integer i;

    initial begin
        rst_n = 1'b0;
        repeat (10) @(posedge clk);
        rst_n = 1'b1;

        // Capture two complete lines: the first may start mid-test
        // (status '.'), the second must be the settled PASS line.
        for (lines_seen = 0; lines_seen < 2; lines_seen = lines_seen + 1) begin
            line_pos = 0;
            while (line_pos < LINE_LEN) begin
                uart_rx_byte;
                line_buf[line_pos] = rx_byte;
                line_pos = line_pos + 1;
            end
        end

        for (i = 0; i < LINE_LEN; i = i + 1) begin
            if (line_buf[i] !== expect_line[i]) begin
                errors = errors + 1;
                $display("  byte %0d: got %02h ('%c') expected %02h ('%c')",
                         i, line_buf[i], line_buf[i],
                         expect_line[i], expect_line[i]);
            end
        end

        // LED sanity: PASS LED low (active-low), FAIL LED high.
        if (led[1] !== 1'b0) begin
            errors = errors + 1;
            $display("  led[1] (PASS, active-low) = %b, expected 0", led[1]);
        end
        if (led[2] !== 1'b1) begin
            errors = errors + 1;
            $display("  led[2] (FAIL, active-low) = %b, expected 1", led[2]);
        end

        if (errors == 0)
            $display("PASS: spu_a7_som_probe_tb (golden line SOM:P T:2 B:6 E:00)");
        else
            $display("FAIL: spu_a7_som_probe_tb (%0d mismatches)", errors);
        $finish;
    end

    // Watchdog: fail loudly rather than letting the runner time out.
    initial begin
        #2000000;
        $display("FAIL: spu_a7_som_probe_tb (watchdog: no UART line)");
        $finish;
    end

endmodule
