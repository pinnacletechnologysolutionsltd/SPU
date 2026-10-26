`timescale 1ns / 1ps

module spu13_lucas_sidecar_tb;
    parameter TEST_MAC_CE_DIV = 1;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg inst_valid = 1'b0;
    reg [63:0] inst_word = 64'd0;

    wire inst_claimed;
    wire busy;
    wire error;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A;
    wire [63:0] qr_commit_B;
    wire [63:0] qr_commit_C;
    wire [63:0] qr_commit_D;
    wire norm_violation;

    integer errors = 0;
    localparam integer GUARD_CYCLES =
        (TEST_MAC_CE_DIV <= 1) ? 8192 : (TEST_MAC_CE_DIV * 2048);

    always #5 clk = ~clk;

    spu13_lucas_sidecar #(
        .MAC_CE_DIV(TEST_MAC_CE_DIV)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .inst_claimed(inst_claimed),
        .busy(busy),
        .error(error),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .norm_violation(norm_violation)
    );

    initial begin
        $display("=== spu13_lucas_sidecar_tb ===");
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        run_lucas(8'hD0, 4'd2, 10'd3, 10'd5, 10'd0, 10'd0,
                  10'd5, 10'd8, "PSCALE");
        run_lucas(8'hD1, 4'd12, 10'd3, 10'd5, 10'd0, 10'd0,
                  10'd8, 10'd516, "PCHIRAL");
        run_lucas(8'hD2, 4'd3, 10'd3, 10'd5, 10'd2, 10'd7,
                  10'd41, 10'd66, "PMUL");
        run_lucas(8'hD3, 4'd4, 10'd3, 10'd5, 10'd0, 10'd0,
                  10'd513, 10'd5, "PINV");
        run_lucas_error(8'hD3, 4'd5, 10'd0, 10'd0, 10'd0, 10'd0,
                        "PINV zero");
        run_phslk_without_load();
        run_phslk(4'd6,
                  10'd3, 10'd5, 10'd2, 10'd7,
                  10'd6, 10'd10, 10'd4, 10'd14,
                  1'b1, 1'b0, "PHSLK coherent");
        run_phslk(4'd7,
                  10'd3, 10'd5, 10'd2, 10'd7,
                  10'd6, 10'd11, 10'd4, 10'd14,
                  1'b0, 1'b0, "PHSLK mismatch");
        run_phslk(4'd8,
                  10'd3, 10'd5, 10'd1, 10'd100,
                  10'd6, 10'd10, 10'd4, 10'd14,
                  1'b0, 1'b1, "PHSLK zero-divisor denominator");
        run_lucas(8'hD0, 4'd15, 10'd522, 10'd523, 10'd0, 10'd0,
                  10'd2, 10'd3, "PSCALE reduced inputs");
        run_unknown();

        // ── Norm invariant tests ─────────────────────────────────
        run_norm_violation(8'hD0, "PSCALE norm check");
        run_norm_violation(8'hD1, "PCHIRAL norm check");

        if (errors == 0) begin
            $display("PASS");
        end else begin
            $display("FAIL errors=%0d", errors);
        end
        $finish;
    end

    task run_lucas;
        input [7:0] opcode;
        input [3:0] lane;
        input [9:0] a_in;
        input [9:0] b_in;
        input [9:0] c_in;
        input [9:0] d_in;
        input [9:0] exp_a;
        input [9:0] exp_b;
        input [8*32:0] label;
        reg [63:0] exp_pack;
        integer guard;
        begin
            exp_pack = {22'd0, exp_b, 22'd0, exp_a};
            @(negedge clk);
            inst_word = {opcode, lane, a_in, b_in, c_in, d_in, 12'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            if (!inst_claimed) begin
                $display("FAIL %0s was not claimed", label);
                errors = errors + 1;
            end
            inst_valid = 1'b0;

            guard = 0;
            while (!qr_commit_valid && guard < GUARD_CYCLES) begin
                @(negedge clk);
                guard = guard + 1;
            end

            if (!qr_commit_valid) begin
                $display("FAIL %0s timed out", label);
                errors = errors + 1;
            end else if (error || qr_commit_A !== exp_pack ||
                         qr_commit_B !== 64'd0 || qr_commit_C !== 64'd0 ||
                         qr_commit_D !== 64'd0 ||
                         qr_commit_lane !== ((lane > 4'd12) ? 4'd0 : lane)) begin
                $display("FAIL %0s lane=%0d A=%016x error=%0d",
                         label, qr_commit_lane, qr_commit_A, error);
                errors = errors + 1;
            end else begin
                $display("PASS %0s lane=%0d A=%016x", label, qr_commit_lane, qr_commit_A);
            end

            @(negedge clk);
        end
    endtask

    task run_lucas_error;
        input [7:0] opcode;
        input [3:0] lane;
        input [9:0] a_in;
        input [9:0] b_in;
        input [9:0] c_in;
        input [9:0] d_in;
        input [8*32:0] label;
        integer guard;
        begin
            @(negedge clk);
            inst_word = {opcode, lane, a_in, b_in, c_in, d_in, 12'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            if (!inst_claimed) begin
                $display("FAIL %0s was not claimed", label);
                errors = errors + 1;
            end
            inst_valid = 1'b0;

            guard = 0;
            while (!error && !qr_commit_valid && guard < GUARD_CYCLES) begin
                @(negedge clk);
                guard = guard + 1;
            end

            if (!error) begin
                $display("FAIL %0s did not report error", label);
                errors = errors + 1;
            end else if (qr_commit_valid) begin
                $display("FAIL %0s committed despite error", label);
                errors = errors + 1;
            end else begin
                $display("PASS %0s error reported", label);
            end

            @(negedge clk);
        end
    endtask

    task run_unknown;
        begin
            @(negedge clk);
            inst_word = {8'h1A, 56'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            if (inst_claimed) begin
                $display("FAIL unknown opcode claimed");
                errors = errors + 1;
            end else begin
                $display("PASS unknown opcode ignored");
            end
            inst_valid = 1'b0;
            repeat (4) @(negedge clk);
        end
    endtask

    task run_phslk_without_load;
        begin
            @(negedge clk);
            inst_word = {8'hD5, 4'd1, 10'd6, 10'd10, 10'd4, 10'd14, 12'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            if (!inst_claimed) begin
                $display("FAIL PHSLK exec without load was not claimed");
                errors = errors + 1;
            end else if (!error || qr_commit_valid) begin
                $display("FAIL PHSLK exec without load error=%0d commit=%0d",
                         error, qr_commit_valid);
                errors = errors + 1;
            end else begin
                $display("PASS PHSLK exec without load error reported");
            end
            inst_valid = 1'b0;
            @(negedge clk);
        end
    endtask

    task run_phslk;
        input [3:0] lane;
        input [9:0] n1_a;
        input [9:0] n1_b;
        input [9:0] d1_a;
        input [9:0] d1_b;
        input [9:0] n2_a;
        input [9:0] n2_b;
        input [9:0] d2_a;
        input [9:0] d2_b;
        input exp_coherent;
        input exp_zero_divisor;
        input [8*40:0] label;
        reg [63:0] exp_pack;
        integer guard;
        begin
            exp_pack = {22'd0, {9'd0, exp_zero_divisor}, 22'd0, {9'd0, exp_coherent}};

            @(negedge clk);
            inst_word = {8'hD4, 4'd0, n1_a, n1_b, d1_a, d1_b, 12'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            if (!inst_claimed) begin
                $display("FAIL %0s load was not claimed", label);
                errors = errors + 1;
            end
            inst_valid = 1'b0;
            @(negedge clk);

            inst_word = {8'hD5, lane, n2_a, n2_b, d2_a, d2_b, 12'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            if (!inst_claimed) begin
                $display("FAIL %0s exec was not claimed", label);
                errors = errors + 1;
            end
            inst_valid = 1'b0;

            guard = 0;
            while (!qr_commit_valid && guard < GUARD_CYCLES) begin
                @(negedge clk);
                guard = guard + 1;
            end

            if (!qr_commit_valid) begin
                $display("FAIL %0s timed out", label);
                errors = errors + 1;
            end else if (error || qr_commit_A !== exp_pack ||
                         qr_commit_B !== 64'd0 || qr_commit_C !== 64'd0 ||
                         qr_commit_D !== 64'd0 || qr_commit_lane !== lane) begin
                $display("FAIL %0s lane=%0d A=%016x exp=%016x error=%0d",
                         label, qr_commit_lane, qr_commit_A, exp_pack, error);
                errors = errors + 1;
            end else begin
                $display("PASS %0s lane=%0d coherent=%0d zero_divisor=%0d",
                         label, qr_commit_lane, exp_coherent, exp_zero_divisor);
            end

            @(negedge clk);
        end
    endtask

    task run_norm_violation;
        input [7:0] opcode;
        input [8*32:0] label;
        integer guard;
        reg [9:0] a_in, b_in, exp_a, exp_b;
        begin
            // Use intentionally wrong expected result to ensure norm_violation
            // fires.  PSCALE: φ·(1+0φ) should be (0+1φ).  If we corrupt the
            // result check with a deliberate fabrication, norm_violation must
            // assert — but the MAC itself is correct, so we verify that
            // norm_violation stays deasserted for valid results.
            @(negedge clk);
            inst_word = {opcode, 4'd0, 10'd1, 10'd2, 10'd0, 10'd0, 12'd0};
            inst_valid = 1'b1;
            @(negedge clk);
            inst_valid = 1'b0;
            guard = 0;
            while (!qr_commit_valid && guard < GUARD_CYCLES) begin
                @(negedge clk);
                guard = guard + 1;
            end
            if (norm_violation) begin
                $display("FAIL %0s norm violation asserted on valid op", label);
                errors = errors + 1;
            end else if (!qr_commit_valid) begin
                $display("FAIL %0s timed out", label);
                errors = errors + 1;
            end else begin
                $display("PASS %0s norm_violation=%0d", label, norm_violation);
            end
        end
    endtask
endmodule
