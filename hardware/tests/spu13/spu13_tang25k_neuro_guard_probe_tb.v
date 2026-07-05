`timescale 1ns / 1ps

module spu13_tang25k_neuro_guard_probe_tb;
    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    integer i;
    integer errors = 0;

    always #5 clk = ~clk;

    spu13_tang25k_neuro_guard_probe dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    initial begin
        $display("=== spu13_tang25k_neuro_guard_probe_tb ===");

        for (i = 0; i < 1000; i = i + 1) begin
            @(posedge clk);
        end

        if (dut.test_state !== 6'd24) begin
            $display("FAIL probe did not reach S_PASS state=%0d fail_code=%02x",
                     dut.test_state, dut.fail_code);
            errors = errors + 1;
        end

        if (dut.fail_code !== 8'h00 ||
            dut.last_proposal_a !== 10'd3 ||
            dut.last_proposal_b !== 10'd3 ||
            dut.last_norm !== 10'd9 ||
            dut.last_commit_a !== 10'd7 ||
            dut.last_commit_b !== 10'd8) begin
            $display("FAIL final telemetry P=%0d/%0d K=%0d C=%0d/%0d E=%02x",
                     dut.last_proposal_a, dut.last_proposal_b,
                     dut.last_norm, dut.last_commit_a,
                     dut.last_commit_b, dut.fail_code);
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
