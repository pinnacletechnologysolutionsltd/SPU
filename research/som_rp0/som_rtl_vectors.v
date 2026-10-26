`timescale 1ns / 1ps
// SOM-RP0a: drives the UNMODIFIED spu_som_bmu.v with vectors from build/som_rp0/rtl_vectors.mem
// (36 words of 36 bits per case: 28 node coefficients {Q,P}, 4 weights, 4 features) and prints raw
// outputs. Not named *tb*: prints values, not PASS/FAIL; rtl_compare.py judges them. RTL output is
// evidence of what the current RTL does, never the reference.
module som_rtl_vectors;
    localparam W = 18, NF = 4, FW = 2 * W;
    reg clk = 0, rst_n = 0, start = 0, we = 0;
    reg  [NF*FW-1:0] features, weights, wdata;
    reg  [2:0] addr = 0;
    wire done, bmu_valid, has_second, accum_overflow;
    wire [15:0] best_id, second_id, label;
    wire [63:0] best_q, second_q, gap;
    wire [NF*FW-1:0] rdata;
    reg [FW-1:0] mem [0:36*1024-1];
    integer n, c, k, j, ncases;

    spu_som_bmu #(.NUM_FEATURES(NF), .MAX_NODES(7), .WIDTH(W)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .done(done),
        .features(features), .feature_weights(weights),
        .bmu_valid(bmu_valid), .best_node_id(best_id), .second_node_id(second_id),
        .cluster_label(label), .best_q(best_q), .second_q(second_q),
        .confidence_gap(gap), .has_second(has_second), .accum_overflow(accum_overflow),
        .train_we(we), .train_addr(addr), .train_be(4'b1111),
        .train_wdata(wdata), .train_rdata(rdata));

    always #5 clk = ~clk;

    initial begin
        if (!$value$plusargs("N=%d", ncases)) ncases = 0;
        $readmemh("build/som_rp0/rtl_vectors.mem", mem);
        repeat (3) @(negedge clk);
        rst_n = 1;
        for (c = 0; c < ncases; c = c + 1) begin
            for (n = 0; n < 7; n = n + 1) begin
                for (j = 0; j < NF; j = j + 1) wdata[j*FW +: FW] = mem[c*36 + n*4 + j];
                @(negedge clk); addr = n; we = 1;
                @(negedge clk); we = 0;
            end
            for (j = 0; j < NF; j = j + 1) begin
                weights[j*FW +: FW]  = mem[c*36 + 28 + j];
                features[j*FW +: FW] = mem[c*36 + 32 + j];
            end
            @(negedge clk); start = 1;
            @(negedge clk); start = 0;
            wait (done);
            $display("R %0d %0d %0d %h %h %h %0d %0d", c, best_id, second_id, best_q, second_q, gap,
                     accum_overflow, has_second);
            @(negedge clk);
        end
        $finish;
    end
endmodule
