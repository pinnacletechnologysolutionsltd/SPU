`timescale 1ns / 1ps

// spu_som_bmu.v — Weighted quadrance BMU (Best Matching Unit) classifier
// Interface matched to spu13_core.v gen_som instantiation.
//
// Architecture:
//   7 nodes, each storing 4 rational-surd feature weights (WIDTH-bit coeffs).
//   On start, computes quadrance between input feature vector and each node,
//   tracks best + second-best match, outputs BMU result.
//   Training port allows external weight updates (SOM_TRAIN opcode).

module spu_som_bmu #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 7,
    parameter WIDTH        = 18
) (
    input  wire         clk,
    input  wire         rst_n,

    // Control
    input  wire         start,
    output reg          done,

    // Feature vector: packed {F3, F2, F1, F0}, each 2*WIDTH bits (P,Q)
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] features,
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] feature_weights,

    // BMU results
    output reg          bmu_valid,
    output reg  [15:0]  best_node_id,
    output reg  [15:0]  second_node_id,
    output reg  [15:0]  cluster_label,
    output reg  [63:0]  best_q,
    output reg  [63:0]  second_q,
    output reg  [63:0]  confidence_gap,
    output reg          has_second,

    // Axiomatic gatekeeper
    input  wire [1:0]   axiomatic_level,
    output reg          axiomatic_fault,
    output reg  [3:0]   fault_type,
    output reg  [31:0]  fault_count,

    // Training port (SOM_TRAIN: update node weights)
    input  wire         train_we,
    input  wire [2:0]   train_addr,
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_wdata,
    output wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_rdata
);

    // ── Internal constants ────────────────────────────────────────────
    localparam FEATURE_W = 2 * WIDTH;               // bits per feature
    localparam NODE_W    = NUM_FEATURES * FEATURE_W; // bits per node
    localparam NODE_BITS = MAX_NODES * NODE_W;       // total node storage

    function [FEATURE_W-1:0] rs_pack;
        input signed [WIDTH-1:0] p;
        input signed [WIDTH-1:0] q;
        begin
            rs_pack = {q, p};
        end
    endfunction

    // ── Node weight BRAM (7 nodes × 4 features each) ──────────────────
    reg [FEATURE_W-1:0] node_weights [0:MAX_NODES-1][0:NUM_FEATURES-1];

    // Training read: pack requested node's weights
    genvar nf;
    wire [NODE_W-1:0] node_rdata_packed;
    generate
        for (nf = 0; nf < NUM_FEATURES; nf = nf + 1) begin : rd_pack
            assign node_rdata_packed[(nf+1)*FEATURE_W-1 : nf*FEATURE_W]
                 = node_weights[train_addr][NUM_FEATURES-1-nf];
        end
    endgenerate
    assign train_rdata = node_rdata_packed;

    // Training write (combinational)
    integer tf;
    always @(posedge clk) begin
        if (train_we) begin
            for (tf = 0; tf < NUM_FEATURES; tf = tf + 1) begin
                node_weights[train_addr][NUM_FEATURES-1-tf]
                    <= train_wdata[tf*FEATURE_W +: FEATURE_W];
            end
        end
    end

    // ── Seed node weights from cluster_labels on first scan ─────────
    reg [31:0] seed_counter = 0;
    wire seeding = (seed_counter < 32'h7FFFFFFF);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) seed_counter <= 0;
        else if (seed_counter != 32'h7FFFFFFF) seed_counter <= seed_counter + 1;
    end

    // Initial node labels: 7 nodes, labels 0-3 cyclically
    reg [15:0] node_label [0:MAX_NODES-1];
    integer nl, nwf;
    initial begin
        for (nl = 0; nl < MAX_NODES; nl = nl + 1) begin
            node_label[nl] = 16'd0;
            for (nwf = 0; nwf < NUM_FEATURES; nwf = nwf + 1)
                node_weights[nl][nwf] = {FEATURE_W{1'b0}};
        end

        // Seven-node fixture shared with software/lib/rational_som.py.
        node_label[0] = 16'd0;
        node_label[1] = 16'd1;
        node_label[2] = 16'd1;
        node_label[3] = 16'd2;
        node_label[4] = 16'd2;
        node_label[5] = 16'd3;
        node_label[6] = 16'd3;

        node_weights[1][0] = rs_pack(2, 0);
        node_weights[2][1] = rs_pack(2, 0);
        node_weights[3][2] = rs_pack(2, 0);
        node_weights[4][0] = rs_pack(-2, 0);
        node_weights[5][1] = rs_pack(-2, 0);
        node_weights[6][2] = rs_pack(-2, 0);
        node_weights[6][3] = rs_pack(1, 1);
    end

    // ── Quadrance computation datapath ────────────────────────────────
    // Quadrance = sum over features of (feature - weight)^2 in Q(√3)
    // Each feature is {P, Q} in WIDTH-bit signed format.

    function signed [2*WIDTH-1:0] rs_sub;
        input signed [WIDTH-1:0] a_p, a_q;
        input signed [WIDTH-1:0] b_p, b_q;
        begin
            rs_sub = {(a_p - b_p), (a_q - b_q)};
        end
    endfunction

    function [4*WIDTH-1:0] rs_quadrance;
        input signed [WIDTH-1:0] dp, dq;
        reg signed [2*WIDTH-1:0] dp_sq, dq_sq, pq;
        reg signed [2*WIDTH-1:0] qp, qq;
        begin
            dp_sq = dp * dp;
            dq_sq = dq * dq;
            pq    = dp * dq;
            // quadrance = P^2 + 3*Q^2 = (p^2 + 3*q^2, 2*p*q)
            qp = dp_sq + (dq_sq <<< 1) + dq_sq;
            qq = pq <<< 1;
            rs_quadrance = {qp, qq};
        end
    endfunction

    // ── Scan FSM ──────────────────────────────────────────────────────
    localparam SCAN_IDLE    = 3'd0;
    localparam SCAN_COMPUTE = 3'd1;
    localparam SCAN_DONE    = 3'd2;

    reg [2:0]  scan_state;
    reg [2:0]  scan_node;       // Current node being evaluated
    reg [31:0] scan_best_dist;  // Best quadrance (P component, lower = closer)
    reg [31:0] scan_sec_dist;   // Second-best quadrance
    reg [15:0] scan_best_id;
    reg [15:0] scan_sec_id;
    reg [15:0] scan_best_label;
    reg [15:0] scan_sec_label;
    reg [63:0] scan_best_q_reg;
    reg [63:0] scan_sec_q_reg;

    reg        scan_has_sec;

    // Pipeline registers for quadrance computation
    reg [FEATURE_W-1:0] f_reg [0:NUM_FEATURES-1];
    reg [FEATURE_W-1:0] w_reg [0:NUM_FEATURES-1];
    reg [4*WIDTH-1:0]   q_reg [0:NUM_FEATURES-1];  // Per-feature quadrance
    reg [31:0]           q_accum_p;
    reg signed [31:0]    q_accum_q;
    reg [1:0]            pipe_stage;

    integer fi, pi;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scan_state     <= SCAN_IDLE;
            done           <= 0;
            bmu_valid      <= 0;
            scan_node      <= 0;
            scan_best_dist <= 32'h7FFFFFFF;
            scan_sec_dist  <= 32'h7FFFFFFF;
            scan_best_id   <= 0;
            scan_sec_id    <= 0;
            pipe_stage     <= 0;
            q_accum_p      <= 0;
            q_accum_q      <= 0;
            axiomatic_fault <= 0;
            fault_type     <= 0;
            fault_count    <= 0;
        end else begin
            done      <= 0;
            bmu_valid <= 0;

            case (scan_state)
                SCAN_IDLE: begin
                    if (start) begin
                        scan_node      <= 0;
                        scan_best_dist <= 32'h7FFFFFFF;
                        scan_sec_dist  <= 32'h7FFFFFFF;
                        scan_best_id   <= 0;
                        scan_sec_id    <= 0;
                        scan_has_sec   <= 0;
                        pipe_stage     <= 0;
                        q_accum_p      <= 0;
                        q_accum_q      <= 0;
                        scan_state     <= SCAN_COMPUTE;

                        // Latch features into pipeline register
                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            f_reg[fi] <= features[fi*FEATURE_W +: FEATURE_W];
                        end
                    end
                end

                SCAN_COMPUTE: begin
                    // Stage 0: load current node's weights, compute differences
                    if (pipe_stage == 0) begin
                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            w_reg[fi] <= node_weights[scan_node][fi];
                        end
                        pipe_stage <= 1;
                    end
                    // Stage 1-2: compute per-feature quadrances (pipeline)
                    else if (pipe_stage == 1) begin
                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            q_reg[fi] <= rs_quadrance(
                                f_reg[fi][WIDTH-1:0]    - w_reg[fi][WIDTH-1:0],
                                f_reg[fi][2*WIDTH-1:WIDTH] - w_reg[fi][2*WIDTH-1:WIDTH]
                            );
                        end
                        pipe_stage <= 2;
                    end
                    // Stage 2: accumulate quadrances across features
                    else if (pipe_stage == 2) begin
                        q_accum_p = 32'd0;
                        q_accum_q = 32'sd0;
                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            q_accum_p = q_accum_p + q_reg[fi][4*WIDTH-1:2*WIDTH];
                            q_accum_q = q_accum_q + $signed(q_reg[fi][2*WIDTH-1:0]);
                        end
                        pipe_stage <= 3;
                    end
                    // Stage 3: compare with best/second
                    else begin
                        // q_accum holds total quadrance for this node
                        // Lower quadrance = better match
                        if (q_accum_p < scan_best_dist ||
                            (q_accum_p == scan_best_dist && $signed(q_accum_q) < $signed(scan_best_q_reg[31:0]))) begin
                            // Current becomes second, new is best
                            scan_sec_dist   <= scan_best_dist;
                            scan_sec_id     <= scan_best_id;
                            scan_sec_label  <= scan_best_label;
                            scan_sec_q_reg  <= scan_best_q_reg;
                            scan_best_dist  <= q_accum_p;
                            scan_best_id    <= {10'd0, scan_node};
                            scan_best_label <= node_label[scan_node];
                            scan_best_q_reg <= {q_accum_p, q_accum_q[31:0]};
                            scan_has_sec    <= (scan_best_dist != 32'h7FFFFFFF);
                        end else if (q_accum_p < scan_sec_dist ||
                                   (q_accum_p == scan_sec_dist && $signed(q_accum_q) < $signed(scan_sec_q_reg[31:0]))) begin
                            scan_sec_dist  <= q_accum_p;
                            scan_sec_id    <= {10'd0, scan_node};
                            scan_sec_label <= node_label[scan_node];
                            scan_sec_q_reg <= {q_accum_p, q_accum_q[31:0]};
                            scan_has_sec   <= 1;
                        end

                        // Next node or done
                        if (scan_node == MAX_NODES - 1) begin
                            scan_state <= SCAN_DONE;
                        end else begin
                            scan_node   <= scan_node + 1;
                            pipe_stage  <= 0;
                        end
                    end
                end

                SCAN_DONE: begin
                    done      <= 1;
                    bmu_valid <= 1;
                    best_node_id  <= scan_best_id;
                    second_node_id <= scan_sec_id;
                    cluster_label <= scan_best_label;
                    best_q        <= scan_best_q_reg;
                    second_q      <= scan_sec_q_reg;
                    // Confidence gap = second_best - best (always positive since best < second)
                    confidence_gap <= {scan_sec_dist - scan_best_dist, scan_sec_q_reg[31:0] - scan_best_q_reg[31:0]};
                    has_second    <= scan_has_sec;
                    scan_state    <= SCAN_IDLE;
                end
            endcase
        end
    end

endmodule
