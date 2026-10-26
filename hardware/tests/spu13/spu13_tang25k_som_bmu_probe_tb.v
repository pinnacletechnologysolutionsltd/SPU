`timescale 1ns / 1ps

module spu13_tang25k_som_bmu_probe_tb;
    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    integer i;
    integer errors = 0;

    always #5 clk = ~clk;

    spu13_tang25k_som_bmu_probe dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    initial begin
        $display("=== spu13_tang25k_som_bmu_probe_tb ===");

        for (i = 0; i < 2000; i = i + 1) begin
            @(posedge clk);
            if (dut.test_state == 4'd6) begin
                i = 2000;
            end
        end

        if (dut.test_state !== 4'd6) begin
            $display("FAIL probe did not reach S_PASS state=%0d idx=%0d fail_code=%02x",
                     dut.test_state, dut.test_idx, dut.fail_code);
            errors = errors + 1;
        end

        if (!dut.all_pass || dut.tests_done !== 2'd2 ||
            dut.best_digit !== 4'd6 || dut.fail_code !== 8'h00) begin
            $display("FAIL final status all_pass=%0d tests_done=%0d best=%0d fail_code=%02x",
                     dut.all_pass, dut.tests_done, dut.best_digit,
                     dut.fail_code);
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
