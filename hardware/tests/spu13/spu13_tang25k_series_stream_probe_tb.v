`timescale 1ns / 1ps

// spu13_tang25k_series_stream_probe_tb.v — probe-top regression.
//
// Never ship an unsimulated probe top (SPU-4 probe lesson, 2026-07-08).
// Runs the board probe with fast timing parameters, decodes the UART
// status stream, and asserts the settled line is exactly:
//   SSTR:P V=8 M=1A E=00\r\n
// (8 golden vectors from the committed .mem all pass in silicon-identical
// logic, last normal vector used exactly 0x1A = 26 shared multiplies.)

module spu13_tang25k_series_stream_probe_tb;

    localparam CLKS_PER_BIT = 8;
    localparam LINE_LEN = 22;

    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    spu13_tang25k_series_stream_probe #(
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .START_DELAY(64),
        .LINE_PERIOD(6000)
    ) u_dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    always #10 clk = ~clk;

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
        expect_line[0]="S";  expect_line[1]="S";  expect_line[2]="T";
        expect_line[3]="R";  expect_line[4]=":";  expect_line[5]="P";
        expect_line[6]=" ";  expect_line[7]="V";  expect_line[8]="=";
        expect_line[9]="8";  expect_line[10]=" "; expect_line[11]="M";
        expect_line[12]="="; expect_line[13]="1"; expect_line[14]="A";
        expect_line[15]=" "; expect_line[16]="E"; expect_line[17]="=";
        expect_line[18]="0"; expect_line[19]="0";
        expect_line[20]=8'h0D; expect_line[21]=8'h0A;

        errors = 0;
        lines_seen = 0;
        settled = 1'b0;

        while (!settled && lines_seen < 200) begin
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

        if (led[1] !== 1'b0 || led[2] !== 1'b1) begin
            errors = errors + 1;
            $display("  led[1]=%b led[2]=%b, expected 0/1 (PASS)", led[1], led[2]);
        end

        if (errors == 0)
            $display("PASS: spu13_tang25k_series_stream_probe_tb (SSTR:P V=8 M=1A E=00, %0d lines)",
                     lines_seen);
        else
            $display("FAIL: spu13_tang25k_series_stream_probe_tb (%0d mismatches)", errors);
        $finish;
    end

    initial begin
        #6000000;
        $display("FAIL: spu13_tang25k_series_stream_probe_tb (watchdog: no settled line, state=%0d)",
                 u_dut.test_state);
        $finish;
    end

endmodule
