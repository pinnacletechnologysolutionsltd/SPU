// spu13_tang25k_satellite_aggregator_probe_tb.v — Testbench for the
// Tang 25K 13-satellite aggregator probe top.
//
// Runs the probe's own self-check FSM to completion with accelerated
// parameters (8 clocks per whisper UART bit, 2500-cycle whisper period
// instead of the board-real 108.5 clocks/bit and 30000-cycle period) so
// the full sequence — 4 driven emitters report, status/worst checks,
// 9 idle lines trip the 3-miss deadman, command-bus shift — fits the
// test runner's time budget. Same whitebox pattern as
// spu13_tang25k_rotc_probe_tb.v: peek probe_state/fail_code
// hierarchically rather than decoding the report UART.

`timescale 1ns/1ps

module spu13_tang25k_satellite_aggregator_probe_tb;

    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    integer i;
    integer errors = 0;

    always #5 clk = ~clk;

    // Accelerated ratio: CLK_HZ/BAUD = 8 clocks per whisper bit.
    // One 18-byte frame = 180 bits * 8 = 1440 whisper cycles; the
    // 2500-cycle period keeps the same >60% idle margin the board-real
    // parameters have (30000 vs ~19531).
    spu13_tang25k_satellite_aggregator_probe #(
        .WHISPER_CLK_HZ(8000),
        .WHISPER_BAUD(1000),
        .PERIOD_CYCLES(2500)
    ) dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    localparam S_PASS = 4'd9;

    initial begin
        $display("=== spu13_tang25k_satellite_aggregator_probe_tb ===");

        // Self-check completes around 8*PERIOD_CYCLES whisper cycles
        // (~20k) = ~80k sys cycles + reset; 150k is generous.
        for (i = 0; i < 150000; i = i + 1) begin
            @(posedge clk);
            if (dut.done_flag) i = 150000;
        end

        if (dut.probe_state !== S_PASS) begin
            $display("FAIL probe did not reach S_PASS state=%0d fail_code=%02x",
                     dut.probe_state, dut.fail_code);
            errors = errors + 1;
        end

        if (!dut.pass_flag || dut.fail_code !== 8'h00) begin
            $display("FAIL final status pass_flag=%0d fail_code=%02x",
                     dut.pass_flag, dut.fail_code);
            errors = errors + 1;
        end

        if (dut.rep_worst !== 4'd2 || dut.rep_incoh !== 4'd9) begin
            $display("FAIL telemetry rep_worst=%0d (exp 2) rep_incoh=%0d (exp 9)",
                     dut.rep_worst, dut.rep_incoh);
            errors = errors + 1;
        end

        // led[1] active-low PASS indicator, led[2] active-low FAIL
        if (led[1] !== 1'b0 || led[2] !== 1'b1) begin
            $display("FAIL LED state led=%b", led);
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL errors=%0d", errors);
        $finish;
    end

endmodule
