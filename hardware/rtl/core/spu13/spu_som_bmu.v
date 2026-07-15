`timescale 1ns / 1ps

// spu_som_bmu.v — Weighted quadrance BMU (Best Matching Unit) classifier
// Interface matched to spu13_core.v gen_som instantiation.
//
// Architecture:
//   BRAM-backed node weight storage with sequential scan FSM.
//   On start, reads node weights from BRAM (1-cycle latency, read-ahead pipelined),
//   computes quadrance between input feature vector and each node,
//   tracks best + second-best match, outputs BMU result.
//   Training port allows external weight updates (SOM_TRAIN opcode).
//
// The BRAM is initialised from .mem files at bitstream time.  To change
// node weights without re-synthesising, write to the training port.

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
    input  wire [$clog2(MAX_NODES)-1 : 0] train_addr,
    input  wire [3:0]   train_be,      // byte-enable: one bit per feature
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_wdata,
    output wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] train_rdata
);

    // ── Internal constants ────────────────────────────────────────────
    localparam FEATURE_W = 2 * WIDTH;               // bits per feature
    localparam NODE_W    = NUM_FEATURES * FEATURE_W; // bits per node
    localparam ADDR_W    = $clog2(MAX_NODES);

    // ── BRAM read address (declared before instantiation) ─────────────
    reg [ADDR_W-1 : 0] bram_rd_addr;

    // ── BRAM-backed node weight storage ───────────────────────────────
    // Initialised from hardware/rtl/core/spu13/som_weights_f{0..3}.mem
    wire [NODE_W - 1 : 0] bram_rd_data;

    spu_som_weight_bram #(
        .MAX_NODES(MAX_NODES),
        .WIDTH(WIDTH)
    ) u_weight_bram (
        .clk(clk),
        .rd_addr(bram_rd_addr),
        .rd_data(bram_rd_data),
        .wr_en(train_we),
        .wr_addr(train_addr),
        .wr_be(train_be),
        .wr_data(train_wdata)
    );

    // Training readback uses the normal BRAM read port while the scanner is idle.
    assign train_rdata = bram_rd_data;

    // ── Scan FSM ──────────────────────────────────────────────────────
    localparam SCAN_IDLE       = 4'd0;
    localparam SCAN_PRIME      = 4'd1;
    localparam SCAN_COMPUTE    = 4'd2;
    localparam SCAN_CMP_BEST   = 4'd3;
    localparam SCAN_WAIT_BEST  = 4'd4;
    localparam SCAN_CMP_SECOND = 4'd5;
    localparam SCAN_WAIT_SECOND= 4'd6;
    localparam SCAN_ADVANCE    = 4'd7;
    localparam SCAN_DONE       = 4'd8;

    reg [3:0]  scan_state;
    reg [ADDR_W-1 : 0] scan_node;       // Current node being evaluated

    // Pipeline registers for quadrance computation
    reg [FEATURE_W-1:0] f_reg  [0:NUM_FEATURES-1];
    reg [FEATURE_W-1:0] fw_reg [0:NUM_FEATURES-1];
    reg [FEATURE_W-1:0] w_reg  [0:NUM_FEATURES-1];
    reg [4*WIDTH-1:0]   q_reg  [0:NUM_FEATURES-1];  // Per-feature quadrance
    reg [31:0]           q_accum_p;
    reg signed [31:0]    q_accum_q;
    reg [1:0]            pipe_stage;

    reg [31:0] scan_best_dist;  // Best quadrance (P component, lower = closer)
    reg [31:0] scan_sec_dist;   // Second-best quadrance
    reg [15:0] scan_best_id;
    reg [15:0] scan_sec_id;
    reg [15:0] scan_best_label;
    reg [15:0] scan_sec_label;
    reg [63:0] scan_best_q_reg;
    reg [63:0] scan_sec_q_reg;
    reg [63:0] scan_cand_q;
    reg [15:0] scan_cand_id;
    reg [15:0] scan_cand_label;
    reg        scan_cand_lt_best;
    reg        scan_have_best;
    reg        scan_has_sec;

    // Exact Q(sqrt(3)) ordering is deliberately bit-serial. A combinational
    // implementation inferred two wide squares and overwhelmed the Tang 25K;
    // the serial comparator spends at most 35 clocks and uses two shift-add
    // accumulators instead.
    wire cmp_start = (scan_state == SCAN_CMP_BEST) ||
                     (scan_state == SCAN_CMP_SECOND);
    wire [63:0] cmp_rhs = (scan_state == SCAN_CMP_SECOND)
                        ? scan_sec_q_reg : scan_best_q_reg;
    wire cmp_done;
    wire cmp_lt;

    spu_surd_lt_serial u_surd_lt (
        .clk(clk), .rst_n(rst_n), .start(cmp_start),
        .lhs(scan_cand_q), .rhs(cmp_rhs),
        .done(cmp_done), .lt(cmp_lt)
    );

    // ── Quadrance computation datapath ────────────────────────────────
    function [4*WIDTH-1:0] rs_weighted_quadrance;
        input signed [WIDTH-1:0] dp, dq;
        input signed [WIDTH-1:0] wp, wq;
        reg signed [2*WIDTH-1:0] dp_sq, dq_sq, pq;
        reg signed [2*WIDTH-1:0] sq_p, sq_q;
        reg signed [2*WIDTH-1:0] w_p, w_q;
        begin
            dp_sq = dp * dp;
            dq_sq = dq * dq;
            pq    = dp * dq;
            sq_p = dp_sq + (dq_sq <<< 1) + dq_sq;
            sq_q = pq <<< 1;
            w_p = (sq_p * wp) + (((sq_q * wq) <<< 1) + (sq_q * wq));
            w_q = (sq_p * wq) + (sq_q * wp);
            rs_weighted_quadrance = {w_p, w_q};
        end
    endfunction

    // ── Node labels (LUT, stays in distributed RAM) ───────────────────
    reg [15:0] node_label [0:MAX_NODES-1];
    integer nl;
    initial begin
        for (nl = 0; nl < MAX_NODES; nl = nl + 1)
            node_label[nl] = 16'd0;
        node_label[0] = 16'd0;
        node_label[1] = 16'd1;
        node_label[2] = 16'd1;
        node_label[3] = 16'd2;
        node_label[4] = 16'd2;
        node_label[5] = 16'd3;
        node_label[6] = 16'd3;
    end

    // Helper: extract one feature from bram_rd_data
    function [FEATURE_W-1:0] bram_feat;
        input [NODE_W-1:0] data;
        input [2:0]        idx;
        begin
            case (idx)
                3'd0: bram_feat = data[0*FEATURE_W +: FEATURE_W];
                3'd1: bram_feat = data[1*FEATURE_W +: FEATURE_W];
                3'd2: bram_feat = data[2*FEATURE_W +: FEATURE_W];
                3'd3: bram_feat = data[3*FEATURE_W +: FEATURE_W];
                default: bram_feat = {FEATURE_W{1'b0}};
            endcase
        end
    endfunction

    integer fi;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scan_state     <= SCAN_IDLE;
            done           <= 0;
            bmu_valid      <= 0;
            scan_node      <= 0;
            bram_rd_addr   <= 0;
            scan_best_dist <= 32'h7FFFFFFF;
            scan_sec_dist  <= 32'h7FFFFFFF;
            scan_best_id   <= 0;
            scan_sec_id    <= 0;
            scan_cand_q    <= 0;
            scan_cand_id   <= 0;
            scan_cand_label <= 0;
            scan_cand_lt_best <= 0;
            scan_have_best <= 0;
            scan_has_sec   <= 0;
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
                    bram_rd_addr <= train_addr;
                    if (start) begin
                        scan_node      <= 0;
                        bram_rd_addr   <= 0;
                        scan_best_dist <= 32'h7FFFFFFF;
                        scan_sec_dist  <= 32'h7FFFFFFF;
                        scan_best_id   <= 0;
                        scan_sec_id    <= 0;
                        scan_have_best <= 0;
                        scan_has_sec   <= 0;
                        pipe_stage     <= 0;
                        q_accum_p      <= 0;
                        q_accum_q      <= 0;
                        scan_state     <= SCAN_PRIME;

                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            f_reg[fi]  <= features[fi*FEATURE_W +: FEATURE_W];
                            fw_reg[fi] <= feature_weights[fi*FEATURE_W +: FEATURE_W];
                        end
                    end
                end

                SCAN_PRIME: begin
                    // BRAM read address is registered.  After idle readback may
                    // point at train_addr, so give rd_addr=0 one full cycle to
                    // propagate before latching node 0 weights.
                    pipe_stage <= 0;
                    scan_state <= SCAN_COMPUTE;
                end

                SCAN_COMPUTE: begin
                    // Pipeline with BRAM read-ahead:
                    //   pipe 0: latch BRAM output into w_reg
                    //   pipe 1: compute per-feature quadrance
                    //   pipe 2: accumulate across features, issue BRAM read-ahead
                    //   pipe 3: latch candidate; exact comparison is serial
                    //
                    // BRAM has 1-cycle registered read latency.  Read-ahead is
                    // issued in pipe 2 (bram_rd_addr <= scan_node+1).  The BRAM
                    // registers this address at the posedge entering pipe 3.
                    // By pipe 0 of the next node, bram_rd_data is stable.

                    if (pipe_stage == 0) begin
                        // Latch BRAM output into w_reg (all features in parallel)
                        w_reg[0] <= bram_feat(bram_rd_data, 0);
                        w_reg[1] <= bram_feat(bram_rd_data, 1);
                        w_reg[2] <= bram_feat(bram_rd_data, 2);
                        w_reg[3] <= bram_feat(bram_rd_data, 3);
                        pipe_stage <= 1;
                    end
                    else if (pipe_stage == 1) begin
                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            q_reg[fi] <= rs_weighted_quadrance(
                                f_reg[fi][WIDTH-1:0]
                                    - w_reg[fi][WIDTH-1:0],
                                f_reg[fi][2*WIDTH-1:WIDTH]
                                    - w_reg[fi][2*WIDTH-1:WIDTH],
                                fw_reg[fi][WIDTH-1:0],
                                fw_reg[fi][2*WIDTH-1:WIDTH]
                            );
                        end
                        pipe_stage <= 2;
                    end
                    else if (pipe_stage == 2) begin
                        q_accum_p = 32'd0;
                        q_accum_q = 32'sd0;
                        for (fi = 0; fi < NUM_FEATURES; fi = fi + 1) begin
                            q_accum_p = q_accum_p
                                + q_reg[fi][4*WIDTH-1:2*WIDTH];
                            q_accum_q = q_accum_q
                                + $signed(q_reg[fi][2*WIDTH-1:0]);
                        end
                        // Read-ahead: start BRAM read for next node
                        // (rd_addr_r latches this at the posedge entering pipe 3)
                        if (scan_node < MAX_NODES - 1)
                            bram_rd_addr <= scan_node + 1;
                        pipe_stage <= 3;
                    end
                    else begin
                        scan_cand_q <= {q_accum_p, q_accum_q[31:0]};
                        scan_cand_id <= {{(16-ADDR_W){1'b0}}, scan_node};
                        scan_cand_label <= node_label[scan_node];
                        if (!scan_have_best) begin
                            scan_best_dist  <= q_accum_p;
                            scan_best_id    <= {{(16-ADDR_W){1'b0}}, scan_node};
                            scan_best_label <= node_label[scan_node];
                            scan_best_q_reg <= {q_accum_p, q_accum_q[31:0]};
                            scan_have_best  <= 1'b1;
                            scan_state <= SCAN_ADVANCE;
                        end else
                            scan_state <= SCAN_CMP_BEST;
                    end
                end

                SCAN_CMP_BEST:
                    scan_state <= SCAN_WAIT_BEST;

                SCAN_WAIT_BEST: begin
                    if (cmp_done) begin
                        if (!scan_has_sec) begin
                            if (cmp_lt) begin
                                scan_sec_dist   <= scan_best_dist;
                                scan_sec_id     <= scan_best_id;
                                scan_sec_label  <= scan_best_label;
                                scan_sec_q_reg  <= scan_best_q_reg;
                                scan_best_dist  <= scan_cand_q[63:32];
                                scan_best_id    <= scan_cand_id;
                                scan_best_label <= scan_cand_label;
                                scan_best_q_reg <= scan_cand_q;
                            end else begin
                                scan_sec_dist  <= scan_cand_q[63:32];
                                scan_sec_id    <= scan_cand_id;
                                scan_sec_label <= scan_cand_label;
                                scan_sec_q_reg <= scan_cand_q;
                            end
                            scan_has_sec <= 1'b1;
                            scan_state     <= SCAN_ADVANCE;
                        end else begin
                            // Always perform the runner-up comparison once a
                            // second candidate exists, even when this candidate
                            // already beat the winner. This keeps node latency
                            // independent of the data.
                            scan_cand_lt_best <= cmp_lt;
                            scan_state <= SCAN_CMP_SECOND;
                        end
                    end
                end

                SCAN_CMP_SECOND:
                    scan_state <= SCAN_WAIT_SECOND;

                SCAN_WAIT_SECOND: begin
                    if (cmp_done) begin
                        if (scan_cand_lt_best) begin
                            scan_sec_dist   <= scan_best_dist;
                            scan_sec_id     <= scan_best_id;
                            scan_sec_label  <= scan_best_label;
                            scan_sec_q_reg  <= scan_best_q_reg;
                            scan_best_dist  <= scan_cand_q[63:32];
                            scan_best_id    <= scan_cand_id;
                            scan_best_label <= scan_cand_label;
                            scan_best_q_reg <= scan_cand_q;
                        end else if (cmp_lt) begin
                            scan_sec_dist  <= scan_cand_q[63:32];
                            scan_sec_id    <= scan_cand_id;
                            scan_sec_label <= scan_cand_label;
                            scan_sec_q_reg <= scan_cand_q;
                        end
                        scan_state <= SCAN_ADVANCE;
                    end
                end

                SCAN_ADVANCE: begin
                    if (scan_node == MAX_NODES - 1)
                        scan_state <= SCAN_DONE;
                    else begin
                        scan_node  <= scan_node + 1'b1;
                        pipe_stage <= 0;
                        scan_state <= SCAN_COMPUTE;
                    end
                end

                SCAN_DONE: begin
                    done      <= 1;
                    bmu_valid <= 1;
                    bram_rd_addr <= 0;

                    best_node_id  <= scan_best_id;
                    second_node_id <= scan_sec_id;
                    cluster_label <= scan_best_label;
                    best_q        <= scan_best_q_reg;
                    second_q      <= scan_sec_q_reg;
                    confidence_gap <= {scan_sec_dist - scan_best_dist,
                                       scan_sec_q_reg[31:0]
                                       - scan_best_q_reg[31:0]};
                    has_second    <= scan_has_sec;
                    scan_state    <= SCAN_IDLE;
                end
            endcase
        end
    end

endmodule

// Exact less-than comparator for non-negative Q(sqrt(3)) distances encoded as
// {P[31:0], Q[31:0]}. For mixed-sign component differences it evaluates
// |a|^2 versus 3|b|^2 with 33 shift-add steps instead of inferred multipliers.
module spu_surd_lt_serial (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [63:0] lhs,
    input  wire [63:0] rhs,
    output reg         done,
    output reg         lt
);
    localparam C_IDLE = 2'd0;
    localparam C_RUN  = 2'd1;
    localparam C_DECIDE = 2'd2;

    reg [1:0] state;
    reg [5:0] bit_idx;
    reg [32:0] abs_a, abs_b;
    reg [65:0] sq_a, sq_b;
    reg mixed_a_negative;
    reg direct_case;
    reg direct_lt;

    wire signed [32:0] da = $signed({1'b0, lhs[63:32]})
                                  - $signed({1'b0, rhs[63:32]});
    wire signed [32:0] db = $signed({lhs[31], lhs[31:0]})
                                  - $signed({rhs[31], rhs[31:0]});
    wire [65:0] add_a = abs_a[bit_idx]
                       ? ({33'd0, abs_a} << bit_idx) : 66'd0;
    wire [65:0] add_b = abs_b[bit_idx]
                       ? ({33'd0, abs_b} << bit_idx) : 66'd0;
    wire [65:0] three_sq_b = sq_b + (sq_b << 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= C_IDLE;
            done <= 1'b0;
            lt <= 1'b0;
            bit_idx <= 0;
            abs_a <= 0;
            abs_b <= 0;
            sq_a <= 0;
            sq_b <= 0;
            mixed_a_negative <= 1'b0;
            direct_case <= 1'b0;
            direct_lt <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                C_IDLE: if (start) begin
                    direct_case <= (da == 0 && db == 0) ||
                                   (da <= 0 && db <= 0) ||
                                   (da >= 0 && db >= 0);
                    direct_lt <= !(da == 0 && db == 0) &&
                                 (da <= 0 && db <= 0);
                    abs_a <= da < 0 ? -da : da;
                    abs_b <= db < 0 ? -db : db;
                    mixed_a_negative <= da < 0;
                    sq_a <= 0;
                    sq_b <= 0;
                    bit_idx <= 0;
                    state <= C_RUN;
                end

                C_RUN: begin
                    sq_a <= sq_a + add_a;
                    sq_b <= sq_b + add_b;
                    if (bit_idx == 6'd32)
                        state <= C_DECIDE;
                    else
                        bit_idx <= bit_idx + 1'b1;
                end

                C_DECIDE: begin
                    lt <= direct_case ? direct_lt :
                          (mixed_a_negative ? (sq_a > three_sq_b)
                                            : (sq_a < three_sq_b));
                    done <= 1'b1;
                    state <= C_IDLE;
                end

                default: state <= C_IDLE;
            endcase
        end
    end
endmodule
