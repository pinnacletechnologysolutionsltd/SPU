// SPU-13 SOM Best-Matching-Unit Controller (v1.0)
//
// Serially scans MAX_NODES nodes, computing weighted quadrance for each via
// spu_quadrance_accum.  Tracks best and second-best with stable tie-breaking
// (lower node_id wins ties).  The node ROM stores the seven-node fixture;
// features and feature_weights are external inputs.
//
// Parameters:
//   NUM_FEATURES = 4    feature dimensions
//   MAX_NODES    = 7    nodes in the SOM map
//   WIDTH        = 32   surd coefficient width

module spu_som_bmu #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 7,
    parameter WIDTH        = 32
)(
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  start,
    output reg                   done,

    // Feature vector (flat, NUM_FEATURES surds)
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] features,

    // Feature weight vector (same packing)
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] feature_weights,

    // --- BMU outputs ---
    output reg                   bmu_valid,
    output reg  [15:0]           best_node_id,
    output reg  [15:0]           second_node_id,
    output reg  [15:0]           cluster_label,
    output reg  [2*WIDTH-1:0]    best_q,
    output reg  [2*WIDTH-1:0]    second_q,
    output reg  [2*WIDTH-1:0]    confidence_gap,
    output reg                   has_second
);

    localparam SURD_W = 2 * WIDTH;

    // --- Node ROM: seven-node fixture (matches tiny_hex_fixture) ---
    // Format: {valid, cluster_label, axial_q, axial_r, node_id,
    //          w0_b,w0_a, w1_b,w1_a, w2_b,w2_a, w3_b,w3_a}
    // Node 0: (0,0) label=0   weights=(0, 0, 0, 0)
    // Node 1: (1,0) label=1   weights=(2, 0, 0, 0)
    // Node 2: (1,-1) label=1  weights=(0, 2, 0, 0)
    // Node 3: (0,-1) label=2  weights=(0, 0, 2, 0)
    // Node 4: (-1,0) label=2  weights=(-2, 0, 0, 0)
    // Node 5: (-1,1) label=3  weights=(0, -2, 0, 0)
    // Node 6: (0,1) label=3   weights=(0, 0, -2, 1+1√3)

    wire [0:MAX_NODES-1] node_valid;
    wire [15:0] node_id    [0:MAX_NODES-1];
    wire [15:0] node_label [0:MAX_NODES-1];
    wire [(2*WIDTH*NUM_FEATURES)-1:0] node_w [0:MAX_NODES-1];

    assign node_valid[0] = 1;  assign node_id[0] = 0;  assign node_label[0] = 0;
    assign node_w[0] = { {WIDTH{1'b0}}, {WIDTH{1'b0}},      // w3
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},      // w2
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},      // w1
                         {WIDTH{1'b0}}, {WIDTH{1'b0}} };    // w0

    assign node_valid[1] = 1;  assign node_id[1] = 1;  assign node_label[1] = 1;
    assign node_w[1] = { {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {32'd2} };

    assign node_valid[2] = 1;  assign node_id[2] = 2;  assign node_label[2] = 1;
    assign node_w[2] = { {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {32'd2},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}} };

    assign node_valid[3] = 1;  assign node_id[3] = 3;  assign node_label[3] = 2;
    assign node_w[3] = { {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {32'd2},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}} };

    assign node_valid[4] = 1;  assign node_id[4] = 4;  assign node_label[4] = 2;
    assign node_w[4] = { {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {32'hFFFFFFFE} };  // -2

    assign node_valid[5] = 1;  assign node_id[5] = 5;  assign node_label[5] = 3;
    assign node_w[5] = { {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {WIDTH{1'b0}},
                         {WIDTH{1'b0}}, {32'hFFFFFFFE},     // -2
                         {WIDTH{1'b0}}, {WIDTH{1'b0}} };

    assign node_valid[6] = 1;  assign node_id[6] = 6;  assign node_label[6] = 3;
    assign node_w[6] = { {32'd1}, {32'd1},                  // w3: 1+1√3 → b=1,a=1
                          {WIDTH{1'b0}}, {32'hFFFFFFFE},     // w2: -2
                          {WIDTH{1'b0}}, {WIDTH{1'b0}},
                          {WIDTH{1'b0}}, {WIDTH{1'b0}} };

    // --- Controller FSM ---
    reg [3:0] state;
    localparam S_IDLE      = 0;
    localparam S_START_ACC = 1;   // start quadrance_accum for current node
    localparam S_WAIT_ACC  = 2;   // wait for quadrance_accum to finish
    localparam S_EVAL      = 3;   // compare q_node vs best/second
    localparam S_NEXT_NODE = 4;   // advance to next node or DONE
    localparam S_DONE      = 5;

    reg [$clog2(MAX_NODES)-1:0] node_idx;

    // --- quadrance_accum interface ---
    reg  qa_start;
    wire qa_done;
    wire [SURD_W-1:0] qa_q;

    spu_quadrance_accum #(.NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)) u_qa (
        .clk(clk), .rst_n(rst_n),
        .start(qa_start), .done(qa_done),
        .features(features),
        .node_weights(node_w[node_idx]),
        .feature_weights(feature_weights),
        .q_node(qa_q)
    );

    // --- Best/second tracking registers ---
    reg                   have_best, have_second_int;
    reg [15:0]            best_id,   second_id_int;
    reg [15:0]            best_label_int;
    reg signed [WIDTH-1:0] best_q_a,  best_q_b;
    reg signed [WIDTH-1:0] second_q_a, second_q_b;

    // --- Comparison helper: returns 1 if candidate is better than reference ---
    // Tie-break by lower node_id.
    function cand_better;
        input signed [2*WIDTH-1:0] ca, cb;  // candidate rational and surd parts
        input [15:0]               cid;
        input signed [2*WIDTH-1:0] ra, rb;  // reference rational and surd parts
        input [15:0]               rid;
        input                      has_ref;
        reg   signed [63:0]        da, db;
        begin
            if (!has_ref)
                cand_better = 1;
            else begin
                // Compare using integer-only Q(√3) ordering:
                //   a+b√3 < c+d√3  via sign analysis
                da = ca - ra;
                db = cb - rb;
                if (da == 0 && db == 0)
                    cand_better = (cid < rid);  // tie → lower id wins
                else if (da <= 0 && db <= 0)
                    cand_better = 1;  // cand ≤ ref in both components
                else if (da >= 0 && db >= 0)
                    cand_better = 0;  // cand ≥ ref in both components
                else if (da < 0 && db > 0)
                    cand_better = (da*da > 3*db*db);  // a<0, b>0: cand < ref iff a² > 3b²
                else
                    cand_better = (da*da < 3*db*db);  // a>0, b<0: cand < ref iff a² < 3b²
            end
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state           <= S_IDLE;
            done            <= 0;
            bmu_valid       <= 0;
            best_node_id    <= 0;
            second_node_id  <= 0;
            cluster_label   <= 0;
            best_q          <= 0;
            second_q        <= 0;
            confidence_gap  <= 0;
            has_second      <= 0;
            node_idx        <= 0;
            qa_start        <= 0;
            have_best       <= 0;
            have_second_int <= 0;
            best_id         <= 0;
            second_id_int   <= 0;
            best_label_int  <= 0;
            best_q_a        <= 0;
            best_q_b        <= 0;
            second_q_a      <= 0;
            second_q_b      <= 0;
        end else begin
            done     <= 0;
            qa_start <= 0;

            case (state)
                S_IDLE: begin
                    if (start) begin
                        node_idx        <= 0;
                        have_best       <= 0;
                        have_second_int <= 0;
                        bmu_valid       <= 0;
                        state           <= S_START_ACC;
                    end
                end

                S_START_ACC: begin
                    if (node_valid[node_idx]) begin
                        qa_start <= 1;
                        state    <= S_WAIT_ACC;
                    end else begin
                        // Skip invalid nodes
                        state <= S_NEXT_NODE;
                    end
                end

                S_WAIT_ACC: begin
                    if (qa_done) begin
                        state <= S_EVAL;
                    end
                end

                S_EVAL: begin
                    // Compare qa_q against best/second
                    if (cand_better(qa_q[WIDTH-1:0], qa_q[SURD_W-1:WIDTH],
                                    node_id[node_idx],
                                    best_q_a, best_q_b, best_id, have_best)) begin
                        // New best → demote current best to second
                        if (have_best) begin
                            second_id_int   <= best_id;
                            second_q_a      <= best_q_a;
                            second_q_b      <= best_q_b;
                            have_second_int <= 1;
                        end
                        best_id        <= node_id[node_idx];
                        best_q_a       <= qa_q[WIDTH-1:0];
                        best_q_b       <= qa_q[SURD_W-1:WIDTH];
                        best_label_int <= node_label[node_idx];
                        have_best      <= 1;
                    end else if (cand_better(qa_q[WIDTH-1:0], qa_q[SURD_W-1:WIDTH],
                                            node_id[node_idx],
                                            second_q_a, second_q_b, second_id_int,
                                            have_second_int)) begin
                        second_id_int   <= node_id[node_idx];
                        second_q_a      <= qa_q[WIDTH-1:0];
                        second_q_b      <= qa_q[SURD_W-1:WIDTH];
                        have_second_int <= 1;
                    end
                    state <= S_NEXT_NODE;
                end

                S_NEXT_NODE: begin
                    if (node_idx == MAX_NODES - 1) begin
                        state <= S_DONE;
                    end else begin
                        node_idx <= node_idx + 1;
                        state    <= S_START_ACC;
                    end
                end

                S_DONE: begin
                    bmu_valid       <= have_best;
                    best_node_id    <= best_id;
                    second_node_id  <= have_second_int ? second_id_int : 16'hFFFF;
                    cluster_label   <= best_label_int;
                    best_q          <= {best_q_b, best_q_a};
                    second_q        <= {second_q_b, second_q_a};
                    has_second      <= have_second_int;
                    // confidence_gap = second_q - best_q (only if has_second)
                    if (have_second_int) begin
                        confidence_gap <= {second_q_b - best_q_b,
                                           second_q_a - best_q_a};
                    end else begin
                        confidence_gap <= 0;
                    end
                    done  <= 1;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
