`timescale 1ns / 1ps

module spu13_tang25k_rotc_probe_tb;
    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    integer i;
    integer errors = 0;

    always #5 clk = ~clk;

    spu13_tang25k_rotc_probe dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    initial begin
        $display("=== spu13_tang25k_rotc_probe_tb ===");

        for (i = 0; i < 20000; i = i + 1) begin
            @(posedge clk);
            if (dut.test_state == 5'd7) begin
                i = 20000;
            end
        end

        if (dut.test_state !== 5'd7) begin
            $display("FAIL probe did not reach S_PASS state=%0d active_angle=%0d fail_code=%02x",
                     dut.test_state, dut.active_angle, dut.fail_code);
            errors = errors + 1;
        end

        if (!dut.all_pass || !dut.trace_done || !dut.closure_done ||
            dut.active_angle !== 3'd5 || dut.fail_code !== 8'h00) begin
            $display("FAIL final status all_pass=%0d trace_done=%0d closure_done=%0d angle=%0d fail_code=%02x",
                     dut.all_pass, dut.trace_done, dut.closure_done,
                     dut.active_angle, dut.fail_code);
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
