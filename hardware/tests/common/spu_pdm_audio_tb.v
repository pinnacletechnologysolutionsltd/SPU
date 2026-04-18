// spu_pdm_audio_tb.v — Testbench for spu_pdm_audio
// Verifies sigma-delta behaviour:
//   - Silence (sample=0) → pdm_out toggles ~50% duty cycle
//   - Full-scale positive → pdm_out majority 1
//   - Full-scale negative → pdm_out majority 0
`timescale 1ns/1ps

module spu_pdm_audio_tb;
    parameter CLK_PERIOD = 37;  // ~27 MHz

    reg        clk, reset;
    reg [31:0] sample_in;
    reg        piranha_en;
    wire       pdm_out;

    // Small SAMPLE_PERIOD for fast simulation
    spu_pdm_audio #(
        .CLK_FREQ(27_000_000),
        .SAMPLE_RATE(44_100),
        .SAMPLE_PERIOD(612)
    ) dut (
        .clk(clk), .reset(reset),
        .sample_in(sample_in),
        .piranha_en(piranha_en),
        .pdm_out(pdm_out)
    );

    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    integer fail = 0;

    // Count pdm_out=1 pulses over N clocks
    task count_ones;
        input integer N;
        output integer cnt;
        integer k;
        begin
            cnt = 0;
            for (k = 0; k < N; k = k + 1) begin
                @(posedge clk); #1;
                if (pdm_out) cnt = cnt + 1;
            end
        end
    endtask

    integer ones;

    initial begin
        reset = 1; sample_in = 32'h0; piranha_en = 0;
        @(posedge clk); @(posedge clk);
        reset = 0;

        // --- Test 1: Silence (P=0, Q=0) → duty ~50% ---
        // After settling, count over 1000 cycles
        sample_in = 32'h0000_0000;
        piranha_en = 1; @(posedge clk); piranha_en = 0;
        @(posedge clk); repeat(100) @(posedge clk);  // settle
        count_ones(2000, ones);
        // Expect roughly 50% ±20%
        if (ones < 800 || ones > 1200) begin
            $display("FAIL silence: ones=%0d/2000 expected ~1000", ones);
            fail = fail + 1;
        end

        // --- Test 2: Full-scale positive (P=0x7FFF, Q=0) → duty > 70% ---
        sample_in = 32'h7FFF_0000;
        piranha_en = 1; @(posedge clk); piranha_en = 0;
        repeat(200) @(posedge clk);
        count_ones(2000, ones);
        if (ones < 1400) begin
            $display("FAIL pos full-scale: ones=%0d/2000 expected >1400", ones);
            fail = fail + 1;
        end

        // --- Test 3: Full-scale negative (P=0x8000, Q=0) → duty < 30% ---
        sample_in = 32'h8000_0000;
        piranha_en = 1; @(posedge clk); piranha_en = 0;
        repeat(200) @(posedge clk);
        count_ones(2000, ones);
        if (ones > 600) begin
            $display("FAIL neg full-scale: ones=%0d/2000 expected <600", ones);
            fail = fail + 1;
        end

        // --- Test 4: Piranha Pulse refreshes sample latch ---
        sample_in = 32'h7FFF_0000;  // positive
        piranha_en = 1; @(posedge clk); piranha_en = 0;
        repeat(100) @(posedge clk);
        count_ones(500, ones);
        if (ones < 350) begin
            $display("FAIL piranha refresh: ones=%0d/500 expected >350", ones);
            fail = fail + 1;
        end

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d errors)", fail);
        $finish;
    end
endmodule
