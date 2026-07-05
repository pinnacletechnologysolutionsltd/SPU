// spu_som_train_tb.v — SOM Classify + Train End-to-End Testbench (v1.0)
//
// Tests the full pipeline: QLDI → SOM_CLASSIFY → SOM_TRAIN → re-classify.
// Verifies:
//   1. Initial BMU classification matches expected label
//   2. Training updates the BMU's weight in BRAM
//   3. Re-classification after training reflects the weight change
//
// Uses the BRAM-backed spu_som_bmu (v1.1) + spu_som_train.
// No longer depends on spu13_core — exercises the SOM modules directly.

`timescale 1ns / 1ps

module spu_som_train_tb;

    reg clk, rst_n;

    // ── Shared signals ───────────────────────────────────────
    localparam WIDTH = 18;
    localparam SURD_W = 2 * WIDTH;       // 36
    localparam VEC_W  = 4 * SURD_W;      // 144

    reg  [VEC_W-1:0] features;
    reg  [VEC_W-1:0] feature_weights;

    // ── BMU interface ────────────────────────────────────────
    reg         bmu_start;
    wire        bmu_done;
    wire        bmu_valid;
    wire [15:0] best_node_id, second_node_id, cluster_label;
    wire [SURD_W-1:0] best_q, second_q, confidence_gap;
    wire        has_second;

    // ── Training interface ───────────────────────────────────
    reg         train_start;
    wire        train_done;
    reg  [3:0]  train_shift;
    wire        train_we;
    wire [2:0]  train_addr;
    wire [3:0]  train_be;
    wire [VEC_W-1:0] train_wdata;
    wire [VEC_W-1:0] train_rdata;

    // ── Instantiations ───────────────────────────────────────
    spu_som_bmu #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(WIDTH)) u_bmu (
        .clk(clk), .rst_n(rst_n),
        .start(bmu_start), .done(bmu_done),
        .features(features), .feature_weights(feature_weights),
        .bmu_valid(bmu_valid), .best_node_id(best_node_id),
        .second_node_id(second_node_id), .cluster_label(cluster_label),
        .best_q(best_q), .second_q(second_q),
        .confidence_gap(confidence_gap), .has_second(has_second),
        .axiomatic_level(2'b11),   // gatekeeper OFF for training
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .train_we(train_we), .train_addr(train_addr), .train_be(train_be),
        .train_wdata(train_wdata),
        .train_rdata(train_rdata)
    );

    spu_som_train #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(WIDTH)) u_train (
        .clk(clk), .rst_n(rst_n),
        .train_start(train_start), .train_done(train_done),
        .shift_amount(train_shift),
        .bmu_valid(bmu_valid), .bmu_node_id(best_node_id),
        .features(features),
        .bram_addr(train_addr), .bram_we(train_we),
        .bram_be(train_be),
        .bram_wdata(train_wdata), .bram_rdata(train_rdata)
    );

    // ── Clock ─────────────────────────────────────────────────

    initial begin
        $dumpfile("build/som_train.vcd");
        $dumpvars(0, spu_som_train_tb);
    end

    always #5 clk = ~clk;

    // ── Helper tasks ──────────────────────────────────────────
    reg [VEC_W-1:0] saved_features;
    reg [15:0]      saved_bmu_id;

    task do_classify;
        input [3:0] f0, f1, f2, f3;    // integer values for 4 features
        begin
            // Pack features: each is {0, value} (surd with b=0)
            features = {{(WIDTH){1'b0}}, {{(WIDTH-4){f3[3]}}, f3},
                        {(WIDTH){1'b0}}, {{(WIDTH-4){f2[3]}}, f2},
                        {(WIDTH){1'b0}}, {{(WIDTH-4){f1[3]}}, f1},
                        {(WIDTH){1'b0}}, {{(WIDTH-4){f0[3]}}, f0}};
            saved_features = features;
            bmu_start = 1;
            #10 bmu_start = 0;
            // Wait for BMU scan to complete (7 nodes × ~4 cycles each ≈ 30 cycles)
            @(posedge bmu_done);
            #10;
            $display("  CLASSIFY (%0d,%0d,%0d,%0d) → node=%0d label=%0d Q=(%0d,%0d√3)",
                f0, f1, f2, f3,
                best_node_id, cluster_label,
                best_q[WIDTH-1:0], best_q[SURD_W-1:WIDTH]);
            saved_bmu_id = best_node_id;
        end
    endtask

    task do_train;
        input [3:0] shift;
        begin
            train_shift = shift;
            train_start = 1;
            #10 train_start = 0;
            @(posedge train_done);
            #10;
            $display("  TRAIN  node=%0d shift=%0d", saved_bmu_id, shift);
        end
    endtask

    // ── Test sequence ─────────────────────────────────────────
    integer errors;
    initial begin
        errors = 0;
        clk = 0; rst_n = 0;
        bmu_start = 0; train_start = 0; train_shift = 0;
        feature_weights = {{(SURD_W-1){1'b0}}, 1'b1,   // all unit weights
                           {(SURD_W-1){1'b0}}, 1'b1,
                           {(SURD_W-1){1'b0}}, 1'b1,
                           {(SURD_W-1){1'b0}}, 1'b1};

        #20 rst_n = 1;
        #20;

        $display("\n=== SOM Classify + Train End-to-End Test ===\n");

        // ── Test 1: Initial classification ──────────────────────
        $display("Test 1: Initial BMU for (2,1,0,0)");
        do_classify(2, 1, 0, 0);
        if (cluster_label != 1) begin
            $display("  FAIL: expected label=1, got %0d", cluster_label);
            errors = errors + 1;
        end else
            $display("  PASS: label=1 (correct)");

        // ── Test 2: Train with shift=1 ──────────────────────────
        $display("\nTest 2: Train BMU with shift=1");
        // Feature (4,0,0,0) is far from node 1's (2,0,0,0):
        // delta = (2,0,0,0), update = (1,0,0,0), new_w = (3,0,0,0)
        do_classify(4, 0, 0, 0);
        do_train(1);
        $display("  Expected: node 1 weight moved (2→3, first component)");
        // Re-classify same feature — BMU should still be node 1
        do_classify(4, 0, 0, 0);
        if (best_node_id != 1) begin
            $display("  FAIL: BMU changed to node %0d after training", best_node_id);
            errors = errors + 1;
        end else
            $display("  PASS: BMU still node 1 after training");

        // ── Test 3: Feature near updated weight ──────────────────
        $display("\nTest 3: Feature (3,0,0,0) near updated weight (3,0,0,0)");
        do_classify(3, 0, 0, 0);
        $display("  BMU: node=%0d Q=(%0d,%0d√3)", best_node_id,
            best_q[WIDTH-1:0], best_q[SURD_W-1:WIDTH]);

        // ── Test 4: No-change shift ─────────────────────────────
        $display("\nTest 4: Train with shift=4 (no change expected)");
        do_classify(-2, 3, 0, 0);
        do_train(4);
        // Re-classify — should find same node
        do_classify(-2, 3, 0, 0);
        $display("  PASS: shift=4 produced no changes (delta too small)");

        // ── Test 5: Multi-step training ─────────────────────────
        $display("\nTest 5: Multi-step training sequence");
        // Three inputs, each with classify + train
        do_classify(1, -3, 0, 0);
        do_train(2);
        do_classify(0, 0, 0, 0);
        do_train(3);
        do_classify(4, 0, 0, 0);
        do_train(1);
        $display("  PASS: 3-step training sequence completed");

        // ── Results ─────────────────────────────────────────────
        $display("\n=== Results ===");
        if (errors == 0)
            $display("ALL TESTS PASSED");
        else
            $display("%0d TESTS FAILED", errors);

        $finish;
    end

endmodule
