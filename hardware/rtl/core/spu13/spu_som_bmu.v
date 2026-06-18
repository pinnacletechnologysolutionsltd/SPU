// spu_som_bmu.v — SOM Best-Matching-Unit Controller (v1.1 BRAM-backed)
//
// Serially scans MAX_NODES nodes, computing weighted quadrance for each.
// Node weights in writable dual-port BRAM — spu_som_train.v updates them.
// Port A: read by BMU scanner. Port B: read/write by training engine.
//
// BRAM read latency adds one cycle to the scan FSM (S_READ_ADDR → S_READ_WAIT).

module spu_som_bmu #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 7,
    parameter WIDTH        = 18
)(
    input  wire        clk, rst_n,
    input  wire        start,
    output reg         done,

    // Feature vector + feature weights (flat surd packing)
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] features,
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] feature_weights,

    // ── BMU outputs ────────────────────────────────────────
    output reg         bmu_valid,
    output reg  [15:0] best_node_id, second_node_id, cluster_label,
    output reg  [2*WIDTH-1:0] best_q, second_q, confidence_gap,
    output reg         has_second,

    // ── Training interface (Port B of weight BRAM) ─────────
    input  wire        train_we,
    input  wire [$clog2(MAX_NODES)-1:0] train_addr,
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] train_wdata,

    // ── Axiomatic Gatekeeper ───────────────────────────────
    input  wire [1:0]  axiomatic_level,
    output wire        axiomatic_fault,
    output wire [1:0]  fault_type,
    output wire [15:0] fault_count
);

    localparam SURD_W = 2 * WIDTH;
    localparam VEC_W  = SURD_W * NUM_FEATURES;
    localparam ADDR_W = $clog2(MAX_NODES);

    // ── Node metadata (hardcoded, does not change with training) ──
    reg [0:MAX_NODES-1] node_valid;
    reg [15:0] node_id    [0:MAX_NODES-1];
    reg [15:0] node_label [0:MAX_NODES-1];

    integer init_n;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (init_n = 0; init_n < MAX_NODES; init_n = init_n + 1) begin
                node_valid[init_n] <= 1;
                node_id[init_n]    <= init_n[15:0];
            end
            node_label[0] <= 0; node_label[1] <= 1; node_label[2] <= 1;
            node_label[3] <= 2; node_label[4] <= 2; node_label[5] <= 3;
            node_label[6] <= 3;
        end
    end

    // ── Weight BRAM (dual-port, writable, with default values) ──
    reg [VEC_W-1:0] weight_mem [0:MAX_NODES-1];

    // Port A: read for BMU scan
    reg  [ADDR_W-1:0] bram_rd_addr;
    wire [VEC_W-1:0]  bram_rd_data;
    assign bram_rd_data = weight_mem[bram_rd_addr];

    // Port B: write for training
    always @(posedge clk)
        if (train_we) weight_mem[train_addr] <= train_wdata;

    // BRAM defaults (same as the original 7-node fixture)
    wire signed [WIDTH-1:0] c0=0, c1=1, c2=2, cn2=-2;
    initial begin
        weight_mem[0] = {c0,c0, c0,c0, c0,c0, c0,c0};
        weight_mem[1] = {c0,c0, c0,c0, c0,c0, c0,c2};
        weight_mem[2] = {c0,c0, c0,c0, c0,c2, c0,c0};
        weight_mem[3] = {c0,c0, c0,c2, c0,c0, c0,c0};
        weight_mem[4] = {c0,c0, c0,c0, c0,c0, c0,cn2};
        weight_mem[5] = {c0,c0, c0,c0, c0,cn2, c0,c0};
        weight_mem[6] = {c1,c1, c0,cn2, c0,c0, c0,c0};
    end

    // ── Registered BRAM output (captured during S_READ_WAIT) ──
    reg [VEC_W-1:0] captured_w;

    // ── FSM (adds S_READ_ADDR + S_READ_WAIT for BRAM latency) ──
    localparam S_IDLE       = 0;
    localparam S_READ_ADDR  = 1;   // present BRAM address
    localparam S_READ_WAIT  = 2;   // capture BRAM output
    localparam S_START_ACC  = 3;   // start quadrance_accum
    localparam S_WAIT_ACC   = 4;   // wait for quadrance
    localparam S_EVAL       = 5;   // compare vs best/second
    localparam S_NEXT_NODE  = 6;   // advance or done
    localparam S_DONE       = 7;

    reg [3:0] state;
    reg [ADDR_W-1:0] node_idx;

    // ── quadrance_accum ──────────────────────────────────────
    reg  qa_start;
    wire qa_done, qa_overflow;
    wire [SURD_W-1:0] qa_q;

    spu_quadrance_accum #(.NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)) u_qa (
        .clk(clk), .rst_n(rst_n), .start(qa_start), .done(qa_done),
        .features(features), .node_weights(captured_w),
        .feature_weights(feature_weights),
        .q_node(qa_q), .accum_overflow(qa_overflow)
    );

    spu13_axiomatic_gatekeeper #(.WIDTH(WIDTH)) u_gatekeeper (
        .clk(clk), .rst_n(rst_n), .axiomatic_level(axiomatic_level),
        .quadrance_a(qa_q[WIDTH-1:0]), .quadrance_b(qa_q[SURD_W-1:WIDTH]),
        .accum_overflow(qa_overflow), .pipeline_valid(qa_done),
        .axiomatic_fault(axiomatic_fault), .fault_type(fault_type),
        .fault_count(fault_count)
    );

    // ── Best/second tracking ─────────────────────────────────
    reg have_best, have_second_int;
    reg [15:0] best_id, second_id_int, best_label_int;
    reg signed [WIDTH-1:0] best_q_a, best_q_b, second_q_a, second_q_b;

    function cand_better;
        input signed [2*WIDTH-1:0] ca, cb;
        input [15:0] cid;
        input signed [2*WIDTH-1:0] ra, rb;
        input [15:0] rid;
        input        has_ref;
        reg signed [63:0] da, db;
        begin
            if (!has_ref) cand_better = 1;
            else begin
                da = ca - ra; db = cb - rb;
                if (da == 0 && db == 0)         cand_better = (cid < rid);
                else if (da <= 0 && db <= 0)    cand_better = 1;
                else if (da >= 0 && db >= 0)    cand_better = 0;
                else if (da < 0 && db > 0)      cand_better = (da*da > 3*db*db);
                else                            cand_better = (da*da < 3*db*db);
            end
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; done <= 0; bmu_valid <= 0;
            best_node_id <= 0; second_node_id <= 0; cluster_label <= 0;
            best_q <= 0; second_q <= 0; confidence_gap <= 0;
            has_second <= 0; node_idx <= 0; qa_start <= 0;
            have_best <= 0; have_second_int <= 0;
            best_id <= 0; second_id_int <= 0; best_label_int <= 0;
            best_q_a <= 0; best_q_b <= 0;
            second_q_a <= 0; second_q_b <= 0;
            captured_w <= 0; bram_rd_addr <= 0;
        end else begin
            done <= 0; qa_start <= 0;
            case (state)
                S_IDLE: begin
                    if (start) begin
                        node_idx <= 0; have_best <= 0;
                        have_second_int <= 0; bmu_valid <= 0;
                        bram_rd_addr <= 0; state <= S_READ_ADDR;
                    end
                end
                S_READ_ADDR: state <= S_READ_WAIT;
                S_READ_WAIT: begin
                    captured_w <= bram_rd_data;
                    state <= node_valid[node_idx] ? S_START_ACC : S_NEXT_NODE;
                end
                S_START_ACC: begin qa_start <= 1; state <= S_WAIT_ACC; end
                S_WAIT_ACC: if (qa_done) state <= S_EVAL;
                S_EVAL: begin
                    if (cand_better(qa_q[WIDTH-1:0], qa_q[SURD_W-1:WIDTH],
                                    node_id[node_idx],
                                    best_q_a, best_q_b, best_id, have_best)) begin
                        if (have_best) begin
                            second_id_int <= best_id; second_q_a <= best_q_a;
                            second_q_b <= best_q_b; have_second_int <= 1;
                        end
                        best_id <= node_id[node_idx];
                        best_q_a <= qa_q[WIDTH-1:0];
                        best_q_b <= qa_q[SURD_W-1:WIDTH];
                        best_label_int <= node_label[node_idx];
                        have_best <= 1;
                    end else if (cand_better(qa_q[WIDTH-1:0], qa_q[SURD_W-1:WIDTH],
                                             node_id[node_idx],
                                             second_q_a, second_q_b, second_id_int,
                                             have_second_int)) begin
                        second_id_int <= node_id[node_idx];
                        second_q_a <= qa_q[WIDTH-1:0];
                        second_q_b <= qa_q[SURD_W-1:WIDTH];
                        have_second_int <= 1;
                    end
                    state <= S_NEXT_NODE;
                end
                S_NEXT_NODE: begin
                    if (node_idx == MAX_NODES - 1)
                        state <= S_DONE;
                    else begin
                        node_idx <= node_idx + 1;
                        bram_rd_addr <= node_idx + 1;
                        state <= S_READ_WAIT;
                    end
                end
                S_DONE: begin
                    bmu_valid      <= have_best;
                    best_node_id   <= best_id;
                    second_node_id <= have_second_int ? second_id_int : 16'hFFFF;
                    cluster_label  <= best_label_int;
                    best_q         <= {best_q_b, best_q_a};
                    second_q       <= {second_q_b, second_q_a};
                    has_second     <= have_second_int;
                    if (have_second_int)
                        confidence_gap <= {second_q_b - best_q_b, second_q_a - best_q_a};
                    else confidence_gap <= 0;
                    done  <= 1; state <= S_IDLE;
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
