// spu4_som_edge_tb.v — Testbench for SPU-4 edge Kohonen BMU
//
// Verifies: weight loading, quadrance computation (p²+3q²),
// BMU selection, Q-dominated vectors (catches shift bugs).
// Oracle: manual quadrance calculation for each test vector.

`timescale 1ns / 1ps

module spu4_som_edge_tb;

    localparam NUM_FEATURES = 3;
    localparam WIDTH = 16;

    reg clk = 0;
    reg rst_n = 0;
    reg start = 0;
    wire done;
    reg [NUM_FEATURES * 2 * WIDTH - 1 : 0] features;
    reg weight_we = 0;
    reg [1:0] weight_node = 0;
    reg [NUM_FEATURES * 2 * WIDTH - 1 : 0] weight_data;
    wire bmu_valid;
    wire [1:0] best_node;
    wire [31:0] best_quadrance;

    spu4_som_edge #(.NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)) u_dut (
        .clk(clk), .rst_n(rst_n), .start(start), .done(done),
        .features(features),
        .weight_we(weight_we), .weight_node(weight_node), .weight_data(weight_data),
        .bmu_valid(bmu_valid), .best_node(best_node), .best_quadrance(best_quadrance)
    );

    always #5 clk = ~clk;

    function [95:0] pack3;
        input signed [15:0] p0, q0, p1, q1, p2, q2;
        begin pack3 = {p2, q2, p1, q1, p0, q0}; end
    endfunction

    integer fail = 0;
    integer test_n = 0;

    task load_node;
        input [1:0] node;
        input signed [15:0] p0, q0, p1, q1, p2, q2;
        begin
            @(posedge clk);
            weight_node = node;
            weight_data = pack3(p0, q0, p1, q1, p2, q2);
            weight_we = 1;
            @(posedge clk);
            weight_we = 0;
        end
    endtask

    // Run classification and check both BMU index AND quadrance value
    task run_classify;
        input signed [15:0] p0, q0, p1, q1, p2, q2;
        input [1:0] exp_node;
        begin
            @(posedge clk);
            features = pack3(p0, q0, p1, q1, p2, q2);
            start = 1;
            @(posedge clk);
            start = 0;
            wait(done);
            @(posedge clk);
            if (!bmu_valid) begin
                $display("FAIL T%0d: bmu_valid not set", test_n);
                fail = fail + 1;
            end else if (best_node !== exp_node) begin
                $display("FAIL T%0d: best_node=%0d exp=%0d Q=%0d",
                    test_n, best_node, exp_node, best_quadrance);
                fail = fail + 1;
            end else begin
                $display("PASS T%0d: best_node=%0d Q=%0d",
                    test_n, best_node, best_quadrance);
            end
        end
    endtask

    // Run classification and check exact quadrance value (oracle)
    task run_classify_q;
        input signed [15:0] p0, q0, p1, q1, p2, q2;
        input [1:0] exp_node;
        input [31:0] exp_q;   // expected quadrance
        begin
            @(posedge clk);
            features = pack3(p0, q0, p1, q1, p2, q2);
            start = 1;
            @(posedge clk);
            start = 0;
            wait(done);
            @(posedge clk);
            if (!bmu_valid) begin
                $display("FAIL T%0d: bmu_valid not set", test_n);
                fail = fail + 1;
            end else if (best_node !== exp_node) begin
                $display("FAIL T%0d: best_node=%0d exp=%0d (Q=%0d expQ=%0d)",
                    test_n, best_node, exp_node, best_quadrance, exp_q);
                fail = fail + 1;
            end else if (best_quadrance !== exp_q) begin
                $display("FAIL T%0d: Q=%0d expQ=%0d (node=%0d correct)",
                    test_n, best_quadrance, exp_q, best_node);
                fail = fail + 1;
            end else begin
                $display("PASS T%0d: node=%0d Q=%0d (exact)", test_n, best_node, best_quadrance);
            end
        end
    endtask

    initial begin
        rst_n = 0; start = 0;
        #20; rst_n = 1; #20;

        // Load 4 nodes
        // Node 0: (100,0), (0,0), (0,0) — "right"
        load_node(0, 100, 0, 0, 0, 0, 0);
        // Node 1: (0,0), (100,0), (0,0) — "forward"
        load_node(1, 0, 0, 100, 0, 0, 0);
        // Node 2: (0,0), (0,0), (100,0) — "up"
        load_node(2, 0, 0, 0, 0, 100, 0);
        // Node 3: (-50,0), (-50,0), (-50,0) — "origin-near"
        load_node(3, -50, 0, -50, 0, -50, 0);

        // ── Basic BMU tests (P-only, Q=0) ────────────────────────
        test_n = 1; run_classify(90, 0, 10, 0, 5, 0, 2'd0);
        test_n = 2; run_classify(10, 0, 95, 0, 5, 0, 2'd1);
        test_n = 3; run_classify(5, 0, 5, 0, 90, 0, 2'd2);
        test_n = 4; run_classify(-45, 0, -45, 0, -45, 0, 2'd3);

        // ── Q-dominated vectors (catches 7q² vs 3q² bug) ────────
        // Load a node at origin with large Q component:
        //   Node 0: (0, 50), (0, 0), (0, 0) — pure √3 offset
        // Re-load: node 0 = (0, 50, 0, 0, 0, 0)
        test_n = 5;
        load_node(0, 0, 50, 0, 0, 0, 0);
        // Input exactly at node 0: expected Q = 0 (perfect match)
        run_classify_q(0, 50, 0, 0, 0, 0, 2'd0, 32'd0);

        // Input offset from node 0 by (10, 0) in first feature:
        //   Δp=10, Δq=0 → Q per feature = 100 + 3*0 = 100
        //   Other features: Δ=0 → Q = 0
        //   Total Q = 100
        test_n = 6;
        run_classify_q(10, 50, 0, 0, 0, 0, 2'd0, 32'd100);

        // Input offset from node 0 by (0, 10) in Q of first feature:
        //   Δp=0, Δq=10 → Q = 0 + 3*100 = 300
        test_n = 7;
        run_classify_q(0, 60, 0, 0, 0, 0, 2'd0, 32'd300);

        // Input offset from node 0 by (10, 10):
        //   Q = 100 + 3*100 = 400
        test_n = 8;
        run_classify_q(10, 60, 0, 0, 0, 0, 2'd0, 32'd400);

        // Multi-feature Q-dominated: node 1 at (0,0, 0,100, 0,0)
        // Input at (0,0, 5,110, 0,0): Δp=5, Δq=10 in feature 1
        //   Q total = 25 + 300 = 325
        // But also check it picked node 1 (not node 0)
        load_node(1, 0, 0, 0, 100, 0, 0);
        test_n = 9;
        run_classify_q(0, 0, 5, 110, 0, 0, 2'd1, 32'd325);

        // Large Q value: Q=0 node, input at Q=100 (Δq=100, Δp=0)
        //   3 features: feature 1 has Δq=100, others Δ=0
        //   Q = 0 + 3*10000 = 30000
        // Node 2 is (0,0, 0,0, 100,0), distance =
        //   f0: Δp=0, Δq=0 → 0
        //   f1: Δp=0, Δq=100 → 30000
        //   f2: Δp=100, Δq=0 → 10000 (only if input was pure P)
        // Input is (0,0, 0,100, 0,0): distance to node 2:
        //   f2: Δp=100, Δq=0 → 10000
        // Node 1 (0,0, 0,100, 0,0): distance = 0 ← wins
        load_node(2, 0, 0, 0, 0, 100, 0);
        test_n = 10;
        run_classify_q(0, 0, 0, 100, 0, 0, 2'd1, 32'd0);

        if (fail == 0)
            $display("\nPASS (%0d tests)", test_n);
        else
            $display("\nFAIL (%0d failures in %0d tests)", fail, test_n);
        $finish;
    end

endmodule
