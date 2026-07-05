`timescale 1ns / 1ps

module spu13_neuro_epoch_sidecar_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start_epoch = 1'b0;
    reg [1:0] spike_in = 2'b00;
    reg [15:0] weights = {8'd5, 8'd3};
    reg [15:0] thresholds = {8'd5, 8'd5};
    reg [9:0] expected_norm = 10'd0;
    reg [9:0] fallback_a = 10'd0;
    reg [9:0] fallback_b = 10'd0;

    wire busy;
    wire done;
    wire accepted;
    wire rejected;
    wire norm_ok;
    wire overflow_fault;
    wire [1:0] token_mask;
    wire [15:0] spike_total;
    wire [9:0] proposal_a;
    wire [9:0] proposal_b;
    wire [9:0] norm_value;
    wire [9:0] commit_a;
    wire [9:0] commit_b;

    reg overflow_start = 1'b0;
    reg overflow_spike = 1'b0;
    wire overflow_busy;
    wire overflow_done;
    wire overflow_accepted;
    wire overflow_rejected;
    wire overflow_norm_ok;
    wire overflow_fault_seen;
    wire [15:0] overflow_total;
    wire [9:0] overflow_norm_value;
    wire [9:0] overflow_commit_a;
    wire [9:0] overflow_commit_b;

    integer errors = 0;

    always #5 clk = ~clk;

    spu13_neuro_epoch_sidecar #(
        .NUM_NEURONS(2),
        .POT_WIDTH(8),
        .COUNT_WIDTH(4),
        .EPOCH_CYCLES(2),
        .EPOCH_COUNT_WIDTH(2),
        .LEAK(1),
        .RESET_VAL(0),
        .L_P(521),
        .L_P_BITS(10)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .clk_en(1'b1),
        .start_epoch(start_epoch),
        .spike_in(spike_in),
        .weights(weights),
        .thresholds(thresholds),
        .expected_norm(expected_norm),
        .fallback_a(fallback_a),
        .fallback_b(fallback_b),
        .busy(busy),
        .done(done),
        .accepted(accepted),
        .rejected(rejected),
        .norm_ok(norm_ok),
        .overflow_fault(overflow_fault),
        .token_mask(token_mask),
        .spike_total(spike_total),
        .proposal_a(proposal_a),
        .proposal_b(proposal_b),
        .norm_value(norm_value),
        .commit_a(commit_a),
        .commit_b(commit_b)
    );

    spu13_neuro_epoch_sidecar #(
        .NUM_NEURONS(1),
        .POT_WIDTH(4),
        .COUNT_WIDTH(2),
        .EPOCH_CYCLES(5),
        .EPOCH_COUNT_WIDTH(3),
        .LEAK(0),
        .RESET_VAL(0),
        .L_P(521),
        .L_P_BITS(10)
    ) overflow_dut (
        .clk(clk),
        .rst_n(rst_n),
        .clk_en(1'b1),
        .start_epoch(overflow_start),
        .spike_in(overflow_spike),
        .weights(4'd1),
        .thresholds(4'd1),
        .expected_norm(10'd9),
        .fallback_a(10'd7),
        .fallback_b(10'd8),
        .busy(overflow_busy),
        .done(overflow_done),
        .accepted(overflow_accepted),
        .rejected(overflow_rejected),
        .norm_ok(overflow_norm_ok),
        .overflow_fault(overflow_fault_seen),
        .token_mask(),
        .spike_total(overflow_total),
        .proposal_a(),
        .proposal_b(),
        .norm_value(overflow_norm_value),
        .commit_a(overflow_commit_a),
        .commit_b(overflow_commit_b)
    );

    initial begin
        $display("=== spu13_neuro_epoch_sidecar_tb ===");
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        run_two_cycle_epoch(10'd11, 10'd7, 10'd8, 1'b1,
                            "accepted Lucas-norm envelope");
        run_two_cycle_epoch(10'd12, 10'd7, 10'd8, 1'b0,
                            "rejected Lucas-norm envelope");
        run_quiet_epoch();
        run_carry_threshold_epoch();
        run_overflow_epoch();

        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("FAIL errors=%0d", errors);
        end
        $finish;
    end

    task wait_done;
        input [8*40:0] label;
        integer guard;
        begin
            guard = 0;
            while (!done && guard < 16) begin
                @(negedge clk);
                guard = guard + 1;
            end
            if (!done) begin
                $display("FAIL %0s timed out", label);
                errors = errors + 1;
            end
        end
    endtask

    task pulse_start;
        begin
            @(negedge clk);
            start_epoch = 1'b1;
            spike_in = 2'b00;
            @(negedge clk);
            start_epoch = 1'b0;
        end
    endtask

    task run_two_cycle_epoch;
        input [9:0] exp_norm;
        input [9:0] fb_a;
        input [9:0] fb_b;
        input       should_accept;
        input [8*40:0] label;
        begin
            expected_norm = exp_norm;
            fallback_a = fb_a;
            fallback_b = fb_b;
            pulse_start();

            spike_in = 2'b11;
            @(negedge clk);
            spike_in = 2'b01;
            @(negedge clk);
            spike_in = 2'b00;
            wait_done(label);

            if (proposal_a !== 10'd3 || proposal_b !== 10'd2 ||
                norm_value !== 10'd11 || spike_total !== 16'd2 ||
                token_mask !== 2'b11 || overflow_fault !== 1'b0) begin
                $display("FAIL %0s proposal a=%0d b=%0d norm=%0d total=%0d mask=%b overflow=%0d",
                         label, proposal_a, proposal_b, norm_value,
                         spike_total, token_mask, overflow_fault);
                errors = errors + 1;
            end else if (should_accept &&
                         (!accepted || rejected || !norm_ok ||
                          commit_a !== 10'd3 || commit_b !== 10'd2)) begin
                $display("FAIL %0s expected accept commit=%0d,%0d accepted=%0d rejected=%0d norm_ok=%0d",
                         label, commit_a, commit_b, accepted, rejected, norm_ok);
                errors = errors + 1;
            end else if (!should_accept &&
                         (accepted || !rejected || norm_ok ||
                          commit_a !== fb_a || commit_b !== fb_b)) begin
                $display("FAIL %0s expected fallback commit=%0d,%0d accepted=%0d rejected=%0d norm_ok=%0d",
                         label, commit_a, commit_b, accepted, rejected, norm_ok);
                errors = errors + 1;
            end else begin
                $display("PASS %0s", label);
            end

            repeat (2) @(negedge clk);
        end
    endtask

    task run_quiet_epoch;
        begin
            expected_norm = 10'd0;
            fallback_a = 10'd7;
            fallback_b = 10'd8;
            pulse_start();

            spike_in = 2'b01;
            @(negedge clk);
            spike_in = 2'b00;
            @(negedge clk);
            wait_done("quiet leak epoch");

            if (!accepted || rejected || !norm_ok ||
                proposal_a !== 10'd0 || proposal_b !== 10'd0 ||
                norm_value !== 10'd0 || commit_a !== 10'd0 ||
                commit_b !== 10'd0 || token_mask !== 2'b00) begin
                $display("FAIL quiet leak epoch proposal=%0d,%0d norm=%0d commit=%0d,%0d token_mask=%b accepted=%0d rejected=%0d",
                         proposal_a, proposal_b, norm_value, commit_a,
                         commit_b, token_mask, accepted, rejected);
                errors = errors + 1;
            end else begin
                $display("PASS quiet leak epoch");
            end
            repeat (2) @(negedge clk);
        end
    endtask

    task run_carry_threshold_epoch;
        begin
            weights = {8'd0, 8'd8};
            thresholds = {8'd0, 8'd15};
            expected_norm = 10'd1;
            fallback_a = 10'd7;
            fallback_b = 10'd8;
            pulse_start();

            spike_in = 2'b01;
            @(negedge clk);
            spike_in = 2'b01;
            @(negedge clk);
            spike_in = 2'b00;
            wait_done("carry-bit threshold epoch");

            if (!accepted || rejected || !norm_ok ||
                proposal_a !== 10'd1 || proposal_b !== 10'd1 ||
                norm_value !== 10'd1 || commit_a !== 10'd1 ||
                commit_b !== 10'd1 || token_mask !== 2'b01) begin
                $display("FAIL carry-bit threshold epoch proposal=%0d,%0d norm=%0d commit=%0d,%0d token_mask=%b accepted=%0d rejected=%0d",
                         proposal_a, proposal_b, norm_value, commit_a,
                         commit_b, token_mask, accepted, rejected);
                errors = errors + 1;
            end else begin
                $display("PASS carry-bit threshold epoch");
            end

            weights = {8'd5, 8'd3};
            thresholds = {8'd5, 8'd5};
            repeat (2) @(negedge clk);
        end
    endtask

    task run_overflow_epoch;
        integer guard;
        begin
            @(negedge clk);
            overflow_start = 1'b1;
            overflow_spike = 1'b0;
            @(negedge clk);
            overflow_start = 1'b0;

            repeat (5) begin
                overflow_spike = 1'b1;
                @(negedge clk);
            end
            overflow_spike = 1'b0;

            guard = 0;
            while (!overflow_done && guard < 16) begin
                @(negedge clk);
                guard = guard + 1;
            end

            if (!overflow_done) begin
                $display("FAIL overflow epoch timed out");
                errors = errors + 1;
            end else if (!overflow_fault_seen || overflow_accepted ||
                         !overflow_rejected || overflow_norm_ok ||
                         overflow_total !== 16'd3 ||
                         overflow_norm_value !== 10'd9 ||
                         overflow_commit_a !== 10'd7 ||
                         overflow_commit_b !== 10'd8) begin
                $display("FAIL overflow epoch fault=%0d accepted=%0d rejected=%0d norm_ok=%0d total=%0d norm=%0d commit=%0d,%0d",
                         overflow_fault_seen, overflow_accepted,
                         overflow_rejected, overflow_norm_ok, overflow_total,
                         overflow_norm_value, overflow_commit_a,
                         overflow_commit_b);
                errors = errors + 1;
            end else begin
                $display("PASS overflow epoch rejects saturated token stream");
            end
            repeat (2) @(negedge clk);
        end
    endtask
endmodule
