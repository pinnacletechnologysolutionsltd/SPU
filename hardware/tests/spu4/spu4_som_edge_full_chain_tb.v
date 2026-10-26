// spu4_som_edge_full_chain_tb.v -- the SPU-4 edge SOM checked against a real
// software oracle, not a hand-built fixture.
//
// spu4_som_edge_tb.v, spu4_som_flash_loader_tb.v, and spu4_som_edge_wrapper_tb.v
// all check "the BMU picks the exact-match node" -- true, but an exact-match
// query (features == weights) gives quadrance 0 regardless of which features
// actually get summed, so it cannot expose a dropped feature term. This file
// drives the whole product chain (mock SPI flash -> spu4_som_flash_loader ->
// spu4_som_edge -> spu4_som_edge_wrapper handshake) with 8 queries whose
// (best_node, best_quadrance) verdicts are computed by
// software/lib/spu4_som_edge_oracle.py (see software/tests/
// test_spu4_som_edge_oracle.py for the same fixture run through that oracle
// directly) -- including near-misses, negative deltas, a genuine exact tie,
// and one query whose verdict depends on feature index 3.
//
// That last one is load-bearing: it is the regression check for a real bug
// found building this file 2026-08-17 -- spu4_som_edge.v's quadrance sum was
// hardcoded to exactly three terms (f0_q+f1_q+f2_q) regardless of the
// NUM_FEATURES parameter, silently dropping feature 3 (and beyond) whenever
// instantiated with NUM_FEATURES=4, which spu4_som_edge_wrapper.v does for
// the INA226 capture contract. Fixed in the same commit as this file, in a
// generic NUM_FEATURES-wide sum. Query 8 below (best_node=1, Q=6400) would
// read best_node=3, Q=300 under the old hardcoded-3-feature sum.
//
// Mock flash SPI slave technique matches spu4_som_edge_wrapper_tb.v /
// spu4_som_flash_loader_tb.v: drive MISO on negedge SCLK from a byte memory
// once CS is asserted.

`timescale 1ns / 1ps

module spu4_som_edge_full_chain_tb;

    localparam integer NUM_FEATURES = 4;
    localparam integer WIDTH        = 16;
    localparam integer FEATURE_W    = 2 * WIDTH;
    localparam integer NODE_W       = NUM_FEATURES * FEATURE_W;
    localparam integer TOTAL_BYTES  = 4 * NUM_FEATURES * (FEATURE_W / 8);

    reg clk = 0, rst_n = 0, start = 0;
    reg [NODE_W-1:0] features = 0;
    wire busy, done;
    wire [1:0] best_node;
    wire [31:0] best_quadrance;
    wire [7:0] status;
    wire [15:0] id;
    wire flash_sclk, flash_cs_n, flash_mosi;
    reg  flash_miso = 0;

    spu4_som_edge_wrapper #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        .features(features),
        .best_node(best_node), .best_quadrance(best_quadrance),
        .status(status), .id(id),
        .flash_sclk(flash_sclk), .flash_cs_n(flash_cs_n),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    always #10 clk = ~clk;

    integer pass = 0, fail = 0;
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // ── Boot weights: oracle fixture, NOT the formulaic "demo" profile ───
    // software/lib/spu4_som_edge_oracle.py's NODES, transcribed exactly.
    reg signed [15:0] exp_p [0:3][0:NUM_FEATURES-1];
    reg signed [15:0] exp_q [0:3][0:NUM_FEATURES-1];

    initial begin
        // Node 0: (100,0) (0,0) (0,0) (0,0)
        exp_p[0][0]=100; exp_q[0][0]=0;  exp_p[0][1]=0; exp_q[0][1]=0;
        exp_p[0][2]=0;   exp_q[0][2]=0;  exp_p[0][3]=0; exp_q[0][3]=0;
        // Node 1: (0,0) (0,40) (0,0) (0,0)
        exp_p[1][0]=0;   exp_q[1][0]=0;  exp_p[1][1]=0; exp_q[1][1]=40;
        exp_p[1][2]=0;   exp_q[1][2]=0;  exp_p[1][3]=0; exp_q[1][3]=0;
        // Node 2: (-30,0) (-30,0) (60,0) (0,0)
        exp_p[2][0]=-30; exp_q[2][0]=0;  exp_p[2][1]=-30; exp_q[2][1]=0;
        exp_p[2][2]=60;  exp_q[2][2]=0;  exp_p[2][3]=0;   exp_q[2][3]=0;
        // Node 3: (0,0) (0,0) (0,0) (50,50)
        exp_p[3][0]=0;   exp_q[3][0]=0;  exp_p[3][1]=0; exp_q[3][1]=0;
        exp_p[3][2]=0;   exp_q[3][2]=0;  exp_p[3][3]=50; exp_q[3][3]=50;
    end

    // ── Mock flash: node-major, feature-ascending, P_hi P_lo Q_hi Q_lo ───
    reg [7:0] spi_mem [0:TOTAL_BYTES-1];
    integer n, f, idx;
    initial begin
        #1; // let the exp_p/exp_q initial block above run first
        idx = 0;
        for (n = 0; n < 4; n = n + 1) begin
            for (f = 0; f < NUM_FEATURES; f = f + 1) begin
                spi_mem[idx] = exp_p[n][f][15:8]; idx = idx + 1;
                spi_mem[idx] = exp_p[n][f][7:0];  idx = idx + 1;
                spi_mem[idx] = exp_q[n][f][15:8]; idx = idx + 1;
                spi_mem[idx] = exp_q[n][f][7:0];  idx = idx + 1;
            end
        end
    end

    integer total_bits, sbn, sbyt;
    always @(negedge flash_cs_n) total_bits = 0;
    always @(negedge flash_sclk) begin
        if (!flash_cs_n) begin
            total_bits = total_bits + 1;
            if (total_bits >= 32) begin
                idx  = total_bits - 32;
                sbn  = idx % 8;
                sbyt = idx / 8;
                flash_miso = (sbyt < TOTAL_BYTES) ? spi_mem[sbyt][7-sbn] : 1'b0;
            end
        end
    end

    // Pack a 4-feature query the same way spu4_som_edge expects: feature 0
    // in the low bits, each feature as {P, Q} with P in the upper 16 bits.
    function [NODE_W-1:0] pack4;
        input signed [15:0] p0, q0, p1, q1, p2, q2, p3, q3;
        begin
            pack4 = {p3, q3, p2, q2, p1, q1, p0, q0};
        end
    endfunction

    // Drive one classification and check the oracle-computed verdict.
    task run_query;
        input [255:0] label;
        input signed [15:0] p0, q0, p1, q1, p2, q2, p3, q3;
        input [1:0]  exp_node;
        input [31:0] exp_quad;
        begin
            features = pack4(p0, q0, p1, q1, p2, q2, p3, q3);
            @(posedge clk); start <= 1; @(posedge clk); start <= 0; #1;
            begin : wait_done
                integer t;
                t = 0;
                while (!done && t < 200) begin @(posedge clk); t = t + 1; end
                if (!done) bad({label, ": classification never completed"});
            end
            if (best_node !== exp_node)
                bad({label, ": best_node mismatch vs oracle"});
            else
                ok({label, ": best_node matches oracle"});
            if (best_quadrance !== exp_quad)
                bad({label, ": best_quadrance mismatch vs oracle"});
            else
                ok({label, ": best_quadrance matches oracle exactly"});
        end
    endtask

    initial begin
        #100 rst_n = 1; repeat (4) @(posedge clk);

        begin : wait_hydrated
            integer t;
            t = 0;
            while (!status[2] && t < 20000) begin @(posedge clk); t = t + 1; end
            if (!status[2]) bad("wrapper never hydrated");
            else            ok("wrapper hydrated from the oracle-fixture flash image");
        end

        // Every (best_node, best_quadrance) pair below is oracle output --
        // see software/tests/test_spu4_som_edge_oracle.py's QUERIES, same
        // fixture, run through find_bmu_edge() directly.
        run_query("exact match node 0",           100, 0,   0, 0,   0, 0,   0, 0,    2'd0, 32'd0);
        run_query("exact match node 1",             0, 0,   0, 40,  0, 0,   0, 0,    2'd1, 32'd0);
        run_query("exact match node 2",           -30, 0, -30, 0,  60, 0,   0, 0,    2'd2, 32'd0);
        run_query("exact match node 3",             0, 0,   0, 0,   0, 0,  50, 50,   2'd3, 32'd0);
        run_query("near node 1, Q-dominated delta",  0, 0,   0, 45,  0, 0,   0, 0,    2'd1, 32'd75);
        run_query("negative deltas near node 2",   -40, 0, -25, 0,  55, 0,   0, 0,    2'd2, 32'd150);
        // Exact tie: node 0 and node 1 both quadrance 3700. Strict `<` in
        // the RTL scan keeps the first (lowest-index) winner.
        run_query("exact tie node 0 / node 1",      50, 0,   0, 20,  0, 0,   0, 0,    2'd0, 32'd3700);
        // Load-bearing regression check -- see file header. Under the bug
        // this fixture would read (node 3, Q=300) instead.
        run_query("far from all nodes, mixed sign", -5, 5,   5, -5, -5, 5,   5, -5,   2'd1, 32'd6400);

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else            $display("FAIL");
        $finish;
    end

    initial begin
        #3_000_000;
        $display("FAIL: timeout");
        $display("FAIL");
        $finish;
    end

endmodule
