`timescale 1ns / 1ps

module spu13_som_bmu_tb;

    localparam WIDTH = 18;
    localparam FEATURE_W = 2 * WIDTH;
    localparam NUM_FEATURES = 4;

    reg clk;
    reg rst_n;
    reg start;
    wire done;

    reg  [NUM_FEATURES * FEATURE_W - 1:0] features;
    reg  [NUM_FEATURES * FEATURE_W - 1:0] feature_weights;
    wire bmu_valid;
    wire [15:0] best_node_id;
    wire [15:0] second_node_id;
    wire [15:0] cluster_label;
    wire [63:0] best_q;
    wire [63:0] second_q;
    wire [63:0] confidence_gap;
    wire has_second;
    wire axiomatic_fault;
    wire [3:0] fault_type;
    wire [31:0] fault_count;

    spu_som_bmu #(.NUM_FEATURES(NUM_FEATURES), .MAX_NODES(7), .WIDTH(WIDTH)) u_bmu (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .done(done),
        .features(features),
        .feature_weights(feature_weights),
        .bmu_valid(bmu_valid),
        .best_node_id(best_node_id),
        .second_node_id(second_node_id),
        .cluster_label(cluster_label),
        .best_q(best_q),
        .second_q(second_q),
        .confidence_gap(confidence_gap),
        .has_second(has_second),
        .axiomatic_level(2'b00),
        .axiomatic_fault(axiomatic_fault),
        .fault_type(fault_type),
        .fault_count(fault_count),
        .train_we(1'b0),
        .train_addr(3'd0),
        .train_be(4'b0000),
        .train_wdata({NUM_FEATURES * FEATURE_W{1'b0}}),
        .train_rdata()
    );

    always #5 clk = ~clk;

    function [FEATURE_W-1:0] rs;
        input signed [WIDTH-1:0] p;
        input signed [WIDTH-1:0] q;
        begin
            rs = {q, p};
        end
    endfunction

    function [NUM_FEATURES * FEATURE_W - 1:0] vec4;
        input [FEATURE_W-1:0] a;
        input [FEATURE_W-1:0] b;
        input [FEATURE_W-1:0] c;
        input [FEATURE_W-1:0] d;
        begin
            vec4 = {d, c, b, a};
        end
    endfunction

    integer test_pass, test_total;
    integer cycle_count, expected_latency;
    always @(posedge clk) cycle_count = cycle_count + 1;

    task run_case;
        input [NUM_FEATURES * FEATURE_W - 1:0] feature_vec;
        input [15:0] exp_best;
        input [15:0] exp_label;
        integer start_cycle;
        integer this_latency;
        begin
            test_total = test_total + 1;
            @(negedge clk);
            features = feature_vec;
            start_cycle = cycle_count;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            wait(done);
            #1;
            this_latency = cycle_count - start_cycle;
            if (expected_latency < 0)
                expected_latency = this_latency;

            if (bmu_valid !== 1'b1 ||
                best_node_id !== exp_best ||
                cluster_label !== exp_label ||
                axiomatic_fault !== 1'b0 ||
                this_latency != expected_latency) begin
                $display("FAIL: best=%0d label=%0d valid=%b fault=%b type=%h count=%0d latency=%0d expected_latency=%0d",
                         best_node_id, cluster_label, bmu_valid,
                         axiomatic_fault, fault_type, fault_count,
                         this_latency, expected_latency);
            end else begin
                test_pass = test_pass + 1;
            end

            repeat (2) @(posedge clk);
        end
    endtask

    initial begin
        clk = 0;
        rst_n = 0;
        start = 0;
        features = 0;
        feature_weights = vec4(rs(1, 0), rs(2, 0), rs(1, 0), rs(1, 0));
        test_pass = 0;
        test_total = 0;
        cycle_count = 0;
        expected_latency = -1;

        #20 rst_n = 1;
        repeat (2) @(posedge clk);

        run_case(vec4(rs(2, 0), rs(0, 0), rs(0, 0), rs(0, 0)), 16'd1, 16'd1);
        run_case(vec4(rs(0, 0), rs(2, 0), rs(0, 0), rs(0, 0)), 16'd2, 16'd1);
        run_case(vec4(rs(0, 0), rs(0, 0), rs(-2, 0), rs(1, 1)), 16'd6, 16'd3);

        // Exact Q(sqrt(3)) ordering regression. Node 5 has quadrance
        // 159+36sqrt(3); node 6 has 157+48sqrt(3). Lexicographic (P,Q)
        // ordering incorrectly picks node 6, while the exact order picks 5.
        run_case(vec4(rs(-3, -3), rs(-3, -3), rs(-3, -3), rs(-2, 3)),
                 16'd5, 16'd3);

        if (test_pass == test_total)
            $display("PASS: spu13_som_bmu_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: spu13_som_bmu_tb (%0d/%0d)", test_pass, test_total);
        $display("INFO: fixed SOM BMU latency = %0d clocks", expected_latency);

        $finish;
    end

endmodule
