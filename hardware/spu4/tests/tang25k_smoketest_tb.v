`timescale 1ns/1ps

module tang25k_smoketest_tb();
    reg clk = 0;
    reg rst_n = 0;
    wire led;
    wire uart_tx;
    wire smoke_ok;

    // Instantiate the board top
    spu_tang25k_top uut (
        .clk_in(clk),
        .rst_n(rst_n),
        .led_out(led),
        .uart_tx(uart_tx),
        .smoke_ok(smoke_ok)
    );

    initial begin
        $dumpfile("tang25k_smoke.vcd");
        $dumpvars(0, tang25k_smoketest_tb);

        // Assert reset for a short time then release
        rst_n = 1'b0;
        #100;
        rst_n = 1'b1;

        // Run for a short interval sufficient for smoke to assert
        #200000; // 200us at 100MHz clock

        if (smoke_ok) begin
            $display("TEST RESULT: PASS");
        end else begin
            $display("TEST RESULT: FAIL");
        end

        $finish;
    end

    // 100 MHz clock
    always #5 clk = ~clk;

endmodule
