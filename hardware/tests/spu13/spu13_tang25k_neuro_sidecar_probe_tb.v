`timescale 1ns / 1ps

module spu13_tang25k_neuro_sidecar_probe_tb;
    reg clk = 1'b0;
    wire [2:0] led;
    wire uart_tx;

    integer i;
    integer errors = 0;

    always #5 clk = ~clk;

    spu13_tang25k_neuro_sidecar_probe dut (
        .sys_clk(clk),
        .led(led),
        .uart_tx(uart_tx)
    );

    initial begin
        $display("=== spu13_tang25k_neuro_sidecar_probe_tb ===");

        for (i = 0; i < 1000; i = i + 1) begin
            @(posedge clk);
        end

        if (dut.test_state !== 9'd24) begin
            $display("FAIL probe did not reach S_PASS state=%0d test_id=%0d fail_code=%02x",
                     dut.test_state, dut.test_id, dut.fail_code);
            errors = errors + 1;
        end

        if (!dut.all_pass || dut.test_id !== 4'd3 || dut.fail_code !== 8'h00) begin
            $display("FAIL final status all_pass=%0d test_id=%0d fail_code=%02x",
                     dut.all_pass, dut.test_id, dut.fail_code);
            errors = errors + 1;
        end

        if (!dut.epA_latched_rejected ||
            dut.epA_commit_a !== 10'd7 || dut.epA_commit_b !== 10'd8) begin
            $display("FAIL epoch A reject readback rejected=%0d commit=(%0d,%0d)",
                     dut.epA_latched_rejected, dut.epA_commit_a, dut.epA_commit_b);
            errors = errors + 1;
        end

        if (!dut.epB_latched_rejected || !dut.epB_latched_overflow ||
            dut.epB_commit_a !== 10'd7 || dut.epB_commit_b !== 10'd8) begin
            $display("FAIL epoch B overflow rejected=%0d overflow=%0d commit=(%0d,%0d)",
                     dut.epB_latched_rejected, dut.epB_latched_overflow,
                     dut.epB_commit_a, dut.epB_commit_b);
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
