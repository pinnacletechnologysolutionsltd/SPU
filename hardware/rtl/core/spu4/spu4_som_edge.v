// spu4_som_edge.v — Lightweight Kohonen BMU for SPU-4 edge node
//
// Arlinghaus micro-tier SOM: 4-node register-backed Best Matching Unit
// classifier using rational quadrance (no square roots, no floats).
// Designed to fit the SPU-4's ~400 LUT edge budget alongside the
// Euclidean ALU, decoder, and UART fixture.
//
// Architecture:
//   - 4 nodes × 3 features × 32-bit signed surd per feature
//   - Register-backed weights (no BRAM)
//   - Sequential scan: one node per cycle, combinational quadrance
//   - Tracks minimum quadrance and its node index
//   - Output som_label[1:0] feeds into spu4_cluster_bridge.v
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

    // ── Weight registers ──────────────────────────────────────────────
    reg [NODE_W - 1 : 0] weights [0:3];
    always @(posedge clk) begin
        if (weight_we)
            weights[weight_node] <= weight_data;
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

    // Combinational quadrance for current node
    wire [63:0] f0_q = feature_quadrance(
        features[1*FEATURE_W-1 : 0*FEATURE_W],
        weights[node_idx][1*FEATURE_W-1 : 0*FEATURE_W]);
    wire [63:0] f1_q = feature_quadrance(
        features[2*FEATURE_W-1 : 1*FEATURE_W],
        weights[node_idx][2*FEATURE_W-1 : 1*FEATURE_W]);
    wire [63:0] f2_q = feature_quadrance(
        features[3*FEATURE_W-1 : 2*FEATURE_W],
        weights[node_idx][3*FEATURE_W-1 : 2*FEATURE_W]);
    wire [63:0] node_quadrance = f0_q + f1_q + f2_q;

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
