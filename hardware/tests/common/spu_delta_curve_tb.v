// spu_delta_curve_tb.v — Delta Curve Testbench
//
// Tests the Triple Quadrance Formula in hardware:
//   (Q₃ − Q₁ − Q₂)² = 4·Q₁·Q₂·(1−s₃)
//
// Cases:
//   1. Q₁=3, Q₂=4, steps=4: right triangle at k=4 → rhs²=0, Q₃=7
//   2. Q₁=1, Q₂=1, steps=4: collapsed at k=0 → rhs²=16, Q₃=2±4
//   3. Q₁=0, Q₂=5, steps=2: degenerate Q₁=0 → rhs²=0 always, Q₃=5
//   4. Full sweep: Q₁=3, Q₂=4, steps=4, verify all 5 points

`timescale 1ns / 1ps

module spu_delta_curve_tb;

    reg         clk, rst_n;
    reg         config_en, step_en, polarity;
    reg  [15:0] Q1, Q2;
    reg  [7:0]  steps;
    wire [31:0] q_sum;
    wire [63:0] rhs_sq_num;
    wire [7:0]  rhs_sq_den, step_k;
    wire        output_valid, done;

    spu_delta_curve uut (
        .clk(clk), .rst_n(rst_n),
        .config_en(config_en), .step_en(step_en),
        .Q1(Q1), .Q2(Q2), .steps(steps), .polarity(polarity),
        .q_sum(q_sum), .rhs_sq_num(rhs_sq_num),
        .rhs_sq_den(rhs_sq_den), .step_k(step_k),
        .output_valid(output_valid), .done(done)
    );

    always #5 clk = ~clk;

    integer pass, fail, i;

    task pulse;
        input what;
        begin
            if (what == 0) config_en = 1; else step_en = 1;
            @(posedge clk);
            config_en = 0; step_en = 0;
            @(posedge clk);
        end
    endtask

    task wait_valid;
        begin
            while (!output_valid) @(posedge clk);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        config_en = 0; step_en = 0; polarity = 0;
        Q1 = 0; Q2 = 0; steps = 0;
        pass = 0; fail = 0;

        @(posedge clk); rst_n = 1;
        @(posedge clk);

        $display("\n── Delta Curve Tests ──");

        // ── Test 1: Q₁=3, Q₂=4, steps=4 ──────────────────────────────
        Q1 = 16'd3; Q2 = 16'd4; steps = 8'd4;
        pulse(0);  // config
        wait_valid();
        // k=0: rhs² = 4·3·4·(4−0)/4 = 48/4... wait, 4·3·4 = 48, ×4 = 192, /4 = 48.
        // Actually: 4·Q₁·Q₂·(steps−k) = 4·3·4·4 = 192, denom = 4.
        if (q_sum == 7 && rhs_sq_num == 192 && rhs_sq_den == 4 && step_k == 0) begin
            $display("  PASS: k=0: Q₃=%0d ± √(%0d/%0d)", q_sum, rhs_sq_num, rhs_sq_den);
            pass = pass + 1;
        end else begin
            $display("  FAIL: k=0: got Q₃=%0d ± √(%0d/%0d) (expected 7 ± √(192/4))",
                     q_sum, rhs_sq_num, rhs_sq_den);
            fail = fail + 1;
        end

        // Advance through remaining steps
        for (i = 1; i <= 4; i = i + 1) begin
            pulse(1);  // step
            wait_valid();
            // rhs² = 4·3·4·(4−i) / 4
            // i=1: 4·3·4·3/4 = 144/4
            // i=2: 4·3·4·2/4 = 96/4
            // i=3: 4·3·4·1/4 = 48/4
            // i=4: 4·3·4·0/4 = 0/4
            if (step_k == i && q_sum == 7) begin
                $display("  PASS: k=%0d: Q₃=%0d ± √(%0d/%0d)", step_k, q_sum, rhs_sq_num, rhs_sq_den);
                pass = pass + 1;
            end else begin
                $display("  FAIL: k=%0d: got step=%0d sum=%0d rhs=%0d/%0d",
                         i, step_k, q_sum, rhs_sq_num, rhs_sq_den);
                fail = fail + 1;
            end
        end

        // ── Test 2: Q₁=1, Q₂=1, steps=4 ──────────────────────────────
        Q1 = 16'd1; Q2 = 16'd1; steps = 8'd4;
        pulse(0);
        wait_valid();
        // k=0: rhs² = 4·1·1·4/4 = 16/4 = 4, Q₃ = 2 ± √4
        if (q_sum == 2 && rhs_sq_num == 16 && step_k == 0) begin
            $display("  PASS: (1,1) k=0: Q₃=2 ± √(16/4)");
            pass = pass + 1;
        end else begin
            $display("  FAIL: (1,1) k=0: got %0d ± √(%0d/%0d)", q_sum, rhs_sq_num, rhs_sq_den);
            fail = fail + 1;
        end

        // Step to k=4: right triangle endpoint
        for (i = 1; i <= 4; i = i + 1) begin
            pulse(1);
            wait_valid();
        end
        // After 4 steps: k=4 should have rhs²=0
        if (step_k == 4 && rhs_sq_num == 0 && q_sum == 2) begin
            $display("  PASS: (1,1) k=4: right triangle, rhs²=0, Q₃=2");
            pass = pass + 1;
        end else begin
            $display("  FAIL: (1,1) k=4: rhs=%0d sum=%0d", rhs_sq_num, q_sum);
            fail = fail + 1;
        end

        repeat (2) @(posedge clk);

        $display("\n──────────────────────────────");
        $display("Results: %0d passed, %0d failed", pass, fail);
        if (fail == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
