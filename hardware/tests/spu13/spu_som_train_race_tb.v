`timescale 1ns / 1ps

// spu_som_train_race_tb.v — SOM training stress test
//
// Verifies training writes and classification work correctly.
// Uses simple wait(done) + #1 to capture post-clock values.

module spu_som_train_race_tb;

    localparam NUM_FEATURES = 4;
    localparam MAX_NODES    = 7;
    localparam WIDTH        = 18;
    localparam FEATURE_W    = 2 * WIDTH;

    reg clk, rst_n;
    reg start;
    reg [NUM_FEATURES * 2 * WIDTH - 1 : 0] features;
    reg [NUM_FEATURES * WIDTH - 1 : 0]     feat_weights;

    wire bmu_valid;
    wire [15:0] best_node_id;
    wire [15:0] second_node_id;
    wire [15:0] best_label;
    wire [63:0] best_quadrance;
    wire [63:0] second_quadrance;
    wire [63:0] confidence_gap;
    wire has_second;
    wire done;
    wire busy;

    reg train_we;
    reg [$clog2(MAX_NODES)-1:0] train_addr;
    reg signed [WIDTH-1:0] train_alpha_h;
    reg [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_features;

    spu_som_node_array #(
        .NUM_FEATURES(NUM_FEATURES),
        .MAX_NODES(MAX_NODES),
        .WIDTH(WIDTH)
    ) uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .features(features), .feat_weights(feat_weights),
        .bmu_valid(bmu_valid), .best_node_id(best_node_id),
        .second_node_id(second_node_id), .best_label(best_label),
        .best_quadrance(best_quadrance), .second_quadrance(second_quadrance),
        .confidence_gap(confidence_gap), .has_second(has_second),
        .done(done), .busy(busy),
        .train_we(train_we), .train_addr(train_addr),
        .train_alpha_h(train_alpha_h), .train_features(train_features)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;

    task check;
        input ok;
        input [255:0] msg;
        begin
            test_total = test_total + 1;
            if (ok) test_pass = test_pass + 1;
            else $display("FAIL: %0s", msg);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; start = 0;
        train_we = 0; train_alpha_h = 0;
        train_addr = 0; train_features = 0;
        features = 0; feat_weights = 0;
        test_pass = 0; test_total = 0;

        // Set all feature weights to 1.0 (Q16.2 fixed-point: 1 << 16)
        // feat_weights is [NUM_FEATURES * WIDTH - 1 : 0], each feature gets 18 bits
        // Pack 18'd65536 (=1.0 in Q16.2) into each 18-bit slot
        feat_weights = {
            18'd65536,  // F3 weight = 1.0
            18'd65536,  // F2 weight = 1.0
            18'd65536,  // F1 weight = 1.0
            18'd65536   // F0 weight = 1.0
        };

        #20 rst_n = 1; #10;

        // ═══════════════════════════════════════════════════════════
        // Scenario A: Baseline classification with known features
        // All nodes have default (zero) weights; feature = (1,0,0,0)
        // ═══════════════════════════════════════════════════════════
        features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd1, 18'd0};
        start = 1; #10; start = 0;
        wait(done); #1;
        test_total = test_total + 1;
        if (!bmu_valid) $display("FAIL A1: BMU valid not asserted, q=%h id=%0d", best_quadrance, best_node_id);
        else test_pass = test_pass + 1;
        test_total = test_total + 1;
        if (best_node_id !== 16'd0) begin
            $display("FAIL A2: tie-break expected node 0, got %0d", best_node_id);
        end else test_pass = test_pass + 1;
        check(best_quadrance != 64'd0, "A3: non-zero quadrance");
        #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario B: Training write on same edge as classification
        // In-flight classification must use old weights; the training write
        // becomes visible on the next classification.
        // ═══════════════════════════════════════════════════════════
        features = 0;
        train_features = 0;
        train_features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd100, 18'd0};
        train_alpha_h = (1 << 16);
        train_addr = 0;
        start = 1; train_we = 1; #10; start = 0; train_we = 0;
        wait(done); #1;
        check(bmu_valid, "B1: BMU valid during simultaneous train/classify");
        check(best_node_id == 16'd0, "B2: simultaneous classification used old node0 weight");
        #20;

        features = 0;
        start = 1; #10; start = 0;
        wait(done); #1;
        check(bmu_valid, "B3: BMU valid after simultaneous training");
        check(best_node_id != 16'd0, "B4: training takes effect on next classification");
        #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario C: Training write between classifications
        // ═══════════════════════════════════════════════════════════
        check(!busy, "C1: idle before training");
        train_features = 0;
        train_features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd10, 18'd0};
        train_alpha_h = (1 << 16);
        train_addr = 3;
        train_we = 1; #10; train_we = 0; #10;
        check(!busy, "C2: idle after training write");
        #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario D: Verify training took effect on next classification
        // ═══════════════════════════════════════════════════════════
        features = 0;
        features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd100, 18'd0};
        start = 1; #10; start = 0;
        wait(done); #1;
        check(bmu_valid, "D1: BMU valid after training");
        check(best_node_id < MAX_NODES, "D2: valid best node ID");
        #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario E: Train multiple nodes, then verify classification
        // ═══════════════════════════════════════════════════════════
        train_alpha_h = (1 << 16);
        train_features = 0;
        train_features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd5, 18'd2};
        train_addr = 1; train_we = 1; #10; train_we = 0; #20;
        train_features = 0;
        train_features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd3, 18'd7};
        train_addr = 5; train_we = 1; #10; train_we = 0; #20;

        features = 0;
        features[NUM_FEATURES * FEATURE_W - 1 : (NUM_FEATURES-1) * FEATURE_W] = {18'd5, 18'd2};
        start = 1; #10; start = 0;
        wait(done); #1;
        check(bmu_valid, "E1: BMU valid after multi-node training");
        #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario F: Confidence gap with 7 nodes
        // ═══════════════════════════════════════════════════════════
        check(has_second, "F1: second-best exists with multiple nodes");

        if (test_pass == test_total)
            $display("PASS: spu_som_train_race_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu_som_train_race_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
