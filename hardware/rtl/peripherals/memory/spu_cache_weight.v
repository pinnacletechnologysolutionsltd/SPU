// spu_cache_weight.v — Infinitesimal Cache Weighting (v1.0)
//
// Replaces LRU heuristics with exact weight-derivative analysis.
// Each cache line carries a "Momentum Weight" ω = a (access frequency)
// tracked by the Nguyen-Widrow laminar_weight() function.
//
// The infinitesimal component is the first derivative:
//   Δ = current_weight − previous_weight
//
// Eviction decision: if Δ < 0 AND Δ < previous_Δ (accelerating downward),
// the line is "drifting out of the active execution horizon" and gets
// flagged for pre-emptive eviction — before LRU would notice.
//
// Resource estimate: 3 subtractors + 2 comparators per way.
// For 4-way associative: ~12 subtractors + 8 comparators = negligible.

module spu_cache_weight #(
    parameter WAYS = 4,
    parameter WEIGHT_BITS = 32
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        eval_en,          // pulse to evaluate weights

    // Current weights from Nguyen-Widrow (one per way)
    input  wire [WEIGHT_BITS-1:0] curr_weight_0,
    input  wire [WEIGHT_BITS-1:0] curr_weight_1,
    input  wire [WEIGHT_BITS-1:0] curr_weight_2,
    input  wire [WEIGHT_BITS-1:0] curr_weight_3,

    // Previous weights (registered internally from last evaluation)
    // Exposed for debug/telemetry
    output wire [WEIGHT_BITS-1:0] prev_weight_0,
    output wire [WEIGHT_BITS-1:0] prev_weight_1,
    output wire [WEIGHT_BITS-1:0] prev_weight_2,
    output wire [WEIGHT_BITS-1:0] prev_weight_3,

    // Previous deltas (acceleration detection)
    output wire signed [WEIGHT_BITS:0] prev_delta_0,
    output wire signed [WEIGHT_BITS:0] prev_delta_1,
    output wire signed [WEIGHT_BITS:0] prev_delta_2,
    output wire signed [WEIGHT_BITS:0] prev_delta_3,

    // Eviction decision
    output reg  [1:0]  evict_way,        // which way to evict (0-3)
    output reg         evict_valid        // 1 = eviction candidate found
);

    // ── Previous weight registers ──────────────────────────────────────
    reg [WEIGHT_BITS-1:0] pw_0, pw_1, pw_2, pw_3;

    assign prev_weight_0 = pw_0;
    assign prev_weight_1 = pw_1;
    assign prev_weight_2 = pw_2;
    assign prev_weight_3 = pw_3;

    // ── Previous delta registers (for acceleration) ────────────────────
    reg signed [WEIGHT_BITS:0] pd_0, pd_1, pd_2, pd_3;

    assign prev_delta_0 = pd_0;
    assign prev_delta_1 = pd_1;
    assign prev_delta_2 = pd_2;
    assign prev_delta_3 = pd_3;

    // ── Current deltas ─────────────────────────────────────────────────
    wire signed [WEIGHT_BITS:0] delta_0 = $signed(curr_weight_0) - $signed(pw_0);
    wire signed [WEIGHT_BITS:0] delta_1 = $signed(curr_weight_1) - $signed(pw_1);
    wire signed [WEIGHT_BITS:0] delta_2 = $signed(curr_weight_2) - $signed(pw_2);
    wire signed [WEIGHT_BITS:0] delta_3 = $signed(curr_weight_3) - $signed(pw_3);

    // ── Eviction logic (fully structural, no always @*) ────────────────

    wire candidate_0 = (delta_0 < 0) && (delta_0 < pd_0);
    wire candidate_1 = (delta_1 < 0) && (delta_1 < pd_1);
    wire candidate_2 = (delta_2 < 0) && (delta_2 < pd_2);
    wire candidate_3 = (delta_3 < 0) && (delta_3 < pd_3);

    wire any_candidate = candidate_0 || candidate_1 || candidate_2 || candidate_3;

    // Priority encoder: most negative delta among candidates
    wire way0_wins = candidate_0 && (!candidate_1 || delta_0 <= delta_1) &&
                     (!candidate_2 || delta_0 <= delta_2) &&
                     (!candidate_3 || delta_0 <= delta_3);
    wire way1_wins = candidate_1 && !way0_wins &&
                     (!candidate_2 || delta_1 <= delta_2) &&
                     (!candidate_3 || delta_1 <= delta_3);
    wire way2_wins = candidate_2 && !way0_wins && !way1_wins &&
                     (!candidate_3 || delta_2 <= delta_3);
    wire way3_wins = candidate_3 && !way0_wins && !way1_wins && !way2_wins;

    // Fallback: lowest current weight
    wire way0_low = (curr_weight_0 <= curr_weight_1) && (curr_weight_0 <= curr_weight_2) &&
                    (curr_weight_0 <= curr_weight_3);
    wire way1_low = (curr_weight_1 <= curr_weight_2) && (curr_weight_1 <= curr_weight_3) && !way0_low;
    wire way2_low = (curr_weight_2 <= curr_weight_3) && !way0_low && !way1_low;

    wire [1:0] next_evict_way = any_candidate
        ? (way0_wins ? 2'd0 : way1_wins ? 2'd1 : way2_wins ? 2'd2 : 2'd3)
        : (way0_low  ? 2'd0 : way1_low  ? 2'd1 : way2_low  ? 2'd2 : 2'd3);
    wire next_evict_valid = 1'b1;  // always have a candidate

    // ── Registered output ──────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pw_0 <= 0; pw_1 <= 0; pw_2 <= 0; pw_3 <= 0;
            pd_0 <= 0; pd_1 <= 0; pd_2 <= 0; pd_3 <= 0;
            evict_way <= 0;
            evict_valid <= 0;
        end else if (eval_en) begin
            pw_0 <= curr_weight_0;
            pw_1 <= curr_weight_1;
            pw_2 <= curr_weight_2;
            pw_3 <= curr_weight_3;
            pd_0 <= delta_0;
            pd_1 <= delta_1;
            pd_2 <= delta_2;
            pd_3 <= delta_3;
            evict_way <= next_evict_way;
            evict_valid <= next_evict_valid;
        end
    end

endmodule
