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
    parameter WIDTH        = 18,
    parameter EXTERNAL_PADE_MULT = 0,
    parameter SHARE_PADE_INV_MULT = 0
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
    input  wire         btu_cfg_we,
    input  wire [5:0]   btu_cfg_addr,
    input  wire         btu_cfg_pair,
    input  wire [63:0]  btu_cfg_data,
    input  wire [31:0]  quadray_target_kappa,

    // ── Φ₄: Final output ───────────────────────────────────────────
    output wire [31:0]  thimble_c0, thimble_c1, thimble_c2, thimble_c3,
    output wire         thimble_valid,
    output wire [31:0]  quadray_delta,
    output wire         quadray_coherent,
    output wire         quadray_valid,
    output wire         pipeline_busy,
    output wire         pipeline_stall,
    output wire         rns_error,        // M31 mod-3 residue parity violation

    // Optional external Padé multiplier interface. When EXTERNAL_PADE_MULT=0,
    // these request outputs are held inactive and an internal multiplier is used.
    output wire         pade_mult_start,
    output wire [31:0]  pade_mult_a0, pade_mult_a1, pade_mult_a2, pade_mult_a3,
    output wire [31:0]  pade_mult_b0, pade_mult_b1, pade_mult_b2, pade_mult_b3,
    input  wire [31:0]  pade_mult_r0, pade_mult_r1, pade_mult_r2, pade_mult_r3,
    input  wire         pade_mult_done,
    input  wire         pade_mult_busy,
    input  wire         pade_mult_rns_error
);

    // ── Φ₁ → Φ₂ interconnect ──────────────────────────────────────
    wire        bmu_done, bmu_valid;
    wire [15:0] bmu_best_id;
    wire [63:0] bmu_best_q;
    wire [15:0] bmu_cluster_label;
    wire        som_start_accept;

    // ── Φ₁ latch: hold BMU result through BTU stall ──────────────
    reg         phi1_valid;
    reg  [5:0]  phi1_best_id;

    // Convert latched BMU best_id to 64-bit one-hot for BTU
    wire [63:0] btu_activation;
    assign btu_activation = (phi1_valid) ? (64'd1 << phi1_best_id) : 64'd0;

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
    wire        mult_done_w, mult_busy_w, mult_rns_error_w;
    wire [31:0] mult_local_r0, mult_local_r1, mult_local_r2, mult_local_r3;
    wire        mult_local_done, mult_local_busy, mult_local_rns_error;

    // ── A31 inverter interface ─────────────────────────────────────
    wire        inv_start_w;
    wire [31:0] inv_z0_w, inv_z1_w, inv_z2_w, inv_z3_w;
    wire [31:0] inv_r0_w, inv_r1_w, inv_r2_w, inv_r3_w;
    wire        inv_done_w, inv_busy_w, inv_flags_v;
    wire        pade_flags_v;

    // ── Pipeline stage latches ─────────────────────────────────────
    reg         phi3_valid, phi4_valid;
    reg         som_active;
    reg         pade_inflight;
    reg [3:0]  quadray_pending;
    reg [31:0]  phi3_c0, phi3_c1, phi3_c2, phi3_c3;
    reg [31:0]  phi4_c0, phi4_c1, phi4_c2, phi4_c3;

    // BTU can serialize up to 64 simultaneous collision rows. Padé is much
    // slower, so the handoff needs a real queue, not a single Φ₂ latch.
    localparam BTU_FIFO_DEPTH = 64;
    localparam BTU_FIFO_PTR_W = 6;
    localparam BTU_FIFO_CNT_W = 7;
    localparam [BTU_FIFO_CNT_W-1:0] BTU_FIFO_DEPTH_COUNT = BTU_FIFO_DEPTH;

    reg [31:0] btu_fifo_c0 [0:BTU_FIFO_DEPTH-1];
    reg [31:0] btu_fifo_c1 [0:BTU_FIFO_DEPTH-1];
    reg [31:0] btu_fifo_c2 [0:BTU_FIFO_DEPTH-1];
    reg [31:0] btu_fifo_c3 [0:BTU_FIFO_DEPTH-1];
    reg [BTU_FIFO_PTR_W-1:0] btu_fifo_wr_ptr;
    reg [BTU_FIFO_PTR_W-1:0] btu_fifo_rd_ptr;
    reg [BTU_FIFO_CNT_W-1:0] btu_fifo_count;
    reg                      btu_fifo_overflow;

    wire pade_launch;
    wire btu_fifo_push;
    wire btu_fifo_empty = (btu_fifo_count == {BTU_FIFO_CNT_W{1'b0}});
    wire btu_fifo_full  = (btu_fifo_count == BTU_FIFO_DEPTH_COUNT);
    wire [31:0] btu_fifo_head_c0 = btu_fifo_c0[btu_fifo_rd_ptr];
    wire [31:0] btu_fifo_head_c1 = btu_fifo_c1[btu_fifo_rd_ptr];
    wire [31:0] btu_fifo_head_c2 = btu_fifo_c2[btu_fifo_rd_ptr];
    wire [31:0] btu_fifo_head_c3 = btu_fifo_c3[btu_fifo_rd_ptr];
    wire [31:0] pade_saddle_c0 = pade_launch ? btu_fifo_head_c0 : phi3_c0;
    wire [31:0] pade_saddle_c1 = pade_launch ? btu_fifo_head_c1 : phi3_c1;
    wire [31:0] pade_saddle_c2 = pade_launch ? btu_fifo_head_c2 : phi3_c2;
    wire [31:0] pade_saddle_c3 = pade_launch ? btu_fifo_head_c3 : phi3_c3;
    localparam [WIDTH-1:0] SOM_WEIGHT_ZERO = {WIDTH{1'b0}};
    localparam [WIDTH-1:0] SOM_WEIGHT_ONE  = {{(WIDTH-1){1'b0}}, 1'b1};

    // ── Φ₁: Kohonen SOM BMU ───────────────────────────────────────
    spu_som_bmu #(
        .NUM_FEATURES(NUM_FEATURES),
        .MAX_NODES(MAX_NODES),
        .WIDTH(WIDTH)
    ) u_som (
        .clk(clk), .rst_n(rst_n),
        .start(som_start_accept),
        .done(som_done),
        .features(som_features),
        .feature_weights({NUM_FEATURES{SOM_WEIGHT_ONE, SOM_WEIGHT_ZERO}}),
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
        .train_be({NUM_FEATURES{1'b0}}),
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
        .cfg_we(btu_cfg_we),
        .cfg_addr(btu_cfg_addr),
        .cfg_pair(btu_cfg_pair),
        .cfg_data(btu_cfg_data),
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
        .saddle_c0(pade_saddle_c0), .saddle_c1(pade_saddle_c1),
        .saddle_c2(pade_saddle_c2), .saddle_c3(pade_saddle_c3),
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

    assign pade_mult_start = (EXTERNAL_PADE_MULT != 0) ? mult_start_w : 1'b0;
    assign pade_mult_a0 = mult_a0_w;
    assign pade_mult_a1 = mult_a1_w;
    assign pade_mult_a2 = mult_a2_w;
    assign pade_mult_a3 = mult_a3_w;
    assign pade_mult_b0 = mult_b0_w;
    assign pade_mult_b1 = mult_b1_w;
    assign pade_mult_b2 = mult_b2_w;
    assign pade_mult_b3 = mult_b3_w;

    assign mult_r0_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_r0 : mult_local_r0;
    assign mult_r1_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_r1 : mult_local_r1;
    assign mult_r2_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_r2 : mult_local_r2;
    assign mult_r3_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_r3 : mult_local_r3;
    assign mult_done_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_done : mult_local_done;
    assign mult_busy_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_busy : mult_local_busy;
    assign mult_rns_error_w = (EXTERNAL_PADE_MULT != 0) ? pade_mult_rns_error : mult_local_rns_error;

    // ── A31 inverter multiplier request/response wires ─────────────
    wire        inv_mult_start;
    wire [31:0] inv_mult_a0, inv_mult_a1, inv_mult_a2, inv_mult_a3;
    wire [31:0] inv_mult_b0, inv_mult_b1, inv_mult_b2, inv_mult_b3;
    wire [31:0] inv_mult_r0, inv_mult_r1, inv_mult_r2, inv_mult_r3;
    wire        inv_mult_done, inv_mult_busy, inv_mult_rns_error;

    // ── Padé/inverter multiplier bank ──────────────────────────────
    // The Padé Horner/final-multiply phases and the inverter phase are
    // sequential, so dense board spins can share one M31 multiplier between
    // them.  External Padé mode keeps the inverter multiplier dedicated.
    generate
        if (SHARE_PADE_INV_MULT != 0 && EXTERNAL_PADE_MULT == 0) begin : gen_shared_pade_inv_mult
            wire        shared_start;
            wire [31:0] shared_a0, shared_a1, shared_a2, shared_a3;
            wire [31:0] shared_b0, shared_b1, shared_b2, shared_b3;
            wire [31:0] shared_r0, shared_r1, shared_r2, shared_r3;
            wire        shared_done, shared_busy, shared_rns_error;

            assign shared_start = inv_mult_start ? inv_mult_start : mult_start_w;
            assign shared_a0 = inv_mult_start ? inv_mult_a0 : mult_a0_w;
            assign shared_a1 = inv_mult_start ? inv_mult_a1 : mult_a1_w;
            assign shared_a2 = inv_mult_start ? inv_mult_a2 : mult_a2_w;
            assign shared_a3 = inv_mult_start ? inv_mult_a3 : mult_a3_w;
            assign shared_b0 = inv_mult_start ? inv_mult_b0 : mult_b0_w;
            assign shared_b1 = inv_mult_start ? inv_mult_b1 : mult_b1_w;
            assign shared_b2 = inv_mult_start ? inv_mult_b2 : mult_b2_w;
            assign shared_b3 = inv_mult_start ? inv_mult_b3 : mult_b3_w;

            spu13_m31_multiplier u_mult_shared (
                .clk(clk), .rst_n(rst_n),
                .start(shared_start),
                .a0(shared_a0), .a1(shared_a1),
                .a2(shared_a2), .a3(shared_a3),
                .b0(shared_b0), .b1(shared_b1),
                .b2(shared_b2), .b3(shared_b3),
                .r0(shared_r0), .r1(shared_r1),
                .r2(shared_r2), .r3(shared_r3),
                .done(shared_done), .busy(shared_busy),
                .rns_error(shared_rns_error)
            );

            assign mult_local_r0 = shared_r0;
            assign mult_local_r1 = shared_r1;
            assign mult_local_r2 = shared_r2;
            assign mult_local_r3 = shared_r3;
            assign mult_local_done = shared_done;
            assign mult_local_busy = shared_busy;
            assign mult_local_rns_error = shared_rns_error;

            assign inv_mult_r0 = shared_r0;
            assign inv_mult_r1 = shared_r1;
            assign inv_mult_r2 = shared_r2;
            assign inv_mult_r3 = shared_r3;
            assign inv_mult_done = shared_done;
            assign inv_mult_busy = shared_busy;
            assign inv_mult_rns_error = shared_rns_error;
        end else begin : gen_external_pade_mult
            if (EXTERNAL_PADE_MULT == 0) begin : gen_internal_pade_mult
                spu13_m31_multiplier u_mult_pade (
                    .clk(clk), .rst_n(rst_n),
                    .start(mult_start_w),
                    .a0(mult_a0_w), .a1(mult_a1_w),
                    .a2(mult_a2_w), .a3(mult_a3_w),
                    .b0(mult_b0_w), .b1(mult_b1_w),
                    .b2(mult_b2_w), .b3(mult_b3_w),
                    .r0(mult_local_r0), .r1(mult_local_r1),
                    .r2(mult_local_r2), .r3(mult_local_r3),
                    .done(mult_local_done), .busy(mult_local_busy),
                    .rns_error(mult_local_rns_error)
                );
            end else begin : gen_no_internal_pade_mult
                assign mult_local_r0 = 32'd0;
                assign mult_local_r1 = 32'd0;
                assign mult_local_r2 = 32'd0;
                assign mult_local_r3 = 32'd0;
                assign mult_local_done = 1'b0;
                assign mult_local_busy = 1'b0;
                assign mult_local_rns_error = 1'b0;
            end

            spu13_m31_multiplier u_mult_inv (
                .clk(clk), .rst_n(rst_n),
                .start(inv_mult_start),
                .a0(inv_mult_a0), .a1(inv_mult_a1),
                .a2(inv_mult_a2), .a3(inv_mult_a3),
                .b0(inv_mult_b0), .b1(inv_mult_b1),
                .b2(inv_mult_b2), .b3(inv_mult_b3),
                .r0(inv_mult_r0), .r1(inv_mult_r1),
                .r2(inv_mult_r2), .r3(inv_mult_r3),
                .done(inv_mult_done), .busy(inv_mult_busy),
                .rns_error(inv_mult_rns_error)
            );
        end
    endgenerate

    // ── A31 Conjugate Reduction Tower Inverter ─────────────────────
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
        .mult_done(inv_mult_done), .mult_busy(inv_mult_busy),
        .debug_state(), .debug_start_accept()
    );

    assign pade_launch = !btu_fifo_empty && !pade_inflight && !pade_busy && !pade_done;
    assign btu_fifo_push = btu_valid && (!btu_fifo_full || pade_launch);
    assign som_start_accept = som_start && !pipeline_busy;

    // ── Pipeline stage advancement ─────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phi1_valid <= 1'b0;
            phi1_best_id <= 6'd0;
            phi3_valid <= 1'b0;
            phi4_valid <= 1'b0;
            som_active <= 1'b0;
            pade_inflight <= 1'b0;
            quadray_pending <= 4'b0000;
            phi3_c0 <= 32'd0; phi3_c1 <= 32'd0;
            phi3_c2 <= 32'd0; phi3_c3 <= 32'd0;
            phi4_c0 <= 32'd0; phi4_c1 <= 32'd0;
            phi4_c2 <= 32'd0; phi4_c3 <= 32'd0;
            btu_fifo_wr_ptr <= {BTU_FIFO_PTR_W{1'b0}};
            btu_fifo_rd_ptr <= {BTU_FIFO_PTR_W{1'b0}};
            btu_fifo_count <= {BTU_FIFO_CNT_W{1'b0}};
            btu_fifo_overflow <= 1'b0;
        end else begin
            phi4_valid <= 1'b0;

            if (som_start_accept)
                som_active <= 1'b1;
            else if (som_done)
                som_active <= 1'b0;

            // ── Φ₁: Capture BMU result ───────────────────────────
            if (bmu_valid) begin
                phi1_valid <= 1'b1;
                phi1_best_id <= bmu_best_id[5:0];
            end

            // ── Φ₂: Capture BTU output into the Padé input FIFO ───
            if (btu_valid) begin
                if (btu_fifo_push) begin
                    btu_fifo_c0[btu_fifo_wr_ptr] <= btu_c0;
                    btu_fifo_c1[btu_fifo_wr_ptr] <= btu_c1;
                    btu_fifo_c2[btu_fifo_wr_ptr] <= btu_c2;
                    btu_fifo_c3[btu_fifo_wr_ptr] <= btu_c3;
                    btu_fifo_wr_ptr <= btu_fifo_wr_ptr + 1'b1;
                    // Clear sticky overflow on successful push
                    btu_fifo_overflow <= 1'b0;
                end else begin
                    // FIFO full and no launch: sticky overflow
                    btu_fifo_overflow <= 1'b1;
                end
            end else begin
                // If no incoming valid this cycle and FIFO not full, clear overflow
                if (btu_fifo_count != BTU_FIFO_DEPTH_COUNT)
                    btu_fifo_overflow <= 1'b0;
            end

            // ── quadray_pending: shift register for pending ────────────
            quadray_pending <= {quadray_pending[2:0], btu_valid};

            if (phi1_valid && !btu_stall)
                phi1_valid <= 1'b0;

            // Φ₂ FIFO → Φ₃: launch Padé exactly when a FIFO element is popped.
            if (pade_launch) begin
                btu_fifo_rd_ptr <= btu_fifo_rd_ptr + 1'b1;
                phi3_valid <= 1'b1;
                phi3_c0 <= btu_fifo_head_c0; phi3_c1 <= btu_fifo_head_c1;
                phi3_c2 <= btu_fifo_head_c2; phi3_c3 <= btu_fifo_head_c3;
                pade_inflight <= 1'b1;
            end

            case ({btu_fifo_push, pade_launch})
                2'b10: btu_fifo_count <= btu_fifo_count + 1'b1;
                2'b01: btu_fifo_count <= btu_fifo_count - 1'b1;
                default: btu_fifo_count <= btu_fifo_count;
            endcase

            // Φ₃ → Φ₄: latch Padé result independently of BTU stall state.
            if (pade_done) begin
                phi4_valid <= 1'b1;
                phi4_c0 <= pade_result_c0; phi4_c1 <= pade_result_c1;
                phi4_c2 <= pade_result_c2; phi4_c3 <= pade_result_c3;
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
    assign rns_error = mult_rns_error_w || inv_mult_rns_error;
    assign pipeline_busy = som_active || phi1_valid || btu_valid || btu_stall ||
                           (btu_fifo_count != {BTU_FIFO_CNT_W{1'b0}}) ||
                           phi3_valid || pade_inflight || pade_busy ||
                           mult_busy_w || inv_busy_w || btu_fifo_overflow ||
                           (|quadray_pending) || quadray_valid_w;
    assign pipeline_stall = btu_stall;

endmodule
