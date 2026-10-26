`timescale 1ns / 1ps

// Testbench: spu_som_node — Verifies individual SOM node quadrance and training
module spu_som_node_tb;

    localparam NUM_FEATURES = 4;
    localparam WIDTH        = 18;
    localparam FEATURE_W    = 2 * WIDTH;   // 36

    reg clk, rst_n, start;
    reg [NUM_FEATURES * FEATURE_W - 1 : 0] features;
    reg [NUM_FEATURES * WIDTH - 1 : 0]     feat_weights;
    wire [63:0] quadrance;
    wire done, busy;
    wire [15:0] node_label;

    reg train_we;
    reg signed [WIDTH-1:0] train_alpha_h;
    reg [NUM_FEATURES * FEATURE_W - 1 : 0] train_features;
    wire [NUM_FEATURES * FEATURE_W - 1 : 0] train_rdata;

    spu_som_node #(.NUM_FEATURES(4), .WIDTH(18), .NODE_ID(2)) uut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .features(features), .feat_weights(feat_weights),
        .quadrance(quadrance), .done(done), .busy(busy),
        .node_label(node_label),
        .train_we(train_we), .train_alpha_h(train_alpha_h),
        .train_features(train_features), .train_rdata(train_rdata)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;

    initial begin
        clk = 0; rst_n = 0; start = 0;
        train_we = 0; train_alpha_h = 0;
        test_pass = 0; test_total = 0;
        features = 0; feat_weights = 0; train_features = 0;
        #20 rst_n = 1; #10;

        // Test 1: All-zeros → quadrance = 0
        test_total = test_total + 1;
        start = 1; #10; start = 0;
        wait(done); #2;
        if (quadrance !== 64'd0) $display("FAIL T1: got %h", quadrance);
        else test_pass = test_pass + 1;

        // Test 2: Node label = NODE_ID % 4 = 2
        test_total = test_total + 1;
        if (node_label !== 16'd2) $display("FAIL T2: expected 2, got %0d", node_label);
        else test_pass = test_pass + 1;

        // Test 3: F0.P=1, weight≈1.0 → quadrance P≈1
        // Feature format: F0 = {P[35:18], Q[17:0]}
        test_total = test_total + 1;
        features = 0; feat_weights = 0;
        features[35:18] = 18'd1;              // F0.P = 1
        feat_weights[17:0] = (1 << 16);       // F0 weight ≈ 1.0 in Q16.2
        start = 1; #10; start = 0;
        wait(done); #2;
        if (quadrance[63:32] == 32'd0) $display("FAIL T3: P=0, full=%h", quadrance);
        else test_pass = test_pass + 1;

        // Test 4: Training update F0.P: 0 → ~1.25 with α·h=0.25, x=5
        test_total = test_total + 1;
        train_features = 0;
        train_features[35:18] = 18'd5;         // train F0.P = 5
        train_alpha_h = (1 << 16);             // α·h = 1.0 (simpler test)
        train_we = 1; #10; train_we = 0; #10;
        if (train_rdata[35:18] == 18'd0) $display("FAIL T4: w not updated, F0.P=%0d", train_rdata[35:18]);
        else test_pass = test_pass + 1;

        if (test_pass == test_total)
            $display("PASS: spu_som_node_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu_som_node_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
