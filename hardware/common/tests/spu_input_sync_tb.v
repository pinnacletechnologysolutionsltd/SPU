// spu_input_sync_tb.v — Testbench for spu_input_sync
`timescale 1ns/1ps

module spu_input_sync_tb;
    reg  clk, reset, async_in;
    wire sync_out;

    spu_input_sync dut (
        .clk(clk), .reset(reset),
        .async_in(async_in), .sync_out(sync_out)
    );

    initial clk = 0;
    always #5 clk = ~clk;  // 100 MHz

    integer fail = 0;

    task check;
        input expected;
        input [63:0] tick;
        begin
            if (sync_out !== expected) begin
                $display("FAIL tick=%0d: sync_out=%b expected=%b", tick, sync_out, expected);
                fail = fail + 1;
            end
        end
    endtask

    integer i;
    initial begin
        reset = 1; async_in = 0;
        @(posedge clk); @(posedge clk);
        reset = 0;

        // After reset both stages should be 0
        @(posedge clk); #1;
        check(0, 0);

        // Assert async_in — should appear at sync_out after 2 rising edges
        async_in = 1;
        @(posedge clk); #1; check(0, 1);  // stage1 just captured 1
        @(posedge clk); #1; check(1, 2);  // sync_out now 1

        // De-assert
        async_in = 0;
        @(posedge clk); #1; check(1, 3);  // still 1 (stage1 just got 0)
        @(posedge clk); #1; check(0, 4);  // now 0

        // Glitch test: pulse async_in for < 1 clock — must NOT propagate
        @(negedge clk);
        async_in = 1; #2; async_in = 0;   // 2 ns glitch
        @(posedge clk); #1; check(0, 5);
        @(posedge clk); #1; check(0, 6);

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d errors)", fail);
        $finish;
    end
endmodule
