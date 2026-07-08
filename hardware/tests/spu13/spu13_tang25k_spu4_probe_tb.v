`timescale 1ns / 1ps

// spu13_tang25k_spu4_probe_tb.v -- SPU-4 silicon probe: golden UART check.
//
// Regression for the 2026-07-08 probe rewrite (multi-driven UART regs,
// latched run, unarmed busy-stable-low).  Runs the board probe with fast
// timing parameters, decodes status lines off the actual uart_tx pin, and
// asserts the settled line is exactly:
//   SPU4:P A=0000 B=0155 C=0155 D=0155\r\n

module spu13_tang25k_spu4_probe_tb;

    localparam CLKS_PER_BIT = 8;
    localparam LINE_LEN = 36;

    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    spu13_tang25k_spu4_probe #(
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .START_DELAY(64),
        .LINE_PERIOD(4000)
    ) u_dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    always #10 clk = ~clk;   // 50 MHz

    reg [7:0] line_buf [0:LINE_LEN-1];
    reg [7:0] expect_line [0:LINE_LEN-1];
    integer i, pos, lines_seen, errors;
    reg [7:0] b;
    reg settled;

    task rx_byte;
        begin
            @(negedge uart_tx);
            repeat (CLKS_PER_BIT + CLKS_PER_BIT/2) @(posedge clk);
            b = 8'd0;
            for (i = 0; i < 8; i = i + 1) begin
                b[i] = uart_tx;
                repeat (CLKS_PER_BIT) @(posedge clk);
            end
        end
    endtask

    initial begin
        expect_line[0]="S"; expect_line[1]="P"; expect_line[2]="U";
        expect_line[3]="4"; expect_line[4]=":"; expect_line[5]="P";
        expect_line[6]=" "; expect_line[7]="A"; expect_line[8]="=";
        expect_line[9]="0"; expect_line[10]="0"; expect_line[11]="0";
        expect_line[12]="0";
        expect_line[13]=" "; expect_line[14]="B"; expect_line[15]="=";
        expect_line[16]="0"; expect_line[17]="1"; expect_line[18]="5";
        expect_line[19]="5";
        expect_line[20]=" "; expect_line[21]="C"; expect_line[22]="=";
        expect_line[23]="0"; expect_line[24]="1"; expect_line[25]="5";
        expect_line[26]="5";
        expect_line[27]=" "; expect_line[28]="D"; expect_line[29]="=";
        expect_line[30]="0"; expect_line[31]="1"; expect_line[32]="5";
        expect_line[33]="5";
        expect_line[34]=8'h0D; expect_line[35]=8'h0A;

        errors = 0;
        lines_seen = 0;
        settled = 1'b0;

        // Decode lines until the verdict char leaves '.' (PASS/FAIL),
        // then capture one more full line as the settled artifact.
        while (!settled && lines_seen < 400) begin
            pos = 0;
            while (pos < LINE_LEN) begin
                rx_byte;
                line_buf[pos] = b;
                pos = pos + 1;
            end
            lines_seen = lines_seen + 1;
            if (line_buf[5] == "P" || line_buf[5] == "F") settled = 1'b1;
        end

        if (!settled) begin
            errors = errors + 1;
            $display("FAIL: no verdict line within %0d lines", lines_seen);
        end else begin
            for (i = 0; i < LINE_LEN; i = i + 1) begin
                if (line_buf[i] !== expect_line[i]) begin
                    errors = errors + 1;
                    $display("  byte %0d: got %02h ('%c') expected %02h ('%c')",
                             i, line_buf[i], line_buf[i],
                             expect_line[i], expect_line[i]);
                end
            end
        end

        // LED sanity: PASS asserted, FAIL deasserted (active-low pair).
        if (led[1] !== 1'b0 || led[2] !== 1'b1) begin
            errors = errors + 1;
            $display("  led[1]=%b led[2]=%b, expected 0/1 (PASS)", led[1], led[2]);
        end

        if (errors == 0)
            $display("PASS: spu13_tang25k_spu4_probe_tb (SPU4:P A=0000 B=0155 C=0155 D=0155, %0d lines)",
                     lines_seen);
        else
            $display("FAIL: spu13_tang25k_spu4_probe_tb (%0d mismatches)", errors);
        $finish;
    end

    initial begin
        #40000000;  // 40 ms: covers the ~9 ms serial-multiplier program run
        $display("FAIL: spu13_tang25k_spu4_probe_tb (watchdog: no settled line)");
        $finish;
    end

endmodule
