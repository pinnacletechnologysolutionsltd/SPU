// SPU-13 Quadrance Accumulator (v1.1)
//
// Computes weighted quadrance for one SOM node across NUM_FEATURES features:
//   Q_node = sum_j r_j * (x_j - w_ij)^2
//
// One shared surd_multiplier (SHIFT=0) re-used for squaring then weight
// multiply.  5 cycles per feature: delta → square-issue → square-wait →
// weight-mul-issue → weight-wait+accumulate.
//
// Parameters:
//   NUM_FEATURES = 4   number of feature dimensions
//   WIDTH        = 32  bit-width of each surd coefficient

module spu_quadrance_accum #(
    parameter NUM_FEATURES = 4,
    parameter WIDTH = 18
)(
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  start,
    output reg                   done,

    // Feature vector x_j  (flat 2*WIDTH*NUM_FEATURES bits, one surd per feature)
    // Packed as: { b[N-1], a[N-1], ..., b[0], a[0] }
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] features,

    // Node weight vector w_ij  (same packing)
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] node_weights,

    // Feature weight vector r_j  (same packing)
    input  wire [(2*WIDTH*NUM_FEATURES)-1:0] feature_weights,

    // Accumulated quadrance Q_node  {surd_b, surd_a}
    output reg  [2*WIDTH-1:0] q_node,
    output reg                 accum_overflow   // high bits lost in truncation
);

    localparam SURD_W = 2 * WIDTH;  // 64 bits per RationalSurd

    // --- TDM controller ---
    reg [3:0] state;  // 0-6
    localparam S_IDLE  = 0;
    localparam S_SQ    = 1;   // issue square multiply
    localparam S_WAIT1 = 2;   // wait for square result
    localparam S_WT    = 3;   // issue weight multiply
    localparam S_WAIT2 = 4;   // wait for weight result, accumulate
    localparam S_NEXT  = 5;   // feat_idx settled, load next delta
    localparam S_DONE  = 6;

    reg [$clog2(NUM_FEATURES)-1:0] feat_idx;

    // --- Combinational extraction of current feature's surds ---
    wire [SURD_W-1:0] cur_feat   = features[      feat_idx * SURD_W +: SURD_W];
    wire [SURD_W-1:0] cur_weight = node_weights[   feat_idx * SURD_W +: SURD_W];
    wire [SURD_W-1:0] cur_fw     = feature_weights[feat_idx * SURD_W +: SURD_W];

    // Delta = feature - node_weight (combinational)
    wire signed [WIDTH-1:0] delta_a = cur_feat[WIDTH-1:0] - cur_weight[WIDTH-1:0];
    wire signed [WIDTH-1:0] delta_b = cur_feat[SURD_W-1:WIDTH] - cur_weight[SURD_W-1:WIDTH];

    // --- surd_multiplier interface ---
    reg  [SURD_W-1:0] sm_op1, sm_op2;
    wire [SURD_W-1:0] sm_res;

    surd_multiplier #(.WIDTH(WIDTH), .SHIFT(0), .DEVICE("GW5A")) u_sm (
        .clk(clk), .reset(!rst_n),
        .field_sel(2'b00),  // Q(√3)
        .a1(sm_op1[WIDTH-1:0]),  .b1(sm_op1[SURD_W-1:WIDTH]),
        .a2(sm_op2[WIDTH-1:0]),  .b2(sm_op2[SURD_W-1:WIDTH]),
        .res_a(sm_res[WIDTH-1:0]), .res_b(sm_res[SURD_W-1:WIDTH])
    );

    // --- Accumulator (double-width for overflow safety) ---
    reg signed [2*WIDTH-1:0] acc_a, acc_b;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            done     <= 0;
            feat_idx <= 0;
            acc_a    <= 0;
            acc_b    <= 0;
            q_node   <= 0;
            sm_op1   <= 0;
            sm_op2   <= 0;
            accum_overflow <= 0;
        end else begin
            done <= 0;
            case (state)
                S_IDLE: begin
                    if (start) begin
                        feat_idx <= 0;
                        acc_a    <= 0;
                        acc_b    <= 0;
                        state    <= S_NEXT;  // wait for delta wires to settle
                    end
                end

                S_SQ: begin
                    // Square result available next cycle
                    state <= S_WAIT1;
                end

                S_WAIT1: begin
                    // Issue weight multiply: feature_weight * square
                    sm_op1 <= cur_fw;
                    sm_op2 <= sm_res;
                    state  <= S_WT;
                end

                S_WT: begin
                    // Weight multiply result available next cycle
                    state <= S_WAIT2;
                end

                S_WAIT2: begin
                    // Accumulate weighted quadrance for this feature
                    acc_a <= acc_a + sm_res[WIDTH-1:0];
                    acc_b <= acc_b + sm_res[SURD_W-1:WIDTH];

                    if (feat_idx == NUM_FEATURES - 1) begin
                        state <= S_DONE;
                    end else begin
                        feat_idx <= feat_idx + 1;
                        state    <= S_NEXT;  // wait for delta wires to settle
                    end
                end

                S_NEXT: begin
                    // feat_idx has updated — delta wires now reflect next feature
                    sm_op1 <= {delta_b, delta_a};
                    sm_op2 <= {delta_b, delta_a};
                    state  <= S_SQ;
                end

                S_DONE: begin
                    // acc updated on this clock edge — truncate to WIDTH bits per component
                    q_node <= {acc_b[WIDTH-1:0], acc_a[WIDTH-1:0]};
                    // Overflow: high bits beyond WIDTH are not pure sign extension
                    accum_overflow <= (|acc_a[2*WIDTH-1:WIDTH]) != (&acc_a[2*WIDTH-1:WIDTH]) ||
                                      (|acc_b[2*WIDTH-1:WIDTH]) != (&acc_b[2*WIDTH-1:WIDTH]);
                    done   <= 1;
                    state  <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
