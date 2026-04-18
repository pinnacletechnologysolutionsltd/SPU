`timescale 1ns/1ps
module laminar_detector_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;

    initial begin
        #20; rst_n = 1;
    end

    // DUT signals
    reg [9:0] addr_in;
    reg signed [31:0] r_q16;
    reg signed [31:0] re_q16;
    reg wake;
    reg [9:0] wake_addr;
    wire irq_out;
    wire latched_out;
    wire cleared_out;

    // declare test-scope integers
    integer waitc;

    // instantiate DUT with fast settling for test
    laminar_detector #(.EPSILON_Q16(16'h0010), .SETTLING_TIME(8)) dut (
        .clk(clk), .rst_n(rst_n), .addr_in(addr_in), .r_q16(r_q16), .re_q16(re_q16), .wake(wake), .wake_addr(wake_addr), .irq_out(irq_out), .latched_out(latched_out), .cleared_out(cleared_out)
    );

    initial begin
        // Initialize
        addr_in = 10'd0; r_q16 = 32'sd0; re_q16 = 32'sd0; wake = 1'b0; wake_addr = 10'd0;
        #10;

        // Test 1: ensure latch engages when below epsilon for SETTLING_TIME cycles
        addr_in = 10'd5; r_q16 = 32'sd1000; re_q16 = 32'sd1000; // equal -> below_eps
        $display("TB: Starting settle test at addr=%0d", addr_in);
        // wait until latched_out asserted (should be after <= SETTLING_TIME cycles)
        wait (latched_out == 1'b1);
        #1;
        if (irq_out !== 1'b1) begin
            $display("TB_FAIL: irq not asserted when latched at addr=%0d", addr_in);
            $finish;
        end
        $display("TB_PASS: latched asserted for addr=%0d", addr_in);

        // Test 2: wake clears latch
        wake_addr = addr_in; wake = 1'b1; $display("TB_DBG: asserted wake=1 wake_addr=%0d at time=%0t", wake_addr, $time);
        @(posedge clk);
        $display("TB_DBG: after posedge wake=%b wake_addr=%0d time=%0t", wake, wake_addr, $time);
        wake = 1'b0; $display("TB_DBG: cleared wake at time=%0t", $time);
        // wait up to 16 clocks for the module to assert cleared_out
        waitc = 0;
        while ((cleared_out != 1'b1) && (waitc < 16)) begin
            @(posedge clk); waitc = waitc + 1;
        end
        if (cleared_out != 1'b1) begin
            $display("TB_FAIL: cleared_out not asserted for addr=%0d after %0d cycles", addr_in, waitc);
            $finish;
        end
        // allow outputs to settle
        @(posedge clk);
        if (latched_out != 1'b0) begin
            $display("TB_FAIL: latched not cleared after cleared_out for addr=%0d", addr_in);
            $finish;
        end
        $display("TB_PASS: wake cleared latch for addr=%0d after %0d cycles", addr_in, waitc);

        // Test 3: activity resets counter (should not latch)
        addr_in = 10'd6; r_q16 = 32'sd1000; re_q16 = 32'sd1100; // above eps
        $display("TB: Starting activity reset test at addr=%0d", addr_in);
        // hold for more than SETTLING_TIME cycles and ensure not latched
        repeat (20) @(posedge clk);
        if (latched_out === 1'b1) begin
            $display("TB_FAIL: latched unexpectedly when activity present at addr=%0d", addr_in);
            $finish;
        end
        $display("TB_PASS: activity prevented latch for addr=%0d", addr_in);

        // Test 4: after activity goes quiet, latch again
        re_q16 = r_q16;
        $display("TB: Now quieting addr=%0d to allow latch", addr_in);
        wait (latched_out == 1'b1);
        $display("TB_PASS: latch re-engaged after quiet for addr=%0d", addr_in);

        $display("ALL_PASS");
        $finish;
    end
endmodule
