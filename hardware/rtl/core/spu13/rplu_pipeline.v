`timescale 1ns / 1ps

// rplu_pipeline.v — 4-stage RPLU pipeline top
//
// Φ₁ Kohonen SOM BMU → saddle point detection
// Φ₂ BTU → native A31/Quadray lane routing
// Φ₃ Thimble-Padé → rational approximant evaluation
// Φ₄ M31 Multiplier + Reducer → final arithmetic and output
//
// Pipeline control: each stage latches its output on posedge clk.
// Pipeline stall is asserted when BTU detects multi-saddle collision.
// The inverter is shared between the Padé solver and pipeline.

module rplu_pipeline #(
    parameter NUM_FEATURES = 4,
    parameter MAX_NODES    = 7,
    parameter WIDTH        = 18
) (
    input  wire         clk,
    input  wire         rst_n,

    // ── Φ₁: SOM input interface ────────────────────────────────────
    input  wire [NUM_FEATURES * 2 * WIDTH - 1 : 0] som_features,
    input  wire                                    som_start,
    output wire                                    som_done,
    output wire [15:0]                             som_best_id,
    output wire [15:0]                             som_cluster_label,
    output wire [63:0]                             som_best_q,

    // ── Padé coefficient load interface ────────────────────────────
    input  wire         pade_coeff_we,
    input  wire         pade_coeff_is_den,
    input  wire [2:0]   pade_coeff_addr,
    input  wire [31:0]  pade_c0, pade_c1, pade_c2, pade_c3,
    input  wire [31:0]  quadray_target_kappa,

    // ── Φ₄: Final output ───────────────────────────────────────────
    output wire [31:0]  thimble_c0, thimble_c1, thimble_c2, thimble_c3,
    output wire         thimble_valid,
    output wire [31:0]  quadray_delta,
    output wire         quadray_coherent,
    output wire         quadray_valid,
    output wire         pipeline_busy,
    output wire         pipeline_stall
);

    // ── Φ₁ → Φ₂ interconnect ──────────────────────────────────────
    wire        bmu_done, bmu_valid;
    wire [15:0] bmu_best_id;
    wire [63:0] bmu_best_q;
    wire [15:0] bmu_cluster_label;

    // Convert BMU best_id to 64-bit one-hot for BTU
    wire [63:0] btu_activation;
    assign btu_activation = (bmu_valid) ? (64'd1 << bmu_best_id[5:0]) : 64'd0;

    // ── Φ₂ → Φ₃ interconnect ──────────────────────────────────────
    wire [31:0] btu_c0, btu_c1, btu_c2, btu_c3;
    wire        btu_valid;
    wire        btu_stall;
    wire [31:0] quadray_delta_w;
    wire        quadray_coherent_w;
    wire        quadray_valid_w;

    // ── Φ₃ → Φ₄ interconnect ──────────────────────────────────────
    wire        pade_start;
    wire [31:0] pade_result_c0, pade_result_c1, pade_result_c2, pade_result_c3;
    wire        pade_done, pade_busy;

    // ── Shared multiplier ──────────────────────────────────────────
    wire        mult_start_w;
    wire [31:0] mult_a0_w, mult_a1_w, mult_a2_w, mult_a3_w;
    wire [31:0] mult_b0_w, mult_b1_w, mult_b2_w, mult_b3_w;
    wire [31:0] mult_r0_w, mult_r1_w, mult_r2_w, mult_r3_w;
    wire        mult_done_w, mult_busy_w;

    // ── F_{p^4} inverter (shared) ──────────────────────────────────
    wire        inv_start_w;
    wire [31:0] inv_z0_w, inv_z1_w, inv_z2_w, inv_z3_w;
    wire [31:0] inv_r0_w, inv_r1_w, inv_r2_w, inv_r3_w;
    wire        inv_done_w, inv_busy_w, inv_flags_v;
    wire        pade_flags_v;

    // ── Pipeline stage latches ─────────────────────────────────────
    reg         phi1_valid, phi2_valid, phi3_valid, phi4_valid;
    reg         som_active;
    reg         pade_inflight;
    reg [1:0]  quadray_pending;
    reg [31:0]  phi2_c0, phi2_c1, phi2_c2, phi2_c3;
    reg [31:0]  phi3_c0, phi3_c1, phi3_c2, phi3_c3;
    reg [31:0]  phi4_c0, phi4_c1, phi4_c2, phi4_c3;

    // ── Φ₁: Kohonen SOM BMU ───────────────────────────────────────
    spu_som_bmu #(
        .NUM_FEATURES(NUM_FEATURES),
        .MAX_NODES(MAX_NODES),
        .WIDTH(WIDTH)
    ) u_som (
        .clk(clk), .rst_n(rst_n),
        .start(som_start),
        .done(som_done),
        .features(som_features),
        .feature_weights({NUM_FEATURES * 2 * WIDTH{1'b0}}),  // default uniform
        .bmu_valid(bmu_valid),
        .best_node_id(bmu_best_id),
        .second_node_id(),
        .cluster_label(bmu_cluster_label),
        .best_q(bmu_best_q),
        .second_q(),
        .confidence_gap(),
        .has_second(),
        .axiomatic_level(2'd0),
        .axiomatic_fault(),
        .fault_type(),
        .fault_count(),
        .train_we(1'b0),
        .train_addr(3'd0),
        .train_wdata({NUM_FEATURES * 2 * WIDTH{1'b0}}),
        .train_rdata()
    );

    assign som_best_id       = bmu_best_id;
    assign som_cluster_label = bmu_cluster_label;
    assign som_best_q        = bmu_best_q;

    // ── Φ₂: BTU transmutation ──────────────────────────────────────
    spu13_btu_core_top u_btu (
        .clk(clk), .rst_n(rst_n),
        .neuron_activation_lines(btu_activation),
        .btu_lane_c0(btu_c0), .btu_lane_c1(btu_c1),
        .btu_lane_c2(btu_c2), .btu_lane_c3(btu_c3),
        .pipeline_stall(btu_stall),
        .data_valid(btu_valid)
    );

    // ── Φ₂ sidecar: native Quadray SQR variety residual ─────────────
    spu13_quadray_variety u_quadray_variety (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(btu_valid),
        .coord_a(btu_c0),
        .coord_b(btu_c1),
        .coord_c(btu_c2),
        .coord_d(btu_c3),
        .target_kappa(quadray_target_kappa),
        .valid_out(quadray_valid_w),
        .delta_out(quadray_delta_w),
        .coherent(quadray_coherent_w)
    );

    // ── Φ₃: Thimble-Padé evaluator ─────────────────────────────────
    rplu_thimble_pade u_pade (
        .clk(clk), .rst_n(rst_n),
        .start(pade_start),
        .saddle_c0(phi2_c0), .saddle_c1(phi2_c1),
        .saddle_c2(phi2_c2), .saddle_c3(phi2_c3),
        .coeff_we(pade_coeff_we),
        .coeff_is_den(pade_coeff_is_den),
        .coeff_addr(pade_coeff_addr),
        .coeff_c0(pade_c0), .coeff_c1(pade_c1),
        .coeff_c2(pade_c2), .coeff_c3(pade_c3),
        .result_c0(pade_result_c0), .result_c1(pade_result_c1),
        .result_c2(pade_result_c2), .result_c3(pade_result_c3),
        .done(pade_done), .busy(pade_busy),
        .flags_v(pade_flags_v),
        .mult_start(mult_start_w),
        .mult_a0(mult_a0_w), .mult_a1(mult_a1_w),
        .mult_a2(mult_a2_w), .mult_a3(mult_a3_w),
        .mult_b0(mult_b0_w), .mult_b1(mult_b1_w),
        .mult_b2(mult_b2_w), .mult_b3(mult_b3_w),
        .mult_r0(mult_r0_w), .mult_r1(mult_r1_w),
        .mult_r2(mult_r2_w), .mult_r3(mult_r3_w),
        .mult_done(mult_done_w), .mult_busy(mult_busy_w),
        .inv_start(inv_start_w),
        .inv_z0(inv_z0_w), .inv_z1(inv_z1_w),
        .inv_z2(inv_z2_w), .inv_z3(inv_z3_w),
        .inv_r0(inv_r0_w), .inv_r1(inv_r1_w),
        .inv_r2(inv_r2_w), .inv_r3(inv_r3_w),
        .inv_done(inv_done_w), .inv_busy(inv_busy_w),
        .inv_flags_v(inv_flags_v)
    );

    // ── Shared multiplier for Padé engine ──────────────────────────
    spu13_m31_multiplier u_mult_pade (
        .clk(clk), .rst_n(rst_n),
        .start(mult_start_w),
        .a0(mult_a0_w), .a1(mult_a1_w), .a2(mult_a2_w), .a3(mult_a3_w),
        .b0(mult_b0_w), .b1(mult_b1_w), .b2(mult_b2_w), .b3(mult_b3_w),
        .r0(mult_r0_w), .r1(mult_r1_w), .r2(mult_r2_w), .r3(mult_r3_w),
        .done(mult_done_w), .busy(mult_busy_w)
    );

    // ── Dedicated multiplier for F_{p^4} inverter ──────────────────
    wire        inv_mult_start;
    wire [31:0] inv_mult_a0, inv_mult_a1, inv_mult_a2, inv_mult_a3;
    wire [31:0] inv_mult_b0, inv_mult_b1, inv_mult_b2, inv_mult_b3;
    wire [31:0] inv_mult_r0, inv_mult_r1, inv_mult_r2, inv_mult_r3;
    wire        inv_mult_done, inv_mult_busy;

    spu13_m31_multiplier u_mult_inv (
        .clk(clk), .rst_n(rst_n),
        .start(inv_mult_start),
        .a0(inv_mult_a0), .a1(inv_mult_a1), .a2(inv_mult_a2), .a3(inv_mult_a3),
        .b0(inv_mult_b0), .b1(inv_mult_b1), .b2(inv_mult_b2), .b3(inv_mult_b3),
        .r0(inv_mult_r0), .r1(inv_mult_r1), .r2(inv_mult_r2), .r3(inv_mult_r3),
        .done(inv_mult_done), .busy(inv_mult_busy)
    );

    // ── F_{p^4} Conjugate Reduction Tower Inverter ─────────────────
    spu13_fp4_inverter u_inverter (
        .clk(clk), .rst_n(rst_n),
        .start(inv_start_w),
        .z0(inv_z0_w), .z1(inv_z1_w), .z2(inv_z2_w), .z3(inv_z3_w),
        .inv0(inv_r0_w), .inv1(inv_r1_w), .inv2(inv_r2_w), .inv3(inv_r3_w),
        .done(inv_done_w), .busy(inv_busy_w),
        .flags_v(inv_flags_v),
        .mult_start(inv_mult_start),
        .mult_a0(inv_mult_a0), .mult_a1(inv_mult_a1),
        .mult_a2(inv_mult_a2), .mult_a3(inv_mult_a3),
        .mult_b0(inv_mult_b0), .mult_b1(inv_mult_b1),
        .mult_b2(inv_mult_b2), .mult_b3(inv_mult_b3),
        .mult_r0(inv_mult_r0), .mult_r1(inv_mult_r1),
        .mult_r2(inv_mult_r2), .mult_r3(inv_mult_r3),
        .mult_done(inv_mult_done), .mult_busy(inv_mult_busy)
    );

    wire pade_launch = phi2_valid && !pade_inflight && !pade_busy && !pade_done;

    // ── Pipeline stage advancement ─────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phi1_valid <= 1'b0;
            phi2_valid <= 1'b0;
            phi3_valid <= 1'b0;
            phi4_valid <= 1'b0;
            som_active <= 1'b0;
            pade_inflight <= 1'b0;
            quadray_pending <= 2'b00;
            phi2_c0 <= 32'd0; phi2_c1 <= 32'd0;
            phi2_c2 <= 32'd0; phi2_c3 <= 32'd0;
            phi3_c0 <= 32'd0; phi3_c1 <= 32'd0;
            phi3_c2 <= 32'd0; phi3_c3 <= 32'd0;
            phi4_c0 <= 32'd0; phi4_c1 <= 32'd0;
            phi4_c2 <= 32'd0; phi4_c3 <= 32'd0;
        end else begin
            if (som_start)
                som_active <= 1'b1;
            else if (som_done)
                som_active <= 1'b0;

            quadray_pending <= {quadray_pending[0], btu_valid};

            // Default: advance pipeline if not stalled
            if (!btu_stall && !pade_busy) begin
                // Φ₁ → Φ₂: latch BTU output when valid
                phi2_valid <= btu_valid;
                if (btu_valid) begin
                    phi2_c0 <= btu_c0; phi2_c1 <= btu_c1;
                    phi2_c2 <= btu_c2; phi2_c3 <= btu_c3;
                end

                // Φ₂ → Φ₃: launch Padé once per latched saddle point.
                if (pade_launch) begin
                    phi2_valid <= 1'b0;
                    phi3_valid <= 1'b1;
                    phi3_c0 <= phi2_c0; phi3_c1 <= phi2_c1;
                    phi3_c2 <= phi2_c2; phi3_c3 <= phi2_c3;
                    pade_inflight <= 1'b1;
                end

                // Φ₃ → Φ₄: latch Padé result
                phi4_valid <= pade_done;
                if (pade_done) begin
                    phi4_c0 <= pade_result_c0; phi4_c1 <= pade_result_c1;
                    phi4_c2 <= pade_result_c2; phi4_c3 <= pade_result_c3;
                    pade_inflight <= 1'b0;
                end
            end

            // Clear valids on consumption
            if (btu_valid)  phi1_valid <= 1'b0;
            if (btu_stall)  phi1_valid <= phi1_valid;  // hold
            if (pade_done) begin
                phi2_valid <= 1'b0;
                phi3_valid <= 1'b0;
                pade_inflight <= 1'b0;
            end
        end
    end

    // Drive Padé start from pipeline advancement
    assign pade_start = pade_launch;

    // ── Outputs ─────────────────────────────────────────────────────
    assign thimble_c0    = phi4_c0;
    assign thimble_c1    = phi4_c1;
    assign thimble_c2    = phi4_c2;
    assign thimble_c3    = phi4_c3;
    assign thimble_valid = phi4_valid;
    assign quadray_delta = quadray_delta_w;
    assign quadray_coherent = quadray_coherent_w;
    assign quadray_valid = quadray_valid_w;
    assign pipeline_busy = som_active || bmu_valid || btu_valid ||
                           pade_inflight || pade_busy || inv_busy_w ||
                           (|quadray_pending) || quadray_valid_w;
    assign pipeline_stall = btu_stall;

endmodule
