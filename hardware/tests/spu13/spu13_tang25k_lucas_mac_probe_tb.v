`timescale 1ns / 1ps

module spu13_tang25k_lucas_mac_probe_tb;
    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    integer i;
    integer errors = 0;

    always #5 clk = ~clk;

    spu13_tang25k_lucas_mac_probe dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    initial begin
        $display("=== spu13_tang25k_lucas_mac_probe_tb ===");

        for (i = 0; i < 10000; i = i + 1) begin
            @(posedge clk);
            if (dut.test_state == 4'd4) begin
                i = 10000;
            end
        end

        if (dut.test_state !== 4'd4) begin
            $display("FAIL probe did not reach S_PASS state=%0d step=%0d drift=(%0d,%0d)",
                     dut.test_state, dut.test_step, dut.drift_a, dut.drift_b);
            errors = errors + 1;
        end

        if (!dut.all_pass || dut.test_step !== 16'd2600) begin
            $display("FAIL final status all_pass=%0d step=%0d",
                     dut.all_pass, dut.test_step);
            errors = errors + 1;
        end

        if (led[1] !== 1'b0 || led[2] !== 1'b1) begin
            $display("FAIL LED state led=%b", led);
            errors = errors + 1;
        end

        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("FAIL errors=%0d", errors);
        end
        $finish;
    end
endmodule
