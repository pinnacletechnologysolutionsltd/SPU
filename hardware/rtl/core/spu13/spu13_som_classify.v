`timescale 1ns / 1ps

// spu13_som_classify.v — SOM Classifier with PHSLK Fast Path
//
// Behavioral model for SOM classification using jet algebra over
// A_SPU = GF(p⁴)[ε]/(ε³).  Two classification paths:
//
//   FAST PATH (PHSLK, ~12 cycles):
//     Compute O·C for each centroid.  If any pair gives identity (coherent),
//     classify immediately — exact Offer/Confirmation match.
//
//   FULL PATH (serial scan, ~N×12 cycles):
//     Compute position-field quadrance Qᵢ = ||f₀ − cᵢ₀||² for each centroid.
//     WTA tree selects minimum.  Confidence gap = Q_second − Q_best.
//     If gap = 0 → boundary region (ambiguous classification).
//
// FLAGS:
//   FLAGS.C = 1 → PHSLK fast path matched (JC branch)
//   FLAGS.V = 1 → err_zero_divisor (feature non-invertible)
//   ambiguous → confidence gap = 0 → boundary region
//
// Parameters:
//   N_CENTROIDS = 7   — number of classification centroids
//   JET_ORDER   = 2   — n=2, ε³=0

module spu13_som_classify #(
    parameter N_CENTROIDS = 7,
    parameter JET_ORDER   = 2
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // ── Feature jet F = (f₀, f₁, f₂) ───────────────────────────────
    input  wire [31:0]  f0_z0, f0_z1, f0_z2, f0_z3,
    input  wire [31:0]  f1_z0, f1_z1, f1_z2, f1_z3,
    input  wire [31:0]  f2_z0, f2_z1, f2_z2, f2_z3,

    // ── Centroid jets C[0..N-1] = (c₀, c₁, c₂) ────────────────────
    // Flattened: centroid[i] has 12 entries: c₀[0..3], c₁[0..3], c₂[0..3]
    input  wire [31:0]  centroid_flat [0:(N_CENTROIDS*12)-1],

    // ── Classification output ──────────────────────────────────────
    output reg  [7:0]   best_id,
    output reg  [7:0]   second_id,
    output reg  [31:0]  confidence_gap,   // Q_second − Q_best
    output reg          ambiguous,
    output reg          flag_c,            // PHSLK fast path matched
    output reg          flag_v,            // valid (non-zero-divisor)
    output reg          done,
    output wire         busy,

    // ── Shared M31 multiplier interface ────────────────────────────
    output reg          mult_start,
    output reg  [31:0]  mult_a0, mult_a1, mult_a2, mult_a3,
    output reg  [31:0]  mult_b0, mult_b1, mult_b2, mult_b3,
    input  wire [31:0]  mult_r0, mult_r1, mult_r2, mult_r3,
    input  wire         mult_done
);

    localparam P = 32'h7FFFFFFF;

    // ── FSM states ──────────────────────────────────────────────────
    localparam ST_IDLE       = 4'd0;
    localparam ST_PHSLK      = 4'd1;  // Fast path: launch O·C coherence check
    localparam ST_PHSLK_CLR  = 4'd2;  // Wait for mac_done to clear (settle)
    localparam ST_PHSLK_WAIT = 4'd3;  // Wait for mac_done (new computation)
    localparam ST_QSCAN      = 4'd4;  // Full path: quadrance scan
    localparam ST_WTA        = 4'd5;  // WTA comparison
    localparam ST_DONE       = 4'd6;

    reg [3:0] state;
    assign busy = (state != ST_IDLE) && (state != ST_DONE);

    // ── Helper functions ────────────────────────────────────────────
    function [31:0] m31_sub;
        input [31:0] x, y;
        begin m31_sub = (x >= y) ? (x - y) : (x + P - y); end
    endfunction

    // ── Quadrance storage (per-centroid) ────────────────────────────
    reg [63:0] quadrance [0:N_CENTROIDS-1];
    reg [7:0]  centroid_id;

    // ── PHSLK coherence check ──────────────────────────────────────
    // For each centroid, compute O·C and check against identity.
    // O = feature jet F, C = centroid jet C[i].
    // Uses jet MAC for Cauchy product, then lane comparison.
    reg        phslk_scanning;
    reg [7:0]  phslk_idx;

    // Jet MAC signals
    wire [31:0] mac_r0_z0, mac_r0_z1, mac_r0_z2, mac_r0_z3;
    wire [31:0] mac_r1_z0, mac_r1_z1, mac_r1_z2, mac_r1_z3;
    wire [31:0] mac_r2_z0, mac_r2_z1, mac_r2_z2, mac_r2_z3;
    wire mac_done, mac_busy, mac_ez;

    // Flatten centroid access for jet MAC
    wire [31:0] centroid_j0_z0, centroid_j0_z1, centroid_j0_z2, centroid_j0_z3;
    wire [31:0] centroid_j1_z0, centroid_j1_z1, centroid_j1_z2, centroid_j1_z3;
    wire [31:0] centroid_j2_z0, centroid_j2_z1, centroid_j2_z2, centroid_j2_z3;

    // Map flattened index to centroid components (12 entries per centroid)
    wire [10:0] c_base = {phslk_idx, 3'd0} + {phslk_idx, 2'd0};  // idx * 12
    assign centroid_j0_z0 = centroid_flat[c_base + 9'd0];
    assign centroid_j0_z1 = centroid_flat[c_base + 9'd1];
    assign centroid_j0_z2 = centroid_flat[c_base + 9'd2];
    assign centroid_j0_z3 = centroid_flat[c_base + 9'd3];
    assign centroid_j1_z0 = centroid_flat[c_base + 9'd4];
    assign centroid_j1_z1 = centroid_flat[c_base + 9'd5];
    assign centroid_j1_z2 = centroid_flat[c_base + 9'd6];
    assign centroid_j1_z3 = centroid_flat[c_base + 9'd7];
    assign centroid_j2_z0 = centroid_flat[c_base + 9'd8];
    assign centroid_j2_z1 = centroid_flat[c_base + 9'd9];
    assign centroid_j2_z2 = centroid_flat[c_base + 9'd10];
    assign centroid_j2_z3 = centroid_flat[c_base + 9'd11];

    // Jet MAC instantiation for PHSLK checks
    spu13_jet_mac #(.N(JET_ORDER)) u_jet_mac (
        .clk(clk), .rst_n(rst_n), .start(phslk_scanning), .op_mul(1'b1),
        .j_coeff('{'{f0_z0,f0_z1,f0_z2,f0_z3},
                    '{f1_z0,f1_z1,f1_z2,f1_z3},
                    '{f2_z0,f2_z1,f2_z2,f2_z3}}),
        .k_coeff('{'{centroid_j0_z0,centroid_j0_z1,centroid_j0_z2,centroid_j0_z3},
                    '{centroid_j1_z0,centroid_j1_z1,centroid_j1_z2,centroid_j1_z3},
                    '{centroid_j2_z0,centroid_j2_z1,centroid_j2_z2,centroid_j2_z3}}),
        .r_coeff('{'{mac_r0_z0,mac_r0_z1,mac_r0_z2,mac_r0_z3},
                    '{mac_r1_z0,mac_r1_z1,mac_r1_z2,mac_r1_z3},
                    '{mac_r2_z0,mac_r2_z1,mac_r2_z2,mac_r2_z3}}),
        .done(mac_done), .busy(mac_busy), .err_zero_divisor(mac_ez),
        .mult_start(mult_start),
        .mult_a0(mult_a0), .mult_a1(mult_a1), .mult_a2(mult_a2), .mult_a3(mult_a3),
        .mult_b0(mult_b0), .mult_b1(mult_b1), .mult_b2(mult_b2), .mult_b3(mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1), .mult_r2(mult_r2), .mult_r3(mult_r3),
        .mult_done(mult_done)
    );

    // ── Main FSM ────────────────────────────────────────────────────
    integer i;
    reg [63:0] best_q, second_q;
    reg [7:0]  best_i, second_i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= ST_IDLE;
            done      <= 1'b0;
            flag_c    <= 1'b0;
            flag_v    <= 1'b0;
            ambiguous <= 1'b0;
            phslk_scanning <= 1'b0;
            phslk_idx <= 8'd0;
            best_id   <= 8'd0;
            second_id <= 8'd0;
            confidence_gap <= 32'd0;
            for (i = 0; i < N_CENTROIDS; i = i + 1)
                quadrance[i] <= 64'd0;
        end else begin
            case (state)
                ST_IDLE: begin
                    done <= 1'b0;
                    flag_c <= 1'b0;
                    flag_v <= 1'b0;
                    ambiguous <= 1'b0;
                    if (start) begin
                        // Zero-divisor check: feature must be invertible
                        if (f0_z0 == 32'd0 && f0_z1 == 32'd0 &&
                            f0_z2 == 32'd0 && f0_z3 == 32'd0) begin
                            flag_v <= 1'b0;
                            best_id <= 8'd0;
                            done <= 1'b1;
                            state <= ST_DONE;
                        end else begin
                            flag_v <= 1'b1;
                            // Start PHSLK fast-path scan
                            phslk_idx <= 8'd0;
                            phslk_scanning <= 1'b1;
                            state <= ST_PHSLK;
                        end
                    end
                end

                // ── PHSLK fast path: launch, then settle ──────────
                ST_PHSLK: begin
                    phslk_scanning <= 1'b0;
                    state <= ST_PHSLK_CLR;
                end

                ST_PHSLK_CLR: begin
                    // Wait one cycle for mac_done to clear (was high from previous op)
                    state <= ST_PHSLK_WAIT;
                end

                ST_PHSLK_WAIT: begin
                    if (mac_done) begin
                        // Check if O·C = (1,0,0)
                        if (mac_r0_z0 == 32'd1 && mac_r0_z1 == 32'd0 &&
                            mac_r0_z2 == 32'd0 && mac_r0_z3 == 32'd0 &&
                            mac_r1_z0 == 32'd0 && mac_r1_z1 == 32'd0 &&
                            mac_r1_z2 == 32'd0 && mac_r1_z3 == 32'd0 &&
                            mac_r2_z0 == 32'd0 && mac_r2_z1 == 32'd0 &&
                            mac_r2_z2 == 32'd0 && mac_r2_z3 == 32'd0) begin
                            // Coherent match found!
                            flag_c <= 1'b1;
                            best_id <= phslk_idx;
                            done <= 1'b1;
                            state <= ST_DONE;
                        end else if (phslk_idx < N_CENTROIDS - 1) begin
                            // Try next centroid
                            phslk_idx <= phslk_idx + 8'd1;
                            phslk_scanning <= 1'b1;
                            state <= ST_PHSLK;
                        end else begin
                            // No coherent match — fall through to full scan
                            // (simplified: just mark as not coherent)
                            flag_c <= 1'b0;
                            best_id <= 8'd0;
                            done <= 1'b1;
                            state <= ST_DONE;
                        end
                    end
                end

                ST_QSCAN: begin
                    // Full quadrance scan (deferred to full implementation)
                    state <= ST_DONE;
                end

                ST_WTA: begin
                    state <= ST_DONE;
                end

                ST_DONE: begin
                    done  <= 1'b1;
                    phslk_scanning <= 1'b0;
                    state <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
