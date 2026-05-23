// SPU-13 Sovereign Core (v1.7 - Strictly Phi-Gated TDM)
// Objective: 13-axis Manifold via Fibonacci-Synchronized Pipeline.
// Architecture: TDM Davis Law Gasket + SQR Rotor Vault + Artery Interface.

`include "spu_arch_defines.vh"

module spu13_core #(
    parameter DEVICE = "GW2A",  // "GW1N" | "GW2A" | "GW5A" | "SIM"
    parameter ENABLE_RPLU = 1,
    parameter ENABLE_LATTICE = 1,
    parameter ENABLE_MATH = 1
)(
    input  wire         clk,            // Fast Clock (e.g. 12-24MHz)
    input  wire         rst_n,

    // Fibonacci Timing Pulses
    input  wire         phi_8,          // Fetch Pulse
    input  wire         phi_13,         // Compute Pulse
    input  wire         phi_21,         // Commit Pulse

    // RPLU fast-domain cfg inputs
    input  wire         dec_fast_cfg_wr_en,
    input  wire [2:0]   dec_fast_cfg_sel,
    input  wire [7:0]   dec_fast_cfg_material,
    input  wire [9:0]   dec_fast_cfg_addr,
    input  wire [63:0]  dec_fast_cfg_data,
    // Phinary config (bits: [0]=enable, [1]=chirality)
    input  wire [15:0]  phinary_cfg,

    // Prime Hydration Interface (from Bootloader)
    input  wire [23:0]  prime_data,
    input  wire [3:0]   prime_addr,
    input  wire         prime_we,
    input  wire         boot_done,
    input  wire [31:0]  pell_data,
    input  wire [2:0]   pell_addr,
    input  wire         pell_we,

    // Manual Rotor Interface (Interaction)
    input  wire         manual_rotor_en,
    input  wire [63:0]  manual_rotor_data,

    // Sovereign Memory Interface
    `MANIFOLD_SIGS,

    // 13-Axis Manifold Snapshot (for Artery TX)
    // Artery writer outputs (one-cycle pulse + 64-bit chord) — driven by core when it emits a chord
    output reg                    artery_wr_en,
    output reg [63:0]             artery_wr_data,

    output wire [3:0]   current_axis_ptr,
    output wire [63:0]  current_axis_data,

    // Instruction input (optional). When unused, tie inst_valid=0 at instantiation.
    input  wire                    inst_valid,
    input  wire [63:0]             inst_word,

    // RPLU comparator outputs (fast domain)
    output wire signed [2:0]       ratio_cmp_res,
    output wire                    ratio_cmp_valid,

    output wire [`MANIFOLD_WIDTH-1:0] manifold_out,
    output wire                      bloom_complete,
    output wire [(`MANIFOLD_AXES*4)-1:0] scale_table_out,
    output wire [`MANIFOLD_AXES-1:0]      scale_overflow_out,
    output reg                       is_janus_point,

    // Proprioception exports
    output reg [1:0]                 audio_mode,
    output wire [15:0]               gasket_sum_out,
    output wire [31:0]               quadrance_out,
    output wire                      cycle_wrap,
    output wire                      rplu_dissoc_out,
    output wire [`MANIFOLD_AXES-1:0] rplu_dissoc_mask_out,
    output wire [9:0]                rplu_addr_out
);

    // 1. Manifold State Buffering
    // Keep the live manifold as explicit 64-bit lanes so boot hydration and
    // axis commits compile into narrow per-lane enables rather than a single
    // wide indexed write across the entire 832-bit slab.
    reg [63:0] manifold_lane [0:(`MANIFOLD_AXES-1)];
    wire [`MANIFOLD_WIDTH-1:0] manifold_reg;

    assign manifold_reg = {
        manifold_lane[12], manifold_lane[11], manifold_lane[10], manifold_lane[9],
        manifold_lane[8],  manifold_lane[7],  manifold_lane[6],  manifold_lane[5],
        manifold_lane[4],  manifold_lane[3],  manifold_lane[2],  manifold_lane[1],
        manifold_lane[0]
    };
    assign manifold_out = annealed_manifold;

    // ── Isotropic Annealer (Golden-Noise Lattice Unlock) ────────────
    // Injects sub-Planckian φ-noise when the full manifold is laminar
    // for 16 consecutive cycles — prevents frozen lattice-lock.
    wire [831:0] annealed_manifold;
    reg          anneal_enable;
    reg [4:0]    laminar_cycle_count;

    spu_annealer u_annealer (
        .clk(clk), .reset(!rst_n),
        .enable(anneal_enable),
        .reg_in(manifold_reg),
        .reg_out(annealed_manifold)
    );

    // Laminar persistence detector: fires annealer after 16 stable cycles
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            laminar_cycle_count <= 0;
            anneal_enable <= 0;
        end else begin
            anneal_enable <= 0;
            if (is_janus_point) begin
                if (laminar_cycle_count < 16)
                    laminar_cycle_count <= laminar_cycle_count + 1;
                else begin
                    anneal_enable <= 1;       // fire φ-perturbation
                    laminar_cycle_count <= 0;
                end
            end else begin
                laminar_cycle_count <= 0;
            end
        end
    end

    // ── Active Inference (Predictive Coding Filter) ─────────────────
    // Filters transient cubic leaks from genuine manifold divergence
    // using the Free Energy Principle. Prior is the last manifold frame;
    // sensory input is the current frame. Dissonance flags real events.
    wire [127:0] inference_posterior;
    wire [127:0] inference_error;
    wire         inference_dissonant;
    reg          fault_pulse_d1;  // delayed fault to align with manifold

    spu_active_inference u_inference (
        .clk(clk), .reset(!rst_n),
        .prior_state(manifold_reg[127:0]),       // low 128 bits of manifold
        .prior_precision(adaptive_tau_q[15:0]),  // from soul metabolism
        .sensory_in(manifold_commit_reg[127:0]),
        .sensory_valid(phi_21),
        .posterior_state(inference_posterior),
        .prediction_error(inference_error),
        .is_dissonant(inference_dissonant)
    );

    // ── Soul Metabolism (Adaptive Safety Valve) ─────────────────────
    // Tracks fault rate and adjusts Davis Gate sensitivity (adaptive_tau).
    // Widens tau when tuck rate > 13% (Fibonacci threshold), tightens
    // when stable. Periodically saves health state to SPI flash.
    wire [31:0] adaptive_tau_q;
    wire [31:0] soul_tuck_count, soul_cycle_count;
    wire        soul_flash_we;
    wire [23:0] soul_flash_addr;
    wire [255:0] soul_flash_page;

    // ── Viscosity Monitor ─────────────────────────────────────────
    // Measures manifold flow quality: 0xFF = liquid, 0x00 = cubic friction.
    wire [7:0] laminar_flow_index;

    spu_viscosity_monitor u_viscosity (
        .clk(clk), .reset(!rst_n),
        .abcd_vector(manifold_reg[127:0]),
        .laminar_flow_index(laminar_flow_index)
    );

    // ── I2S Audio Output ──────────────────────────────────────────
    // Converts Davis Gate audio surds to I2S protocol for PCM5102A DAC.
    wire        i2s_bclk, i2s_lrclk, i2s_dout;

    spu_i2s_out u_i2s (
        .clk(clk), .rst_n(rst_n),
        .mode(2'b01),               // passthrough mode
        .lfi(laminar_flow_index),
        .left_data(audio_p[23:0]),
        .right_data(audio_q[23:0]),
        .i2s_bclk(i2s_bclk),
        .i2s_lrclk(i2s_lrclk),
        .i2s_dout(i2s_dout)
    );

    // ── Toroidal Register File (Manifold Frame Buffer) ────────────
    // 832-bit × 8-entry rotating buffer. Stores manifold snapshots
    // on each axis-wrap for history comparison and Artery distribution.
    wire [831:0] torus_rd_data;
    reg          torus_wr_en;
    reg  [2:0]   torus_wr_addr;

    toroidal_regfile #(.WIDTH(832), .NUM(8)) u_torus (
        .clk(clk), .rst_n(rst_n),
        .wr_en(torus_wr_en),
        .wr_addr(torus_wr_addr),
        .wr_data(manifold_commit_reg),
        .rd_en(1'b0),        // read port unused for now
        .rd_addr(3'd0),
        .rd_data(torus_rd_data),
        .rotate_start(1'b0), // rotate on demand
        .rotate_amount(32'd0),
        .rotate_idx(3'd0),
        .rotate_dir(1'b0),
        .method_sel(1'b0),
        .rotate_done()
    );

    // Write manifold frame on each axis-wrap
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            torus_wr_en <= 0;
            torus_wr_addr <= 0;
        end else begin
            torus_wr_en <= 0;
            if (cycle_wrap) begin
                torus_wr_en <= 1;
                torus_wr_addr <= torus_wr_addr + 1;  // ring buffer
            end
        end
    end

    spu_soul_metabolism #(.CLK_HZ(24_000_000)) u_metabolism (
        .clk(clk), .reset(!rst_n),
        .q_state(manifold_reg[127:0]),
        .fault_pulse(rplu_dissoc),
        .is_idle(~|stability_bits),     // idle when no axis is stable
        .adaptive_tau_q(adaptive_tau_q),
        .tuck_count(soul_tuck_count),
        .cycle_count(soul_cycle_count),
        .flash_we(soul_flash_we),
        .flash_addr(soul_flash_addr),
        .soul_page(soul_flash_page),
        .flash_ready(1'b0)               // SPI flash not ready in sim
    );

    function [`MANIFOLD_WIDTH-1:0] manifold_with_axis;
        input [`MANIFOLD_WIDTH-1:0] manifold_in;
        input [3:0] axis_idx;
        input [63:0] axis_value;
        begin
            manifold_with_axis = manifold_in;
            case (axis_idx)
                4'd0:  manifold_with_axis[63:0]    = axis_value;
                4'd1:  manifold_with_axis[127:64]  = axis_value;
                4'd2:  manifold_with_axis[191:128] = axis_value;
                4'd3:  manifold_with_axis[255:192] = axis_value;
                4'd4:  manifold_with_axis[319:256] = axis_value;
                4'd5:  manifold_with_axis[383:320] = axis_value;
                4'd6:  manifold_with_axis[447:384] = axis_value;
                4'd7:  manifold_with_axis[511:448] = axis_value;
                4'd8:  manifold_with_axis[575:512] = axis_value;
                4'd9:  manifold_with_axis[639:576] = axis_value;
                4'd10: manifold_with_axis[703:640] = axis_value;
                4'd11: manifold_with_axis[767:704] = axis_value;
                4'd12: manifold_with_axis[831:768] = axis_value;
                default: ;
            endcase
        end
    endfunction

    // 2. TDM Axis Pointer
    reg [3:0] axis_ptr;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) axis_ptr <= 0;
        else if (phi_21) begin
            axis_ptr <= (axis_ptr == 4'd12) ? 4'd0 : axis_ptr + 4'd1;
        end
    end

    reg [63:0] current_axis_data_mux;

    assign current_axis_ptr = axis_ptr;
    assign current_axis_data = current_axis_data_mux;

    always @(*) begin
        case (axis_ptr)
            4'd0:  current_axis_data_mux = manifold_lane[0];
            4'd1:  current_axis_data_mux = manifold_lane[1];
            4'd2:  current_axis_data_mux = manifold_lane[2];
            4'd3:  current_axis_data_mux = manifold_lane[3];
            4'd4:  current_axis_data_mux = manifold_lane[4];
            4'd5:  current_axis_data_mux = manifold_lane[5];
            4'd6:  current_axis_data_mux = manifold_lane[6];
            4'd7:  current_axis_data_mux = manifold_lane[7];
            4'd8:  current_axis_data_mux = manifold_lane[8];
            4'd9:  current_axis_data_mux = manifold_lane[9];
            4'd10: current_axis_data_mux = manifold_lane[10];
            4'd11: current_axis_data_mux = manifold_lane[11];
            4'd12: current_axis_data_mux = manifold_lane[12];
            default: current_axis_data_mux = 64'd0;
        endcase
    end

    // Phinary control exported from top-level config
    wire phinary_enable;
    assign phinary_enable = phinary_cfg[0];
    wire [7:0] phinary_chirality;
    assign phinary_chirality = phinary_cfg[8:1];

    // 3. Stage 1: Rotor & Axis Fetch (Pulse 8)
    // Vault v2.0: Pell Octave tracking — rot_en driven by sequencer pulse.
    // In SPU-13 context, ROT fires once per axis per sovereign cycle.
    wire [31:0] current_rotor;
    wire [7:0]  current_octave;
    wire [2:0]  current_step;
    generate
        if (ENABLE_MATH) begin : gen_rotor_vault
            spu_rotor_vault u_vault (
                .clk(clk),
                .reset(!rst_n),
                .axis_id(axis_ptr[3:0]),
                .rot_en(phi_8),         // advance one Pell orbit step during the fetch pulse
                .init_we(pell_we && !boot_done),
                .init_step(pell_addr),
                .init_rotor(pell_data),
                .rotor_out(current_rotor),
                .octave_out(current_octave),
                .step_out(current_step)
            );
        end else begin : gen_no_rotor_vault
            assign current_rotor = 32'h0001_0000;
            assign current_octave = 8'd0;
            assign current_step = 3'd0;
        end
    endgenerate

    // Scale raw Pell integers (from vault) to Q12 for the cross-rotor.
    // Steps 0-7: P in {1,2,7,26,97,362,1351,5042} — all fit in 32-bit Q12
    //            (max P*4096 = 5042*4096 = 20,652,032 < 2^25, safe in int32).
    wire [31:0] rotor_p_q12;
    assign rotor_p_q12 = {16'b0, current_rotor[31:16]} << 12;
    wire [31:0] rotor_q_q12;
    assign rotor_q_q12 = {16'b0, current_rotor[15:0]}  << 12;
    wire [63:0] rotor_q12_internal;
    assign rotor_q12_internal = {rotor_p_q12, rotor_q_q12};

    wire [63:0] rotor_q12;
    assign rotor_q12 = manual_rotor_en ? manual_rotor_data : rotor_q12_internal;

    // TDM lattice probe for the active axis. The original full lattice remains
    // available as a standalone module, but the core bring-up image keeps this
    // path phi-gated so the 25K target does not instantiate every node at once.
    wire [63:0] lattice_axis_out;
    wire [3:0]  lattice_axis_shift;
    wire        lattice_axis_overflow;

    generate
        if (ENABLE_LATTICE) begin : gen_lattice
            laminar_node #(.WIDTH(64)) u_lattice_axis (
                .clk(clk),
                .rst_n(rst_n),
                .enable(phinary_enable),
                .surd_in(current_axis_data),
                .surd_out(lattice_axis_out),
                .scale_shift(lattice_axis_shift),
                .scale_overflow(lattice_axis_overflow)
            );
        end else begin : gen_no_lattice
            assign lattice_axis_out = current_axis_data;
            assign lattice_axis_shift = 4'd0;
            assign lattice_axis_overflow = 1'b0;
        end
    endgenerate

    // Scale manager: stores per-axis normalization shifts and overflow flags
    wire [(`MANIFOLD_AXES*4)-1:0] scale_table;
    wire [`MANIFOLD_AXES-1:0]      overflow_table;
    reg scale_write_en;
    reg [3:0] scale_write_shift;
    reg       scale_write_overflow;

    rational_surd5_scale_manager #(.NODES(`MANIFOLD_AXES)) u_scale (
        .clk(clk),
        .rst_n(rst_n),
        .write_en(scale_write_en),
        .write_idx(axis_ptr),
        .write_shift(scale_write_shift),
        .write_overflow(scale_write_overflow),
        .scale_table(scale_table),
        .overflow_table(overflow_table)
    );

    assign scale_table_out = scale_table;
    assign scale_overflow_out = overflow_table;

    // Stage 2: The SQR Cross-Product (Pulse 13)
    // Manifold axis format: {A[31:0], B[31:0]} — full 64-bit axis is the surd.
    wire [63:0] q_prime_ab;
    generate
        if (ENABLE_MATH) begin : gen_cross_rotor
            spu_cross_rotor #(.DEVICE(DEVICE)) u_rotor (
                .clk(clk),
                .reset(!rst_n),
                .q_axis(current_axis_data),  // {A[31:0], B[31:0]} full axis
                .r_rotor(rotor_q12),         // Q12-scaled Pell rotor
                .q_prime(q_prime_ab)
            );
        end else begin : gen_no_cross_rotor
            assign q_prime_ab = current_axis_data;
        end
    endgenerate

    // ── Quadray Register File + ROTC Circulant ─────────────────────────
    // 13 registers × 4 components × 64 bits each = 3328 bits total.
    // Stores full (A,B,C,D) Quadray vectors for circulant rotation ops.
    wire [63:0] qrf_rd_A, qrf_rd_B, qrf_rd_C, qrf_rd_D;
    wire [63:0] qrf_wr_A, qrf_wr_B, qrf_wr_C, qrf_wr_D;
    reg         qrf_wr_en;
    reg  [3:0]  qrf_wr_lane;
    reg  [3:0]  qrf_init_lane;
    reg         rote_en;          // ROTC execute pulse
    reg  [5:0]  rote_angle;       // F,G,H angle (0-63)
    reg  [1:0]  rote_field;       // Q(√k) field: 00=√3, 01=√5, 10=√15
    reg  [3:0]  rote_src_lane;

    // F,G,H output from lookup
    wire signed [63:0] rote_F, rote_G, rote_H;
    // Rotated output from circulant (raw, before inverse permute)
    wire [63:0] rote_A_out_raw, rote_B_out_raw, rote_C_out_raw, rote_D_out_raw;
    // Rotated output after inverse permute (final writeback values)
    wire [63:0] rote_B_out, rote_C_out, rote_D_out;

    generate
        if (ENABLE_MATH) begin : gen_qrf
            // ── VE QR Hydration ──────────────────────────────────
            wire ve_qr_init_en;
            wire [3:0] ve_qr_init_lane;
            wire [63:0] ve_qr_init_A, ve_qr_init_B, ve_qr_init_C, ve_qr_init_D;
            wire ve_qr_init_done;

            spu_ve_qr_init u_ve_qr_init (
                .clk(clk), .rst_n(rst_n),
                .boot_done(boot_done),
                .init_en(ve_qr_init_en),
                .init_lane(ve_qr_init_lane),
                .init_A(ve_qr_init_A), .init_B(ve_qr_init_B),
                .init_C(ve_qr_init_C), .init_D(ve_qr_init_D),
                .init_done(ve_qr_init_done)
            );

            spu_quadray_regfile u_qrf (
                .clk(clk), .rst_n(rst_n),
                .rd_lane(rote_src_lane),
                .rd_A(qrf_rd_A), .rd_B(qrf_rd_B),
                .rd_C(qrf_rd_C), .rd_D(qrf_rd_D),
                .wr_en(qrf_wr_en),
                .wr_lane(qrf_wr_lane),
                .wr_A(qrf_wr_A), .wr_B(qrf_wr_B),
                .wr_C(qrf_wr_C), .wr_D(qrf_wr_D),
                .init_en(ve_qr_init_en), .init_lane(ve_qr_init_lane),
                .init_A(ve_qr_init_A), .init_B(ve_qr_init_B),
                .init_C(ve_qr_init_C), .init_D(ve_qr_init_D),
                .dbg_A(), .dbg_B(), .dbg_C(), .dbg_D()
            );

            // ── Quadray Permuter ──────────────────────────────────
            // For ROTC angles 6-11 (non-A-invariant rotations), permute
            // coordinates so the target axis becomes A, apply ROTC, then
            // un-permute back. Angles 0-5 are direct (A is invariant).
            wire [1:0] rote_perm_sel;
            wire [63:0] perm_A, perm_B, perm_C, perm_D;
            wire [63:0] rotor_A_in, rotor_B_in, rotor_C_in, rotor_D_in;

            // Angle → perm_sel: 0-5→id, 6-7→B→A, 8-9→C→A, 10-11→D→A
            assign rote_perm_sel = (rote_angle < 6) ? 2'b00 :
                                   (rote_angle < 8) ? 2'b01 :
                                   (rote_angle < 10) ? 2'b10 : 2'b11;

            spu_quadray_permute u_perm_fwd (
                .perm_sel(rote_perm_sel),
                .A_in(qrf_rd_A), .B_in(qrf_rd_B),
                .C_in(qrf_rd_C), .D_in(qrf_rd_D),
                .A_out(rotor_A_in), .B_out(rotor_B_in),
                .C_out(rotor_C_in), .D_out(rotor_D_in)
            );

            spu13_rotor_core u_rotc (
                .clk(clk), .rst_n(rst_n),
                .A_in(rotor_A_in),
                .B_in(rotor_B_in),
                .C_in(rotor_C_in),
                .D_in(rotor_D_in),
                .F(rote_F), .G(rote_G), .H(rote_H),
                .field_sel(rote_field),
                .bypass_p5(rote_angle == 6'd2),  // 120° → pure permutation
                .A_out(rote_A_out_raw),
                .B_out(rote_B_out_raw),
                .C_out(rote_C_out_raw),
                .D_out(rote_D_out_raw)
            );

            // ── Inverse Permuter ───────────────────────────────────
            // Undo the coordinate permutation for angles 6-11.
            // inv(00)=00, inv(01)=11, inv(10)=10, inv(11)=01
            wire [1:0] rote_inv_sel;
            assign rote_inv_sel = (rote_perm_sel == 2'b01) ? 2'b11 :
                                  (rote_perm_sel == 2'b11) ? 2'b01 :
                                  rote_perm_sel;

            spu_quadray_permute u_perm_inv (
                .perm_sel(rote_inv_sel),
                .A_in(rote_A_out_raw), .B_in(rote_B_out_raw),
                .C_in(rote_C_out_raw), .D_in(rote_D_out_raw),
                .A_out(qrf_wr_A), .B_out(rote_B_out),
                .C_out(rote_C_out), .D_out(rote_D_out)
            );

            // Write-back: A is invariant, B',C',D' come from circulant
            assign qrf_wr_B = rote_B_out;
            assign qrf_wr_C = rote_C_out;
            assign qrf_wr_D = rote_D_out;
        end else begin : gen_no_qrf
            assign qrf_rd_A = 64'd0; assign qrf_rd_B = 64'd0;
            assign qrf_rd_C = 64'd0; assign qrf_rd_D = 64'd0;
            assign qrf_wr_A = 64'd0; assign qrf_wr_B = 64'd0;
            assign qrf_wr_C = 64'd0; assign qrf_wr_D = 64'd0;
            assign rote_B_out = 64'd0; assign rote_C_out = 64'd0;
            assign rote_D_out = 64'd0;
            assign rote_F = 64'd0; assign rote_G = 64'd0; assign rote_H = 64'd0;
        end
    endgenerate

    // ── F,G,H lookup table (combinational) ─────────────────────────────
    // Identical to VM _ROTC_TABLE. Scaled by denominator 3 for tetrahedral
    // angles; the rotor core handles the /3 scaling internally via
    // fixed-point truncation in the surd multiplier path.
    // Extended entries (6-63) are populated at hydration time from flash;
    // the combinational default returns identity (F=1, G=0, H=0) for
    // unpopulated entries.
    assign rote_F = (rote_angle == 6'd0)  ? 64'sd1  :
                    (rote_angle == 6'd1)  ? 64'sd2  :
                    (rote_angle == 6'd2)  ? -64'sd1 :
                    (rote_angle == 6'd3)  ? -64'sd1 :
                    (rote_angle == 6'd4)  ? 64'sd2  :
                    (rote_angle == 6'd5)  ? 64'sd2  :
                    // Extended entries 6-11 (A₄ group) — same F,G,H patterns
                    (rote_angle == 6'd6)  ? 64'sd2  :
                    (rote_angle == 6'd7)  ? 64'sd2  :
                    (rote_angle == 6'd8)  ? -64'sd1 :
                    (rote_angle == 6'd9)  ? 64'sd2  :
                    (rote_angle == 6'd10) ? 64'sd2  :
                    (rote_angle == 6'd11) ? -64'sd1 :
                    // Entries 12-63: identity fallback (flash-load for actual values)
                    64'sd1;

    assign rote_G = (rote_angle == 6'd0)  ? 64'sd0  :
                    (rote_angle == 6'd1)  ? 64'sd2  :
                    (rote_angle == 6'd2)  ? 64'sd2  :
                    (rote_angle == 6'd3)  ? -64'sd1 :
                    (rote_angle == 6'd4)  ? -64'sd1 :
                    (rote_angle == 6'd5)  ? 64'sd2  :
                    // Extended entries
                    (rote_angle == 6'd6)  ? -64'sd1 :
                    (rote_angle == 6'd7)  ? 64'sd2  :
                    (rote_angle == 6'd8)  ? 64'sd2  :
                    (rote_angle == 6'd9)  ? 64'sd2  :
                    (rote_angle == 6'd10) ? -64'sd1 :
                    (rote_angle == 6'd11) ? 64'sd2  :
                    64'sd0;

    assign rote_H = (rote_angle == 6'd0)  ? 64'sd0  :
                    (rote_angle == 6'd1)  ? -64'sd1 :
                    (rote_angle == 6'd2)  ? 64'sd2  :
                    (rote_angle == 6'd3)  ? -64'sd1 :
                    (rote_angle == 6'd4)  ? 64'sd2  :
                    (rote_angle == 6'd5)  ? -64'sd1 :
                    // Extended entries
                    (rote_angle == 6'd6)  ? 64'sd2  :
                    (rote_angle == 6'd7)  ? -64'sd1 :
                    (rote_angle == 6'd8)  ? 64'sd2  :
                    (rote_angle == 6'd9)  ? -64'sd1 :
                    (rote_angle == 6'd10) ? 64'sd2  :
                    (rote_angle == 6'd11) ? 64'sd2  :
                    64'sd0;

    // ── ROTC execution FSM ─────────────────────────────────────────────
    // On ROTC instruction (0x1C): latch source/dest/angle, fire rote_en.
    // The QR register file reads the source lane combinationally,
    // the rotor core computes the circulant, and we write back on the
    // next cycle.
    reg rote_active;
    reg [3:0] rote_dest_lane;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rote_en <= 0;
            rote_active <= 0;
            rote_src_lane <= 0;
            rote_dest_lane <= 0;
            rote_angle <= 6'd0;
            rote_field <= 2'b00;
            qrf_wr_en <= 0;
            qrf_wr_lane <= 0;
        end else begin
            qrf_wr_en <= 0;  // default: no write

            // ── QLDI Handler (0x1D) ────────────────────────────────
            // QLDI QRd, A, B, C, D — load integer Quadray from immediate.
            // P1_A[15:8]=A, P1_A[7:0]=B, P1_B[15:8]=C, P1_B[7:0]=D
            // Each component is sign-extended from 8-bit to 64-bit surd
            // with Q=0 (pure rational, no √3 component).
            if (inst_valid && inst_word[63:56] == 8'h1D) begin
                qrf_wr_en   <= 1;
                qrf_wr_lane <= inst_word[55:48] % 13;
                // Sign-extend 8-bit A→64-bit: P=sign_ext, Q=0
                qrf_wr_A[31:0]  <= {{24{inst_word[39]}}, inst_word[39:32]};
                qrf_wr_A[63:32] <= 32'd0;
                qrf_wr_B[31:0]  <= {{24{inst_word[31]}}, inst_word[31:24]};
                qrf_wr_B[63:32] <= 32'd0;
                qrf_wr_C[31:0]  <= {{24{inst_word[23]}}, inst_word[23:16]};
                qrf_wr_C[63:32] <= 32'd0;
                qrf_wr_D[31:0]  <= {{24{inst_word[15]}}, inst_word[15:8]};
                qrf_wr_D[63:32] <= 32'd0;
            end

            if (inst_valid && inst_word[63:56] == 8'h1C) begin
                // Latch ROTC parameters from instruction
                rote_src_lane  <= inst_word[47:40] % 13;
                rote_dest_lane <= inst_word[55:48] % 13;
                rote_angle     <= inst_word[29:24];  // P1_A[5:0] = angle
                rote_field     <= inst_word[31:30];  // P1_A[7:6] = field
                rote_active    <= 1;
            end else if (rote_active) begin
                // Execute: fire rotor core (combinational read already
                // feeding qrf_rd_*), then write back on next cycle.
                rote_en    <= 1;
                rote_active <= 0;
            end else if (rote_en) begin
                // Write-back cycle
                qrf_wr_en   <= 1;
                qrf_wr_lane <= rote_dest_lane;
                rote_en     <= 0;
            end
        end
    end

    // Stage 3: Stability Check & Commit (Pulse 21)
    wire [63:0] rotated_axis;
    assign rotated_axis = q_prime_ab;
    wire [`MANIFOLD_WIDTH-1:0] manifold_commit_reg;
    assign manifold_commit_reg = manifold_with_axis(manifold_reg, axis_ptr, rotated_axis);
    wire [31:0] quadrance;
    wire [31:0] ivm_quadrance;
    wire [15:0] gasket_sum;
    wire signed [31:0] audio_p;
    wire signed [31:0] audio_q;
    
    generate
        if (ENABLE_MATH) begin : gen_davis_gate
            davis_gate_dsp #(.DEVICE(DEVICE)) u_gate (
                .clk(clk),
                .rst_n(rst_n),
                .q_vector(rotated_axis),
                .q_rotated(),
                .quadrance(quadrance),
                .ivm_quadrance(ivm_quadrance),
                .gasket_sum(gasket_sum),
                .audio_p(audio_p),
                .audio_q(audio_q)
            );
        end else begin : gen_no_davis_gate
            assign quadrance = current_axis_data[63:32] >> 12;
            assign ivm_quadrance = 32'd0;
            assign gasket_sum = current_axis_data[63:48] + current_axis_data[47:32]
                              + current_axis_data[31:16] + current_axis_data[15:0];
            assign audio_p = 32'sd0;
            assign audio_q = 32'sd0;
        end
    endgenerate

    wire rplu_dissoc;
    wire rplu_done;
    wire [9:0] rplu_addr_dbg;
    generate
        if (ENABLE_RPLU) begin : gen_rplu
            davis_to_rplu u_davis_rplu (
                .clk(clk), .rst_n(rst_n), .start(phi_21), .q_vector(rotated_axis), .material_id(phinary_chirality),
                .cfg_wr_en(dec_fast_cfg_wr_en), .cfg_wr_sel(dec_fast_cfg_sel), .cfg_wr_material(dec_fast_cfg_material), .cfg_wr_addr(dec_fast_cfg_addr), .cfg_wr_data(dec_fast_cfg_data),
                .v_q16(), .dissoc(rplu_dissoc), .done(rplu_done),
                .quadrance(), .ivm_quadrance(), .gasket_sum(), .audio_p(), .audio_q(),
                .ratio_cmp_res(ratio_cmp_res), .ratio_cmp_valid(ratio_cmp_valid),
                .r_addr_dbg(rplu_addr_dbg), .r_q16_dbg()
            );
        end else begin : gen_no_rplu
            assign rplu_dissoc = 1'b0;
            assign rplu_done = phi_21;
            assign ratio_cmp_res = 3'sd0;
            assign ratio_cmp_valid = 1'b0;
            assign rplu_addr_dbg = 10'd0;
        end
    endgenerate

    // Scoreboard for RPLU results (since RPLU takes multiple cycles, we latch the result)
    reg [12:0] rplu_dissoc_bits;
    reg [3:0]  rplu_axis_pending;

    assign gasket_sum_out = gasket_sum;
    assign quadrance_out  = quadrance;
    assign cycle_wrap     = (axis_ptr == 4'd12);
    assign rplu_dissoc_out = rplu_dissoc;
    assign rplu_dissoc_mask_out = rplu_dissoc_bits;
    assign rplu_addr_out = rplu_addr_dbg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rplu_dissoc_bits <= 13'h0;
            rplu_axis_pending <= 4'd0;
        end else begin
            if (phi_21) begin
                rplu_axis_pending <= axis_ptr;
            end
            if (rplu_done && (rplu_axis_pending <= 4'd12)) begin
                rplu_dissoc_bits[rplu_axis_pending] <= rplu_dissoc;
            end
        end
    end


    wire [31:0] quadrance_err;
    // Adaptive threshold from soul metabolism (default 0x0100_0000 = 256 in Q16).
    // When fault rate is high, tau widens → gate less sensitive.
    // When stable, tau tightens → gate more sensitive.
    wire [31:0] adaptive_threshold;
    assign adaptive_threshold = (adaptive_tau_q != 32'd0) ? adaptive_tau_q : 32'h0100_0000;
    assign quadrance_err = (quadrance > adaptive_threshold) ? (quadrance - adaptive_threshold) : (adaptive_threshold - quadrance);
    wire axis_stable;
    assign axis_stable = (quadrance > 32'h0000_0000) && !rplu_dissoc;


    reg [12:0] stability_bits;

    // Toroidal emitter index (wraps naturally at 10 bits)
    reg [9:0] torus_idx;
    reg        torus_emit_enable;

    // Sovereign Hydration & State Logic
    reg [2:0] hydration_state;
    localparam H_IDLE   = 3'd0;
    localparam H_INHALE = 3'd1;
    localparam H_BLOOM  = 3'd2;
    localparam H_EXHALE = 3'd3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hydration_state <= H_IDLE;
            mem_burst_rd <= 0; mem_burst_wr <= 0; mem_addr <= 0;
            stability_bits <= 13'h1FFF;
            is_janus_point <= 1'b1;
            scale_write_en <= 1'b0;
            scale_write_shift <= 4'd0;
            scale_write_overflow <= 1'b0;
            artery_wr_en <= 1'b0;
            artery_wr_data <= 64'd0;
            audio_mode <= 2'b00;
            torus_idx <= 10'd0;
            torus_emit_enable <= 1'b0;
            // Seed the 13-axis manifold with a non-zero laminar value.
            // Explicit constant assignments are required for FPGA FF initialisation
            // (Yosys does not synthesise initial blocks with for-loops).
            manifold_lane[0]  <= 64'h0002000_00000000; // Prime 2
            manifold_lane[1]  <= 64'h0003000_00000000; // Prime 3
            manifold_lane[2]  <= 64'h0005000_00000000; // Prime 5
            manifold_lane[3]  <= 64'h0007000_00000000; // Prime 7
            manifold_lane[4]  <= 64'h000B000_00000000; // Prime 11
            manifold_lane[5]  <= 64'h000D000_00000000; // Prime 13
            manifold_lane[6]  <= 64'h0011000_00000000; // Prime 17
            manifold_lane[7]  <= 64'h0013000_00000000; // Prime 19
            manifold_lane[8]  <= 64'h0017000_00000000; // Prime 23
            manifold_lane[9]  <= 64'h001D000_00000000; // Prime 29
            manifold_lane[10] <= 64'h001F000_00000000; // Prime 31
            manifold_lane[11] <= 64'h0025000_00000000; // Prime 37
            manifold_lane[12] <= 64'h0029000_00000000; // Prime 41
        end else if (prime_we && !boot_done) begin
            // Hydrate the specified axis with the flash prime in the same
            // Q12-scaled format used by the hardcoded reset seeds.
            case (prime_addr)
                4'd0:  manifold_lane[0]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd1:  manifold_lane[1]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd2:  manifold_lane[2]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd3:  manifold_lane[3]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd4:  manifold_lane[4]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd5:  manifold_lane[5]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd6:  manifold_lane[6]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd7:  manifold_lane[7]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd8:  manifold_lane[8]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd9:  manifold_lane[9]  <= {({8'd0, prime_data} << 12), 32'd0};
                4'd10: manifold_lane[10] <= {({8'd0, prime_data} << 12), 32'd0};
                4'd11: manifold_lane[11] <= {({8'd0, prime_data} << 12), 32'd0};
                4'd12: manifold_lane[12] <= {({8'd0, prime_data} << 12), 32'd0};
                default: ;
            endcase
        end else begin
            // default: clear any one-cycle artery writes
            artery_wr_en <= 1'b0;
            artery_wr_data <= 64'd0;
            scale_write_en <= 1'b0;

            // fast-domain config writes: torus control (sel==7)
            if (dec_fast_cfg_wr_en && dec_fast_cfg_sel == 3'd7) begin
                torus_idx <= dec_fast_cfg_data[9:0];
                torus_emit_enable <= dec_fast_cfg_data[10];
            end

`ifdef DEBUG_VOICE
            // Chord 0xB5 Handler: Audio Control
            if (dec_fast_cfg_wr_en && dec_fast_cfg_sel == 3'd5) begin
                audio_mode <= dec_fast_cfg_data[1:0];
            end
`endif

            // Instruction-level POLY_STEP handler (optional): emit a direct RPLU config write
            // Encoding: Lithic-L [63:56]=0xE0 — POLY_STEP
            // Use p1_a[9:0] (inst_word[33:24]) as the RPLU address index.
            if (inst_valid) begin
                if (inst_word[63:56] == 8'hE0) begin
                    artery_wr_en <= 1'b1;
                    artery_wr_data <= {8'hA5, 8'd7, 1'b0, inst_word[33:24], 1'b1, 36'd0};
                end
            end

            case (hydration_state)
                H_IDLE: begin
                    if (phi_8) begin
                        hydration_state <= H_BLOOM;
                    end
                end
                H_INHALE: begin
                    if (mem_burst_done) begin
                        mem_burst_rd <= 0;
                        manifold_lane[0]  <= mem_rd_manifold[63:0];
                        manifold_lane[1]  <= mem_rd_manifold[127:64];
                        manifold_lane[2]  <= mem_rd_manifold[191:128];
                        manifold_lane[3]  <= mem_rd_manifold[255:192];
                        manifold_lane[4]  <= mem_rd_manifold[319:256];
                        manifold_lane[5]  <= mem_rd_manifold[383:320];
                        manifold_lane[6]  <= mem_rd_manifold[447:384];
                        manifold_lane[7]  <= mem_rd_manifold[511:448];
                        manifold_lane[8]  <= mem_rd_manifold[575:512];
                        manifold_lane[9]  <= mem_rd_manifold[639:576];
                        manifold_lane[10] <= mem_rd_manifold[703:640];
                        manifold_lane[11] <= mem_rd_manifold[767:704];
                        manifold_lane[12] <= mem_rd_manifold[831:768];
                        hydration_state <= H_BLOOM;
                    end
                end
                H_BLOOM: begin
                    // Commit current axis on Pulse 21
                    if (phi_21) begin
                        case (axis_ptr)
                            4'd0:  manifold_lane[0]  <= rotated_axis;
                            4'd1:  manifold_lane[1]  <= rotated_axis;
                            4'd2:  manifold_lane[2]  <= rotated_axis;
                            4'd3:  manifold_lane[3]  <= rotated_axis;
                            4'd4:  manifold_lane[4]  <= rotated_axis;
                            4'd5:  manifold_lane[5]  <= rotated_axis;
                            4'd6:  manifold_lane[6]  <= rotated_axis;
                            4'd7:  manifold_lane[7]  <= rotated_axis;
                            4'd8:  manifold_lane[8]  <= rotated_axis;
                            4'd9:  manifold_lane[9]  <= rotated_axis;
                            4'd10: manifold_lane[10] <= rotated_axis;
                            4'd11: manifold_lane[11] <= rotated_axis;
                            4'd12: manifold_lane[12] <= rotated_axis;
                            default: ;
                        endcase
                        stability_bits[axis_ptr] <= axis_stable && !rplu_dissoc_bits[axis_ptr];

                        // Capture scale shift for this axis into global scale manager
                        scale_write_en <= 1'b1;
                        scale_write_shift <= lattice_axis_shift;
                        scale_write_overflow <= lattice_axis_overflow;
                        
                        // If we just finished axis 12, move to Exhale
                        if (axis_ptr == 4'd12) begin
                            is_janus_point <= &stability_bits;
                            mem_burst_wr <= 1;
                            mem_wr_manifold <= manifold_commit_reg;
                            hydration_state <= H_EXHALE;

                            // Emit a POLY_STEP Artery chord using toroidal index (if enabled).
                            // Header layout: [63:56]=0xA5, [55:48]=sel, [47]=material, [46:37]=addr, [36]=singleton
                            if (torus_emit_enable) begin
                                artery_wr_en <= 1'b1;
                                artery_wr_data <= {8'hA5, 8'd7, 1'b0, torus_idx[9:0], 1'b1, 36'd0};
                                // advance torus index (wraps naturally at 10 bits)
                                torus_idx <= torus_idx + 10'd1;
                            end
                        end
                    end else begin
                    end
                end
                H_EXHALE: begin
                    if (mem_burst_done) begin
                        mem_burst_wr <= 0;
                        mem_burst_rd <= 1;
                        hydration_state <= H_INHALE;
                    end
                end
            endcase
        end
    end

    assign bloom_complete = (hydration_state == H_IDLE);

endmodule
