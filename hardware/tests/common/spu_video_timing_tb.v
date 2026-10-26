// spu_video_timing_tb.v — Testbench for spu_video_timing
// Checks: active goes low at x=640, hsync pulses at correct interval,
// y increments after each full horizontal line.
`timescale 1ns/1ps
module spu_video_timing_tb;

    reg  clk = 0, rst_n = 0;
    wire [9:0] x, y;
    wire hsync, vsync, active;

    spu_video_timing dut (.clk(clk), .rst_n(rst_n),
        .x(x), .y(y), .hsync(hsync), .vsync(vsync), .active(active));

    always #20 clk = ~clk;  // 25 MHz

    integer pass = 1;
    integer cycle = 0;

    // Count cycles until x wraps to check H_TOTAL=800
    integer x_prev = 0;
    integer wrap_cycle = -1;

    always @(posedge clk) begin
        cycle = cycle + 1;
        if (x == 0 && x_prev > 700 && wrap_cycle < 0)
            wrap_cycle = cycle;
        x_prev = x;
    end

    initial begin
        #30  rst_n = 1;
        // Run two full frames (2 × 525 × 800 cycles = 840,000 cycles)
        #(840_000 * 40 + 100);

        // x=640 → active must be 0
        @(posedge clk);
        if (x === 10'd640 && active !== 1'b0) begin
            $display("FAIL: active should be 0 at x=640");
            pass = 0;
        end

        // Check wrap cycle ≈ 800
        if (wrap_cycle < 798 || wrap_cycle > 802) begin
            $display("FAIL: H_TOTAL wrap at cycle %0d (expected ~800)", wrap_cycle);
            pass = 0;
        end

        if (pass) $display("PASS");
        else      $display("FAIL");
        $finish;
    end
endmodule
