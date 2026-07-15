// spu_som_sidecar_top_tb.v -- Smoke test for standalone SOM sidecar.

`timescale 1ns / 1ps

module spu_som_sidecar_top_tb;
    localparam CLK_PERIOD = 20;
    localparam NUM_FEATURES = 4;
    localparam MAX_NODES = 7;
    localparam WIDTH = 18;
    localparam FEATURE_W = 2 * WIDTH;
    localparam VEC_W = NUM_FEATURES * FEATURE_W;

    reg clk;
    reg rst_n;

    reg        cfg_wr_en;
    reg [2:0]  cfg_sel;
    reg [7:0]  cfg_material;
    reg [9:0]  cfg_addr;
    reg [63:0] cfg_data;

    wire       qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    wire [7:0] debug_status;
    wire [2:0] debug_state;

    spu_som_sidecar_top #(
        .NUM_FEATURES(NUM_FEATURES),
        .MAX_NODES(MAX_NODES),
        .WIDTH(WIDTH)
    ) u_sidecar (
        .clk(clk),
        .rst_n(rst_n),
        .cfg_wr_en(cfg_wr_en),
        .cfg_sel(cfg_sel),
        .cfg_material(cfg_material),
        .cfg_addr(cfg_addr),
        .cfg_data(cfg_data),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .debug_status(debug_status),
        .debug_state(debug_state)
    );

    always #(CLK_PERIOD/2) clk = ~clk;

    // Latch QR commit for test checking
    reg qr_seen;
    reg [63:0] qr_A, qr_B, qr_C, qr_D;
    always @(posedge clk) begin
        if (qr_commit_valid) begin
            qr_seen <= 1;
            qr_A <= qr_commit_A;
            qr_B <= qr_commit_B;
            qr_C <= qr_commit_C;
            qr_D <= qr_commit_D;
        end
    end

    // Monitor sidecar internal state
    always @(posedge clk) begin
        if (u_sidecar.state != 0 || u_sidecar.run || u_sidecar.bmu_done_r || u_sidecar.train_we_r)
            $display("DBG clk=%0d: state=%0d run=%d bmu_done=%d bmu_done_r=%d train_we=%d feat_reg0=%h",
                $time, u_sidecar.state, u_sidecar.run, u_sidecar.bmu_done,
                u_sidecar.bmu_done_r, u_sidecar.train_we_r,
                u_sidecar.feature_reg[0]);
    end

    function [63:0] pack_rs;
        input [WIDTH-1:0] p;
        input [WIDTH-1:0] q;
        begin
            // Pack as {28'd0, Q[17:0], P[17:0]} = 64 bits.
            // cfg_data[35:0] extracts {Q[17:0], P[17:0]} for the feature.
            pack_rs = {28'd0, q[17:0], p[17:0]};
        end
    endfunction

    // Drive with non-blocking assignments (proper Verilog)
    task write_cfg;
        input [2:0] sel;
        input [7:0] material;
        input [9:0] addr;
        input [63:0] data;
        begin
            @(posedge clk);
            cfg_sel <= sel; cfg_material <= material;
            cfg_addr <= addr; cfg_data <= data;
            cfg_wr_en <= 1;
            @(posedge clk);
            cfg_wr_en <= 0;
            @(posedge clk);
        end
    endtask

    task write_feature;
        input [3:0] idx;
        input [WIDTH-1:0] p;
        input [WIDTH-1:0] q;
        begin
            write_cfg(3'd5, {4'd0, idx}, 10'd0, pack_rs(p, q));
        end
    endtask

    task write_weight;
        input [9:0] node;
        input [3:0] feat;
        input [WIDTH-1:0] p;
        input [WIDTH-1:0] q;
        begin
            write_cfg(3'd4, {4'd0, feat}, node, pack_rs(p, q));
        end
    endtask

    task classify_and_wait;
        begin
            qr_seen = 0;
            write_cfg(3'd6, 8'd0, 10'd0, 64'd0);
            wait (qr_seen);
            #(CLK_PERIOD);
        end
    endtask

    integer pass_count, fail_count;

    initial begin
        clk = 0;
        rst_n = 0;
        cfg_wr_en = 0; cfg_sel = 0; cfg_material = 0; cfg_addr = 0; cfg_data = 0;
        qr_seen = 0;
        pass_count = 0; fail_count = 0;

        #(CLK_PERIOD * 4);
        rst_n = 1;
        #(CLK_PERIOD * 2);

        // ── Write node 0, feature 0 weight = {P=2, Q=0} ──────────────
        write_weight(10'd0, 4'd0, 18'sd2, 18'sd0);
        // Write node 6, feature 3 weight = {P=4, Q=1}
        write_weight(10'd6, 4'd3, 18'sd4, 18'sd1);

        $display("--- Test 1: feature {2,0,0,0} -> expect node 0 ---");
        write_feature(4'd0, 18'sd2, 18'sd0);
        write_feature(4'd1, 18'sd0, 18'sd0);
        write_feature(4'd2, 18'sd0, 18'sd0);
        write_feature(4'd3, 18'sd0, 18'sd0);

        classify_and_wait;

        if (qr_A[63:48] == 16'd0) begin
            $display("PASS test 1: best_node_id=0");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL test 1: best_node_id=%0d (expected 0)", qr_A[63:48]);
            fail_count = fail_count + 1;
        end

        // ── Test 2: feature {4+√3,0,0,4+√3} → expect node 6 ──────────
        $display("--- Test 2: feature {4+√3,0,0,4+√3} -> expect node 6 ---");
        write_feature(4'd0, 18'sd4, 18'sd1);
        write_feature(4'd1, 18'sd0, 18'sd0);
        write_feature(4'd2, 18'sd0, 18'sd0);
        write_feature(4'd3, 18'sd4, 18'sd1);

        classify_and_wait;

        if (qr_A[63:48] == 16'd6) begin
            $display("PASS test 2: best_node_id=6");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL test 2: best_node_id=%0d (expected 6)", qr_A[63:48]);
            fail_count = fail_count + 1;
        end

        // ── Summary ───────────────────────────────────────────────────
        if (fail_count == 0)
            $display("PASS: %0d checks passed", pass_count);
        else
            $display("FAIL: %0d passed, %0d failed", pass_count, fail_count);

        $finish;
    end
endmodule
