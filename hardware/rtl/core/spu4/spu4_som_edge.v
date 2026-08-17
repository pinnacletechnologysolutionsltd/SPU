// spu4_som_edge.v — Lightweight Kohonen BMU for SPU-4 edge node
//
// Arlinghaus micro-tier SOM: 4-node register-backed Best Matching Unit
// classifier using rational quadrance (no square roots, no floats).
// Designed to fit the SPU-4's edge budget alongside the
// Euclidean ALU, decoder, and UART fixture.
//
// Architecture:
//   - 4 nodes × 3 features × 32-bit signed surd per feature
//   - Register-backed weights (no BRAM)
//   - Sequential scan: one node per cycle, combinational quadrance
//   - Tracks minimum quadrance and its node index
//   - Output is a 2-bit winner node, not a semantic label
//   - A deployment-specific node→class mapper is required before the
//     4-bit som_label input of spu4_cluster_bridge.v
//
// Lifecycle: RTL/TB experiment only. This module is not instantiated by an
// SPU-4 core or board top, has no host weight-upload path, and has not been
// synthesized or proven in silicon.
//
// Quadrance of surd (p + q√3): Q = p² + 3q²  (no division, no sqrt)

module spu4_som_edge #(
    parameter NUM_FEATURES = 3,
    parameter WIDTH        = 16
) (
    input  wire         clk,
    input  wire         rst_n,

    input  wire         start,
    output reg          done,

    // Feature vector: {F2_P, F2_Q, F1_P, F1_Q, F0_P, F0_Q}
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] features,

    // Weight load port
    input  wire         weight_we,
    input  wire [1:0]   weight_node,
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] weight_data,

    // BMU results
    output reg          bmu_valid,
    output reg  [1:0]   best_node,
    output reg  [31:0]  best_quadrance
);

    localparam FEATURE_W = 2 * WIDTH;
    localparam NODE_W    = NUM_FEATURES * FEATURE_W;

    // ── Weight registers (flat — Icarus 14 submodule-NBA workaround) ─
    reg [NODE_W - 1 : 0] weight0, weight1, weight2, weight3;
    initial begin weight0=0; weight1=0; weight2=0; weight3=0; end
    always @(posedge clk) begin
        if (weight_we) begin
            case (weight_node)
                2'd0: weight0 <= weight_data;
                2'd1: weight1 <= weight_data;
                2'd2: weight2 <= weight_data;
                2'd3: weight3 <= weight_data;
            endcase
        end
    end

    // ── Per-feature combinational quadrance ───────────────────────────
    function [63:0] feature_quadrance;
        input [FEATURE_W - 1 : 0] feat_in;
        input [FEATURE_W - 1 : 0] feat_wt;
        reg signed [WIDTH:0] dp, dq;  // one extra bit for sign
        reg signed [2*WIDTH+1:0] sq_p, sq_q;
        begin
            dp = $signed({feat_in[FEATURE_W-1], feat_in[FEATURE_W-1:WIDTH]}) -
                 $signed({feat_wt[FEATURE_W-1], feat_wt[FEATURE_W-1:WIDTH]});
            dq = $signed({feat_in[WIDTH-1], feat_in[WIDTH-1:0]}) -
                 $signed({feat_wt[WIDTH-1], feat_wt[WIDTH-1:0]});
            sq_p = dp * dp;
            sq_q = dq * dq;
            feature_quadrance = {32'd0, sq_p} + {30'd0, sq_q, 2'd0} - {32'd0, sq_q};  // sq_p + 3*sq_q
        end
    endfunction

    // ── Sequential scan FSM ──────────────────────────────────────────
    localparam S_IDLE  = 2'd0;
    localparam S_SCAN  = 2'd1;
    localparam S_DONE  = 2'd2;

    reg [1:0] state;
    reg [1:0] node_idx;
    reg [63:0] best_q;
    reg [1:0]  best_idx;

    // Mux active node's weight register
    wire [NODE_W - 1 : 0] w = (node_idx == 2'd0) ? weight0 :
                               (node_idx == 2'd1) ? weight1 :
                               (node_idx == 2'd2) ? weight2 : weight3;

    // Combinational quadrance for current node — sum of feature_quadrance
    // across all NUM_FEATURES features. Previously hardcoded to exactly
    // three terms (f0_q+f1_q+f2_q) regardless of NUM_FEATURES, which
    // silently dropped feature index 3 (and any beyond) from the BMU
    // decision whenever this module was instantiated with NUM_FEATURES=4,
    // as spu4_som_edge_wrapper.v does for the INA226 capture contract. An
    // exact-match query never exposes a dropped feature (its delta is 0
    // either way), which is why the existing TBs' exact-match checks
    // passed despite the bug. Found 2026-08-17 building the oracle-checked
    // full-chain testbench.
    reg [63:0] node_quadrance;
    integer feat_i;
    always @* begin
        node_quadrance = 64'd0;
        for (feat_i = 0; feat_i < NUM_FEATURES; feat_i = feat_i + 1) begin
            node_quadrance = node_quadrance + feature_quadrance(
                features[feat_i*FEATURE_W +: FEATURE_W],
                w[feat_i*FEATURE_W +: FEATURE_W]);
        end
    end

    // Combinational winner for this cycle
    wire node_wins = (node_quadrance < best_q);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            done     <= 1'b0;
            bmu_valid <= 1'b0;
            best_node <= 2'd0;
            best_quadrance <= 32'd0;
            node_idx <= 2'd0;
            best_q   <= 64'hFFFFFFFFFFFFFFFF;
            best_idx <= 2'd0;
        end else begin
            done     <= 1'b0;
            bmu_valid <= 1'b0;

            case (state)
                S_IDLE: begin
                    if (start) begin
                        node_idx <= 2'd0;
                        best_q   <= 64'hFFFFFFFFFFFFFFFF;
                        best_idx <= 2'd0;
                        state    <= S_SCAN;
                    end
                end

                S_SCAN: begin
                    // Update best tracker: if current node wins, latch its index
                    if (node_wins) begin
                        best_q   <= node_quadrance;
                        best_idx <= node_idx;
                    end

                    if (node_idx == 3) begin
                        // Last node: output the winner
                        bmu_valid <= 1'b1;
                        best_node <= node_wins ? node_idx : best_idx;
                        best_quadrance <= node_wins ? node_quadrance[31:0] : best_q[31:0];
                        done  <= 1'b1;
                        state <= S_DONE;
                    end else begin
                        node_idx <= node_idx + 2'd1;
                    end
                end

                S_DONE: state <= S_IDLE;

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
