`timescale 1ns / 1ps
// SOM-RP0a width probe: drives the UNMODIFIED spu_som_bmu.v with in-domain
// (signed 18-bit, uploader-valid) vectors and prints raw results for
// oracle_compare.py. Deliberately not named *tb* (not a regression bench) and
// prints values, not PASS/FAIL; the verdict is computed against the oracle.
module som_width_probe;
    localparam W = 18, NF = 4, FW = 2 * W;
    reg clk = 0, rst_n = 0, start = 0;
    reg  [NF*FW-1:0] features, weights, wdata;
    reg              we = 0;
    reg  [2:0]       addr = 0;
    wire             done, bmu_valid, has_second, accum_overflow;
    wire [15:0]      best_id, second_id, label;
    wire [63:0]      best_q, second_q, gap;
    wire [NF*FW-1:0] rdata;

    spu_som_bmu #(.NUM_FEATURES(NF), .MAX_NODES(7), .WIDTH(W)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .done(done),
        .features(features), .feature_weights(weights),
        .bmu_valid(bmu_valid), .best_node_id(best_id), .second_node_id(second_id),
        .cluster_label(label), .best_q(best_q), .second_q(second_q),
        .confidence_gap(gap), .has_second(has_second), .accum_overflow(accum_overflow),
        .train_we(we), .train_addr(addr), .train_be(4'b1111),
        .train_wdata(wdata), .train_rdata(rdata));

    always #5 clk = ~clk;

    function [FW-1:0] pq(input integer p, input integer q);
        pq = {q[W-1:0], p[W-1:0]};
    endfunction

    task load_all_nodes(input [NF*FW-1:0] w);
        integer n;
        begin
            for (n = 0; n < 7; n = n + 1) begin
                @(negedge clk); addr = n; wdata = w; we = 1;
                @(negedge clk); we = 0;
            end
        end
    endtask

    task classify(input [8*8-1:0] name);
        begin
            @(negedge clk); start = 1;
            @(negedge clk); start = 0;
            wait (done);
            $display("RTL %0s best_p=%0d best_q=%0d overflow=%0d best_id=%0d",
                     name, best_q[63:32], $signed(best_q[31:0]), accum_overflow, best_id);
            @(negedge clk);
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1;
        // C: safe-range positive control. x0=100+3r3, w0=-20+1r3, r=1.
        weights  = {pq(1,0), pq(1,0), pq(1,0), pq(1,0)};
        load_all_nodes({pq(0,0), pq(0,0), pq(0,0), pq(-20,1)});
        features = {pq(0,0), pq(0,0), pq(0,0), pq(100,3)};
        classify("control");
        // A: difference 2^18-1 exceeds the 18-bit difference field.
        load_all_nodes({pq(0,0), pq(0,0), pq(0,0), pq(-131072,0)});
        features = {pq(0,0), pq(0,0), pq(0,0), pq(131071,0)};
        classify("diffwrap");
        // B: weighted square 16 * 2^32 = 2^36 exceeds the 36-bit product field.
        weights  = {pq(1,0), pq(1,0), pq(1,0), pq(16,0)};
        load_all_nodes({pq(0,0), pq(0,0), pq(0,0), pq(0,0)});
        features = {pq(0,0), pq(0,0), pq(0,0), pq(65536,0)};
        classify("prodwrap");
        // D: per-feature in range, 4-feature sum > 2^32: existing flag case.
        weights  = {pq(1,0), pq(1,0), pq(1,0), pq(1,0)};
        features = {pq(60000,0), pq(60000,0), pq(60000,0), pq(60000,0)};
        classify("sumflag");
        $finish;
    end
endmodule
