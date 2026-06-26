`timescale 1ns / 1ps

// spu_som_node.v — Individual SOM node cell with parallel subtract-and-square
//
// Each node stores a weight vector of NUM_FEATURES features in Q(√3) rational-surd
// format: each feature = {P[WIDTH-1:0], Q[WIDTH-1:0]}, total 2×WIDTH bits.
//
// On start: computes weighted quadrance Q = Σ w_j · (x_j − node_w_j)²
//   across all features simultaneously using parallel subtract-and-square lanes.
//
// On train_we: updates weights via w ← w + α · h · (x − w)
//   where α·h is a pre-computed scalar learning-rate × neighborhood factor.
//
// Pipeline: 3 stages
//   Stage 0: subtract (x − w) for all features
//   Stage 1: square each difference → per-feature quadrance
//   Stage 2: accumulate across features → total quadrance

module spu_som_node #(
    parameter NUM_FEATURES = 4,
    parameter WIDTH        = 18,
    parameter NODE_ID      = 0
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // Feature vector: {F3, F2, F1, F0}, each 2×WIDTH bits
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] features,

    // Feature weights for weighted quadrance (one per feature, scalar)
    input  wire [NUM_FEATURES * WIDTH - 1 : 0]     feat_weights,

    // Result: {quadrance_P[31:0], quadrance_Q[31:0]}
    output reg  [63:0]  quadrance,
    output reg          done,
    output wire         busy,

    // Label output (classification category)
    output wire [15:0]  node_label,

    // ── Training port ──────────────────────────────────────────────
    input  wire         train_we,
    input  wire signed [WIDTH-1:0]  train_alpha_h,  // α · h_ci scalar
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_features, // x vector for training
    output wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_rdata      // current weights readback
);

    localparam FEATURE_W = 2 * WIDTH;               // bits per feature {P,Q}
    localparam NODE_W    = NUM_FEATURES * FEATURE_W; // bits per node

    // ── Local weight storage ───────────────────────────────────────
    reg signed [WIDTH-1:0] weights_p [0:NUM_FEATURES-1];
    reg signed [WIDTH-1:0] weights_q [0:NUM_FEATURES-1];

    // Default weights: identity cluster center (all zeros → R0 origin)
    integer wi;
    initial begin
        for (wi = 0; wi < NUM_FEATURES; wi = wi + 1) begin
            weights_p[wi] = {WIDTH{1'b0}};
            weights_q[wi] = {WIDTH{1'b0}};
        end
    end

    // ── Label ──────────────────────────────────────────────────────
    // Node label is the node's classification category (0–3 cyclic)
    wire [15:0] label_wire;
    assign label_wire = (NUM_FEATURES >= 4) ? (NODE_ID % 4) : (NODE_ID % NUM_FEATURES);
    assign node_label = label_wire;

    // ── Training readback ──────────────────────────────────────────
    genvar tr;
    generate
        for (tr = 0; tr < NUM_FEATURES; tr = tr + 1) begin : trd_pack
            assign train_rdata[(tr+1)*FEATURE_W-1 : tr*FEATURE_W]
                 = {weights_p[tr], weights_q[tr]};
        end
    endgenerate

    // ── Feature extraction wires (genvar for iverilog compatibility) ──
    wire signed [WIDTH-1:0] feat_p [0:NUM_FEATURES-1];
    wire signed [WIDTH-1:0] feat_q [0:NUM_FEATURES-1];
    wire [WIDTH-1:0]        feat_w [0:NUM_FEATURES-1];
    wire signed [WIDTH-1:0] train_p [0:NUM_FEATURES-1];
    wire signed [WIDTH-1:0] train_q [0:NUM_FEATURES-1];

    genvar fx;
    generate
        for (fx = 0; fx < NUM_FEATURES; fx = fx + 1) begin : feat_extract
            assign feat_p[fx] = features[(fx+1)*FEATURE_W-1 : fx*FEATURE_W + WIDTH];
            assign feat_q[fx] = features[fx*FEATURE_W + WIDTH - 1 : fx*FEATURE_W];
            assign feat_w[fx] = feat_weights[fx*WIDTH +: WIDTH];
            assign train_p[fx] = train_features[(fx+1)*FEATURE_W-1 : fx*FEATURE_W + WIDTH];
            assign train_q[fx] = train_features[fx*FEATURE_W + WIDTH - 1 : fx*FEATURE_W];
        end
    endgenerate

    // ── Pipeline stages ────────────────────────────────────────────
    // Stage 0: feature difference (x − w) for all features in parallel
    reg signed [WIDTH-1:0] s0_diff_p [0:NUM_FEATURES-1];
    reg signed [WIDTH-1:0] s0_diff_q [0:NUM_FEATURES-1];
    reg [WIDTH-1:0]        s0_fw     [0:NUM_FEATURES-1];
    reg                    s0_valid;

    // Stage 1: per-feature quadrance = weighted · (diff_p² + 3·diff_q², 2·diff_p·diff_q)
    reg signed [4*WIDTH-1:0] s1_q_p [0:NUM_FEATURES-1];
    reg signed [4*WIDTH-1:0] s1_q_q [0:NUM_FEATURES-1];
    reg                       s1_valid;

    // Stage 2: accumulate across features
    reg signed [63:0] s2_acc_p;
    reg signed [63:0] s2_acc_q;
    reg               s2_valid;

    // Per-feature weighted quadrance (Stage 1.5, combinational)
    wire signed [63:0] s15_wq_p [0:NUM_FEATURES-1];
    wire signed [63:0] s15_wq_q [0:NUM_FEATURES-1];

    genvar fwj;
    generate
        for (fwj = 0; fwj < NUM_FEATURES; fwj = fwj + 1) begin : wq_gen
            assign s15_wq_p[fwj] = s1_valid ? (s1_q_p[fwj] * $signed({1'b0, s0_fw[fwj]})) : 64'sd0;
            assign s15_wq_q[fwj] = s1_valid ? (s1_q_q[fwj] * $signed({1'b0, s0_fw[fwj]})) : 64'sd0;
        end
    endgenerate

    integer fi;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_valid <= 1'b0;
            s1_valid <= 1'b0;
            s2_valid <= 1'b0;
            done     <= 1'b0;
            for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                s0_diff_p[fi] <= 0;
                s0_diff_q[fi] <= 0;
                s0_fw[fi]     <= 0;
                s1_q_p[fi]    <= 0;
                s1_q_q[fi]    <= 0;
            end
            s2_acc_p <= 0;
            s2_acc_q <= 0;
        end else begin
            done <= 1'b0;

            // ── Stage 0: latch inputs, compute differences ─────────
            if (start) begin
                for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                    s0_diff_p[fi] <= feat_p[fi] - weights_p[fi];
                    s0_diff_q[fi] <= feat_q[fi] - weights_q[fi];
                    s0_fw[fi]     <= feat_w[fi];
                end
                s0_valid <= 1'b1;
            end else begin
                s0_valid <= 1'b0;
            end

            // ── Stage 1: compute per-feature quadrance ─────────────
            // quadrance_i = w_i · (diff_p² + 3·diff_q², 2·diff_p·diff_q)
            if (s0_valid) begin
                for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                    // Rational surd quadrance: (p² + 3q², 2pq)
                    s1_q_p[fi] <= (s0_diff_p[fi] * s0_diff_p[fi])
                                + 3 * (s0_diff_q[fi] * s0_diff_q[fi]);
                    s1_q_q[fi] <= 2 * (s0_diff_p[fi] * s0_diff_q[fi]);
                end
                s1_valid <= 1'b1;
            end else begin
                s1_valid <= 1'b0;
            end

            // ── Stage 2: accumulate weighted sum ───────────────────
            if (s1_valid) begin
                s2_acc_p <= s15_wq_p[0] + s15_wq_p[1] + s15_wq_p[2] + s15_wq_p[3];
                s2_acc_q <= s15_wq_q[0] + s15_wq_q[1] + s15_wq_q[2] + s15_wq_q[3];
                s2_valid <= 1'b1;
            end else begin
                s2_valid <= 1'b0;
            end

            // ── Output latch ───────────────────────────────────────
            if (s2_valid) begin
                quadrance <= {s2_acc_p[31:0], s2_acc_q[31:0]};
                done      <= 1'b1;
            end
        end
    end

    assign busy = s0_valid || s1_valid || s2_valid;

    // ── Training update (combinational address, synchronous write) ─
    integer tf;
    reg signed [35:0] train_diff_p, train_diff_q;
    reg signed [35:0] train_prod_p, train_prod_q;
    always @(posedge clk) begin
        if (train_we) begin
            for (tf = 0; tf < NUM_FEATURES; tf = tf + 1) begin
                // Widen to 36-bit before multiply to prevent truncation (18b×18b→36b)
                train_diff_p = $signed({18'd0, train_p[tf]}) - $signed({18'd0, weights_p[tf]});
                train_diff_q = $signed({18'd0, train_q[tf]}) - $signed({18'd0, weights_q[tf]});
                train_prod_p = train_diff_p * $signed({18'd0, train_alpha_h});
                train_prod_q = train_diff_q * $signed({18'd0, train_alpha_h});
                weights_p[tf] <= weights_p[tf] + train_prod_p[35:18];  // >>> WIDTH equivalent
                weights_q[tf] <= weights_q[tf] + train_prod_q[35:18];
            end
        end
    end

endmodule
