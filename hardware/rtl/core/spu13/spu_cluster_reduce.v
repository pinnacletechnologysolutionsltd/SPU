// SPU-13 Cluster/Classification Reduce (v1.0)
//
// Validates BMU result and emits final classification output:
//   - cluster_label from best matching unit
//   - confidence_gap = second_q − best_q
//   - ambiguity flag when gap ≤ threshold or no valid BMU
//
// This is a thin pipeline stage that bridges the BMU to the classifier
// emission layer.  In the staged RTL plan it sits between spu_som_bmu
// and spu_class_emit.

module spu_cluster_reduce #(
    parameter WIDTH = 32
)(
    input  wire               clk,
    input  wire               rst_n,

    input  wire               bmu_valid,
    input  wire [15:0]        best_node_id,
    input  wire [15:0]        cluster_label_in,
    input  wire [2*WIDTH-1:0] best_q,
    input  wire [2*WIDTH-1:0] second_q,
    input  wire [2*WIDTH-1:0] confidence_gap_in,
    input  wire               has_second,

    // Optional ambiguity threshold (default: zero)
    input  wire [2*WIDTH-1:0] ambiguity_threshold,

    output reg                 classify_valid,
    output reg  [15:0]         label,
    output reg  [2*WIDTH-1:0]  confidence_gap,
    output reg                 ambiguous
);

    wire signed [2*WIDTH-1:0] gap_a, gap_b;
    wire signed [2*WIDTH-1:0] thresh_a, thresh_b;
    wire signed [63:0]        da, db;

    // Recompute confidence_gap from second_q - best_q for safety
    assign gap_a = second_q[WIDTH-1:0] - best_q[WIDTH-1:0];
    assign gap_b = second_q[2*WIDTH-1:WIDTH] - best_q[2*WIDTH-1:WIDTH];

    assign thresh_a = ambiguity_threshold[WIDTH-1:0];
    assign thresh_b = ambiguity_threshold[2*WIDTH-1:WIDTH];

    // gap ≤ threshold check using integer-only Q(√3) ordering
    wire gap_le_thresh;

    assign da = gap_a - thresh_a;
    assign db = gap_b - thresh_b;

    assign gap_le_thresh =
        (da == 0 && db == 0) ? 1 :
        (da <= 0 && db <= 0) ? 1 :
        (da >= 0 && db >= 0) ? 0 :
        (da < 0 && db > 0)   ? (da*da > 3*db*db) :
                               (da*da < 3*db*db);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            classify_valid <= 0;
            label          <= 0;
            confidence_gap <= 0;
            ambiguous      <= 0;
        end else begin
            classify_valid <= bmu_valid;
            label          <= cluster_label_in;
            confidence_gap <= confidence_gap_in;
            ambiguous      <= !bmu_valid ||
                              (has_second && gap_le_thresh);
        end
    end

endmodule
