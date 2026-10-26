// spu13_neuro_epoch_sidecar.v -- deterministic SNN epoch guard proof.
//
// This block is intentionally synchronous.  It models a compact digital
// leaky-integrate-and-fire field for a fixed number of clock cycles, clamps
// membrane state at the epoch boundary, projects the spike counters into
// Z[phi]/L_p, then admits the vector only when its Lucas norm matches the
// configured envelope.

module spu13_neuro_epoch_sidecar #(
    parameter NUM_NEURONS = 8,
    parameter POT_WIDTH = 12,
    parameter COUNT_WIDTH = 8,
    parameter EPOCH_CYCLES = 16,
    parameter EPOCH_COUNT_WIDTH = 8,
    parameter LEAK = 1,
    parameter RESET_VAL = 0,
    parameter L_P = 521,
    parameter L_P_BITS = 10
) (
    input  wire                             clk,
    input  wire                             rst_n,
    input  wire                             clk_en,
    input  wire                             start_epoch,
    input  wire [NUM_NEURONS-1:0]           spike_in,
    input  wire [NUM_NEURONS*POT_WIDTH-1:0] weights,
    input  wire [NUM_NEURONS*POT_WIDTH-1:0] thresholds,
    input  wire [L_P_BITS-1:0]              expected_norm,
    input  wire [L_P_BITS-1:0]              fallback_a,
    input  wire [L_P_BITS-1:0]              fallback_b,
    output reg                              busy,
    output reg                              done,
    output reg                              accepted,
    output reg                              rejected,
    output reg                              norm_ok,
    output reg                              overflow_fault,
    output reg  [NUM_NEURONS-1:0]           token_mask,
    output reg  [15:0]                      spike_total,
    output reg  [L_P_BITS-1:0]              proposal_a,
    output reg  [L_P_BITS-1:0]              proposal_b,
    output reg  [L_P_BITS-1:0]              norm_value,
    output reg  [L_P_BITS-1:0]              commit_a,
    output reg  [L_P_BITS-1:0]              commit_b
);

    localparam [COUNT_WIDTH-1:0] COUNT_MAX = {COUNT_WIDTH{1'b1}};
    localparam [31:0] BARRETT_MU = 32'h8000_0000 / L_P;

    reg [POT_WIDTH-1:0] membrane [0:NUM_NEURONS-1];
    reg [COUNT_WIDTH-1:0] spike_count [0:NUM_NEURONS-1];
    reg [EPOCH_COUNT_WIDTH-1:0] epoch_idx;

    integer i;
    reg [POT_WIDTH:0] mem_next;
    reg [POT_WIDTH-1:0] weight_i;
    reg [POT_WIDTH-1:0] threshold_i;
    reg [COUNT_WIDTH-1:0] count_next;
    reg [31:0] sum_a_tmp;
    reg [31:0] sum_b_tmp;
    reg norm_pending;
    reg overflow_latched;
    reg [L_P_BITS-1:0] expected_norm_latched;
    reg [L_P_BITS-1:0] fallback_a_latched;
    reg [L_P_BITS-1:0] fallback_b_latched;
    reg overflow_tmp;
    reg last_cycle;

    function [POT_WIDTH-1:0] packed_word;
        input [NUM_NEURONS*POT_WIDTH-1:0] bus;
        input integer idx;
        begin
            packed_word = bus[idx*POT_WIDTH +: POT_WIDTH];
        end
    endfunction

    function [L_P_BITS-1:0] red_full;
        input [31:0] x;
        reg [31:0] hi1;
        reg [31:0] hi2;
        reg signed [31:0] fold1;
        reg signed [31:0] fold2;
        reg [63:0] q_est;
        reg [31:0] r_est;
        begin
            if (L_P == 521) begin
                // 521 = 2^9 + 9, so 2^9 == -9 (mod 521).  The sidecar only
                // feeds bounded counter and norm values here; two folds cover
                // the Tang 25K guard proof range without a reciprocal multiply.
                hi1 = x >> 9;
                fold1 = $signed({1'b0, x[8:0]}) + 32'sd17714 -
                        $signed((hi1 << 3) + hi1);
                hi2 = fold1[31:9];
                fold2 = $signed({1'b0, fold1[8:0]}) + 32'sd521 -
                        $signed((hi2 << 3) + hi2);
                if (fold2 < 0) fold2 = fold2 + 32'sd521;
                if (fold2 >= 521) fold2 = fold2 - 32'sd521;
                if (fold2 >= 521) fold2 = fold2 - 32'sd521;
                red_full = fold2[L_P_BITS-1:0];
            end else begin
                q_est = (x * BARRETT_MU) >> 31;
                r_est = x - (q_est * L_P);
                if (r_est >= L_P) r_est = r_est - L_P;
                if (r_est >= L_P) r_est = r_est - L_P;
                red_full = r_est[L_P_BITS-1:0];
            end
        end
    endfunction

    wire [31:0] proposal_a_ext = proposal_a;
    wire [31:0] proposal_b_ext = proposal_b;
    wire [31:0] norm_span = proposal_a_ext + L_P - proposal_b_ext;
    wire [31:0] norm_raw = (proposal_a_ext * proposal_a_ext) +
                           (proposal_b_ext * norm_span);
    wire [L_P_BITS-1:0] norm_calc = red_full(norm_raw);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy <= 1'b0;
            done <= 1'b0;
            accepted <= 1'b0;
            rejected <= 1'b0;
            norm_ok <= 1'b0;
            overflow_fault <= 1'b0;
            token_mask <= {NUM_NEURONS{1'b0}};
            spike_total <= 16'd0;
            proposal_a <= {L_P_BITS{1'b0}};
            proposal_b <= {L_P_BITS{1'b0}};
            norm_value <= {L_P_BITS{1'b0}};
            commit_a <= {L_P_BITS{1'b0}};
            commit_b <= {L_P_BITS{1'b0}};
            epoch_idx <= {EPOCH_COUNT_WIDTH{1'b0}};
            norm_pending <= 1'b0;
            overflow_latched <= 1'b0;
            expected_norm_latched <= {L_P_BITS{1'b0}};
            fallback_a_latched <= {L_P_BITS{1'b0}};
            fallback_b_latched <= {L_P_BITS{1'b0}};
            for (i = 0; i < NUM_NEURONS; i = i + 1) begin
                membrane[i] <= {POT_WIDTH{1'b0}};
                spike_count[i] <= {COUNT_WIDTH{1'b0}};
            end
        end else if (clk_en) begin
            done <= 1'b0;
            // accepted, rejected, norm_ok are NOT cleared here; they hold
            // until the next epoch overwrites them.  Only done (which
            // drives the adapter's auto-latch trigger) is a 1-cycle pulse.
            //
            // This avoids an NB-timing wall where an external observer
            // (adapter latch, probe state machine) reads cleared values
            // before the norm_pending NBA updates take effect.

            if (norm_pending) begin
                norm_pending <= 1'b0;
                busy <= 1'b0;
                done <= 1'b1;
                norm_value <= norm_calc;
                norm_ok <= (norm_calc == expected_norm_latched) && !overflow_latched;

                if ((norm_calc == expected_norm_latched) && !overflow_latched) begin
                    accepted <= 1'b1;
                    rejected <= 1'b0;
                    commit_a <= proposal_a;
                    commit_b <= proposal_b;
                end else begin
                    accepted <= 1'b0;
                    rejected <= 1'b1;
                    commit_a <= fallback_a_latched;
                    commit_b <= fallback_b_latched;
                end
            end else if (!busy && start_epoch) begin
                busy <= 1'b1;
                epoch_idx <= {EPOCH_COUNT_WIDTH{1'b0}};
                overflow_fault <= 1'b0;
                overflow_latched <= 1'b0;
                expected_norm_latched <= expected_norm;
                fallback_a_latched <= fallback_a;
                fallback_b_latched <= fallback_b;
                accepted <= 1'b0;
                rejected <= 1'b0;
                norm_ok <= 1'b0;
                token_mask <= {NUM_NEURONS{1'b0}};
                spike_total <= 16'd0;
                for (i = 0; i < NUM_NEURONS; i = i + 1) begin
                    membrane[i] <= RESET_VAL[POT_WIDTH-1:0];
                    spike_count[i] <= {COUNT_WIDTH{1'b0}};
                end
            end else if (busy) begin
                sum_a_tmp = 32'd0;
                sum_b_tmp = 32'd0;
                overflow_tmp = overflow_fault;
                last_cycle = (epoch_idx == (EPOCH_CYCLES - 1));

                for (i = 0; i < NUM_NEURONS; i = i + 1) begin
                    weight_i = packed_word(weights, i);
                    threshold_i = packed_word(thresholds, i);
                    count_next = spike_count[i];

                    if (spike_in[i]) begin
                        mem_next = {1'b0, membrane[i]} + {1'b0, weight_i};
                    end else if (membrane[i] > LEAK[POT_WIDTH-1:0]) begin
                        mem_next = {1'b0, membrane[i] - LEAK[POT_WIDTH-1:0]};
                    end else begin
                        mem_next = {(POT_WIDTH+1){1'b0}};
                    end

                    if ((threshold_i != {POT_WIDTH{1'b0}}) &&
                        (mem_next >= {1'b0, threshold_i})) begin
                        if (spike_count[i] == COUNT_MAX) begin
                            overflow_tmp = 1'b1;
                        end else begin
                            count_next = spike_count[i] + {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
                        end
                        token_mask[i] <= 1'b1;
                        membrane[i] <= RESET_VAL[POT_WIDTH-1:0];
                    end else begin
                        membrane[i] <= mem_next[POT_WIDTH-1:0];
                    end

                    spike_count[i] <= count_next;

                    if (last_cycle) begin
                        sum_a_tmp = sum_a_tmp + (count_next * (i + 1));
                        sum_b_tmp = sum_b_tmp + count_next;
                    end
                end

                overflow_fault <= overflow_tmp;

                if (last_cycle) begin
                    norm_pending <= 1'b1;
                    proposal_a <= red_full(sum_a_tmp);
                    proposal_b <= red_full(sum_b_tmp);
                    spike_total <= sum_b_tmp[15:0];
                    overflow_latched <= overflow_tmp;

                    for (i = 0; i < NUM_NEURONS; i = i + 1) begin
                        membrane[i] <= RESET_VAL[POT_WIDTH-1:0];
                    end
                end else begin
                    epoch_idx <= epoch_idx + {{(EPOCH_COUNT_WIDTH-1){1'b0}}, 1'b1};
                end
            end
        end
    end
endmodule
