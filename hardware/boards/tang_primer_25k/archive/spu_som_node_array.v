`timescale 1ns / 1ps

// spu_som_node_array.v — Parallel SOM node array with winner-take-all BMU
//
// Instantiates MAX_NODES copies of spu_som_node in parallel. All nodes
// compute quadrance simultaneously in a 3-stage pipeline.
//
// After all nodes finish (deterministic fixed latency), a combinational
// winner-take-all tree selects the Best Matching Unit (minimum quadrance)
// and the second-best unit (for confidence gap).
//
// This replaces the sequential scan in spu_som_bmu.v with fully parallel
// computation, trading area for classification speed.
//
// Training writes are dispatched to individual nodes via train_addr decode.

module spu_som_node_array #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 7,
    parameter WIDTH        = 18
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // Feature vector for classification
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] features,
    input  wire [NUM_FEATURES * WIDTH - 1 : 0]     feat_weights,

    // BMU results
    output reg          bmu_valid,
    output reg  [15:0]  best_node_id,
    output reg  [15:0]  second_node_id,
    output reg  [15:0]  best_label,
    output reg  [63:0]  best_quadrance,
    output reg  [63:0]  second_quadrance,
    output reg  [63:0]  confidence_gap,
    output reg          has_second,
    output reg          done,
    output wire         busy,

    // Training port
    input  wire         train_we,
    input  wire [$clog2(MAX_NODES)-1:0] train_addr,
    input  wire signed [WIDTH-1:0]      train_alpha_h,
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_features
);

    localparam IDX_W = $clog2(MAX_NODES);

    // ── Per-node signals ────────────────────────────────────────────
    wire [MAX_NODES-1:0]        node_done;
    wire [MAX_NODES-1:0]        node_busy;
    wire [63:0]                 node_quadrance [0:MAX_NODES-1];
    wire [15:0]                 node_label     [0:MAX_NODES-1];
    wire                        node_train_we  [0:MAX_NODES-1];
    wire [NUM_FEATURES*2*WIDTH-1:0] node_train_rdata [0:MAX_NODES-1];

    // ── Instantiate node array ──────────────────────────────────────
    genvar gn;
    generate
        for (gn = 0; gn < MAX_NODES; gn = gn + 1) begin : node_gen
            assign node_train_we[gn] = train_we && (train_addr == gn);

            spu_som_node #(
                .NUM_FEATURES(NUM_FEATURES),
                .WIDTH(WIDTH),
                .NODE_ID(gn)
            ) u_node (
                .clk(clk), .rst_n(rst_n),
                .start(start),
                .features(features),
                .feat_weights(feat_weights),
                .quadrance(node_quadrance[gn]),
                .done(node_done[gn]),
                .busy(node_busy[gn]),
                .node_label(node_label[gn]),
                .train_we(node_train_we[gn]),
                .train_alpha_h(train_alpha_h),
                .train_features(train_features),
                .train_rdata(node_train_rdata[gn])
            );
        end
    endgenerate

    // ── All-done detection ──────────────────────────────────────────
    wire all_done = &node_done;
    assign busy = |node_busy;

    // ── Winner-take-all comparator tree ─────────────────────────────
    // Combinational: selects minimum quadrance among all nodes.
    // Uses P component as primary key, Q component as tiebreaker.
    //
    // We build a logarithmic reduction tree. For MAX_NODES=7,
    // it's small enough for a flat priority-min chain.

    function [63:0] min_quadrance;
        input [63:0] a, b;
        begin
            if (a[63:32] < b[63:32])
                min_quadrance = a;
            else if (a[63:32] > b[63:32])
                min_quadrance = b;
            else if ($signed(a[31:0]) < $signed(b[31:0]))
                min_quadrance = a;
            else
                min_quadrance = b;
        end
    endfunction

    function [63:0] max_quadrance;
        input [63:0] a, b;
        begin
            if (a[63:32] > b[63:32])
                max_quadrance = a;
            else if (a[63:32] < b[63:32])
                max_quadrance = b;
            else if ($signed(a[31:0]) > $signed(b[31:0]))
                max_quadrance = a;
            else
                max_quadrance = b;
        end
    endfunction

    // Two-pass: find best (minimum) and second-best
    // Pass 1: find best node
    wire [63:0] wta_best_q;
    wire [IDX_W:0] wta_best_id;  // extra bit for sentinel
    wire [15:0]    wta_best_label;

    // Using generate for the winner-take-all reduction
    // For small MAX_NODES, unroll directly
    wire [63:0] wta_stage [0:MAX_NODES];
    wire [IDX_W:0] wta_id_stage [0:MAX_NODES];
    wire [15:0]    wta_label_stage [0:MAX_NODES];

    assign wta_stage[0]       = node_quadrance[0];
    assign wta_id_stage[0]    = {1'b0, {IDX_W{1'b0}}};
    assign wta_label_stage[0] = node_label[0];

    genvar wi;
    generate
        for (wi = 1; wi < MAX_NODES; wi = wi + 1) begin : wta_chain
            wire better = (node_quadrance[wi][63:32] < wta_stage[wi-1][63:32]) ||
                         ((node_quadrance[wi][63:32] == wta_stage[wi-1][63:32]) &&
                          ($signed(node_quadrance[wi][31:0]) < $signed(wta_stage[wi-1][31:0])));
            assign wta_stage[wi]       = better ? node_quadrance[wi] : wta_stage[wi-1];
            assign wta_id_stage[wi]    = better ? wi[IDX_W:0]       : wta_id_stage[wi-1];
            assign wta_label_stage[wi] = better ? node_label[wi]     : wta_label_stage[wi-1];
        end
    endgenerate

    assign wta_best_q     = wta_stage[MAX_NODES-1];
    assign wta_best_id    = wta_id_stage[MAX_NODES-1];
    assign wta_best_label = wta_label_stage[MAX_NODES-1];

    // Pass 2: find second-best (minimum excluding best)
    // For each non-best node, compare against running second-best
    wire [63:0] wta_sec_stage [0:MAX_NODES];
    wire [IDX_W:0] wta_sec_id_stage [0:MAX_NODES];

    // Init with sentinel (max value)
    assign wta_sec_stage[0]    = 64'hFFFFFFFF_FFFFFFFF;
    assign wta_sec_id_stage[0] = {1'b1, {IDX_W{1'b0}}};  // invalid sentinel

    genvar wj;
    generate
        for (wj = 1; wj < MAX_NODES; wj = wj + 1) begin : wta_sec_chain
            wire is_best     = (wj[IDX_W:0] == wta_best_id);
            wire better_sec  = !is_best && (
                               (node_quadrance[wj][63:32] < wta_sec_stage[wj-1][63:32]) ||
                              ((node_quadrance[wj][63:32] == wta_sec_stage[wj-1][63:32]) &&
                               ($signed(node_quadrance[wj][31:0]) < $signed(wta_sec_stage[wj-1][31:0]))));
            assign wta_sec_stage[wj]    = better_sec ? node_quadrance[wj] : wta_sec_stage[wj-1];
            assign wta_sec_id_stage[wj] = better_sec ? wj[IDX_W:0]       : wta_sec_id_stage[wj-1];
        end
    endgenerate

    // Handle node 0 as well (separate from the generate loop above)
    // The loop starts at 1, so we need to also check node 0
    wire node0_is_best = (wta_best_id == 0);
    wire node0_better_sec = !node0_is_best && (
        (node_quadrance[0][63:32] < wta_sec_stage[MAX_NODES-1][63:32]) ||
       ((node_quadrance[0][63:32] == wta_sec_stage[MAX_NODES-1][63:32]) &&
        ($signed(node_quadrance[0][31:0]) < $signed(wta_sec_stage[MAX_NODES-1][31:0]))));

    wire [63:0]    wta_sec_final_q  = node0_better_sec ? node_quadrance[0] : wta_sec_stage[MAX_NODES-1];
    wire [IDX_W:0] wta_sec_final_id = node0_better_sec ? {1'b0, {IDX_W{1'b0}}} : wta_sec_id_stage[MAX_NODES-1];
    wire           wta_has_second   = !wta_sec_final_id[IDX_W];  // valid if MSB not set

    // ── Output register ────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bmu_valid        <= 1'b0;
            done             <= 1'b0;
            best_node_id     <= 16'd0;
            second_node_id   <= 16'd0;
            best_label       <= 16'd0;
            best_quadrance   <= 64'd0;
            second_quadrance <= 64'd0;
            confidence_gap   <= 64'd0;
            has_second       <= 1'b0;
        end else begin
            done      <= 1'b0;
            bmu_valid <= 1'b0;
            if (all_done) begin
                best_node_id     <= {{(16-IDX_W){1'b0}}, wta_best_id[IDX_W-1:0]};
                second_node_id   <= wta_has_second ? {{(16-IDX_W){1'b0}}, wta_sec_final_id[IDX_W-1:0]} : 16'd0;
                best_label       <= wta_best_label;
                best_quadrance   <= wta_best_q;
                second_quadrance <= wta_has_second ? wta_sec_final_q : 64'd0;
                has_second       <= wta_has_second;
                confidence_gap   <= wta_has_second
                    ? {wta_sec_final_q[63:32] - wta_best_q[63:32],
                       wta_sec_final_q[31:0]  - wta_best_q[31:0]}
                    : 64'd0;
                bmu_valid <= 1'b1;
                done      <= 1'b1;
            end
        end
    end

endmodule
