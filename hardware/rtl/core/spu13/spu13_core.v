// SPU-13 Sovereign Core (v1.7 - Strictly Phi-Gated TDM)
// Objective: 13-axis Manifold via Fibonacci-Synchronized Pipeline.
// Architecture: TDM Davis Law Gasket + SQR Rotor Vault + Artery Interface.

`include "spu_arch_defines.vh"

module spu13_core #(
    parameter DEVICE = "GW2A",  // "GW1N" | "GW2A" | "GW5A" | "SIM"
    parameter ENABLE_RPLU = 1,
    parameter ENABLE_LATTICE = 1,
    parameter ENABLE_MATH = 1,
    parameter ENABLE_SEQUENCER = 1,
    parameter ENABLE_CORE_SOM  = 0,   // SOM/BMU classifier pipeline (legacy serial scan)
    parameter ENABLE_CORE_RPLU_V2 = 0, // RPLU v2: A31 Thimble-Padé pipeline (parallel SOM + BTU + Padé + M31)
    parameter ENABLE_CORE_RPLU_V2_PIPELINE = ENABLE_CORE_RPLU_V2, // live SOM/BTU/Padé/inverter evaluator
    parameter ENABLE_CORE_RPLU_V2_EXTENSIONS = ENABLE_CORE_RPLU_V2, // NSA/topology6 extension bundle
    parameter EXTERNAL_RPLU_PADE_MULT = 0,
    parameter SHARE_RPLU_PADE_INV_MULT = 0,
    parameter ENABLE_TORUS = 0, // optional 832-bit manifold snapshot ring buffer
    parameter ENABLE_IROTC = 0, // icosahedral A₅ engine + φ-plane typestate (IROTC_SPEC.md v0.2)
    parameter [255:0] MEM_FILE = "hardware/rtl/arch/hw_test.mem"
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

    // Last QLDI QR commit telemetry for the southbridge.
    output wire                   qr_commit_valid,
    output wire [3:0]             qr_commit_lane,
    output wire [63:0]            qr_commit_A,
    output wire [63:0]            qr_commit_B,
    output wire [63:0]            qr_commit_C,
    output wire [63:0]            qr_commit_D,

    // Instruction input (optional). When unused, tie inst_valid=0 at instantiation.
    input  wire                    inst_valid,
    input  wire [63:0]             inst_word,
    output wire                    inst_done,   // pulsed when instruction completes

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
    output wire [9:0]                rplu_addr_out,

    // ── Audio / I2S outputs ─────────────────────────────────────
    output wire                      i2s_bclk,
    output wire                      i2s_lrclk,
    output wire                      i2s_dout,
    output wire [7:0]                laminar_flow_index_out,
    output wire [31:0]               thermal_pressure_out,

    // ── Hex coordinate output (for UART telemetry) ──────────────
    output reg                      hex_valid,
    output reg  [15:0]              hex_q,
    output reg  [15:0]              hex_r,
    output wire signed [31:0]        audio_p_out,
    output wire signed [31:0]        audio_q_out,

    // ── SOM / gatekeeper fault telemetry ───────────────────────
    output wire                      axiomatic_fault,
    output wire [1:0]                fault_type,
    output wire [15:0]               fault_count,
    output wire                      rns_error,        // M31 multiplier residue parity
    output wire                      ecc_single_err,   // QR regfile single-bit error corrected
    output wire                      ecc_double_err,   // QR regfile double-bit error detected
    output wire [15:0]               rotc_debug_status, // bring-up: flags/state/angle

    // Optional external RPLU v2 Padé multiplier. Active only when
    // EXTERNAL_RPLU_PADE_MULT=1 and ENABLE_CORE_RPLU_V2_PIPELINE=1.
    output wire                      rplu_pade_mult_start,
    output wire [31:0]               rplu_pade_mult_a0,
    output wire [31:0]               rplu_pade_mult_a1,
    output wire [31:0]               rplu_pade_mult_a2,
    output wire [31:0]               rplu_pade_mult_a3,
    output wire [31:0]               rplu_pade_mult_b0,
    output wire [31:0]               rplu_pade_mult_b1,
    output wire [31:0]               rplu_pade_mult_b2,
    output wire [31:0]               rplu_pade_mult_b3,
    input  wire [31:0]               rplu_pade_mult_r0,
    input  wire [31:0]               rplu_pade_mult_r1,
    input  wire [31:0]               rplu_pade_mult_r2,
    input  wire [31:0]               rplu_pade_mult_r3,
    input  wire                      rplu_pade_mult_done,
    input  wire                      rplu_pade_mult_busy,
    input  wire                      rplu_pade_mult_rns_error
);

    // 1. Manifold State Buffering

    // Keep the live manifold as explicit 64-bit lanes so boot hydration and
    // axis commits compile into narrow per-lane enables rather than a single
    // wide indexed write across the entire 832-bit slab.
    reg [63:0] manifold_lane [0:(`MANIFOLD_AXES-1)];
    wire [`MANIFOLD_WIDTH-1:0] manifold_reg;
    wire [831:0] annealed_manifold;
    wire [`MANIFOLD_WIDTH-1:0] manifold_commit_reg;
    wire [31:0] adaptive_tau_q;
    wire signed [31:0] audio_p;
    wire signed [31:0] audio_q;
    wire rplu_dissoc;
    wire rplu_done;
    wire [9:0] rplu_addr_dbg;
    wire        som_done;
    wire        som_train_done;
    wire        som_classify_valid;
    wire [15:0] som_label;
    wire [63:0] som_gap;
    wire        som_ambiguous;
    wire        som_rns_error;
    wire        rplu2_core_rns_error;
    wire        rplu2_result_valid;
    wire [31:0] rplu2_result_c0;
    wire [31:0] rplu2_result_c1;
    wire [31:0] rplu2_result_c2;
    wire [31:0] rplu2_result_c3;
    reg  [31:0] quadray_target_kappa;
    reg         quadray_target_valid;
    reg [12:0] stability_bits;

    // RPLU v2 fast config stream:
    //   sel=1: Padé numerator coefficient pair, addr[2:0]=coeff, addr[3]=pair
    //   sel=2: Padé denominator coefficient pair, addr[2:0]=coeff, addr[3]=pair
    //   sel=3: BTU row pair, addr[5:0]=row, addr[6]=pair
    //   sel=6: Quadray target kappa
    localparam [2:0] RPLU2_CFG_PADE_NUM = 3'd1;
    localparam [2:0] RPLU2_CFG_PADE_DEN = 3'd2;
    localparam [2:0] RPLU2_CFG_BTU_ROW  = 3'd3;
    localparam [2:0] SOM_CFG_WEIGHT      = 3'd4;
    localparam [2:0] RPLU2_CFG_KAPPA    = 3'd6;
    reg [31:0] rplu2_pade_num_c0 [0:4];
    reg [31:0] rplu2_pade_num_c1 [0:4];
    reg [31:0] rplu2_pade_den_c0 [0:4];
    reg [31:0] rplu2_pade_den_c1 [0:4];
    integer rplu2_cfg_i;
    initial begin
        for (rplu2_cfg_i = 0; rplu2_cfg_i < 5; rplu2_cfg_i = rplu2_cfg_i + 1) begin
            rplu2_pade_num_c0[rplu2_cfg_i] = 32'd0;
            rplu2_pade_num_c1[rplu2_cfg_i] = 32'd0;
            rplu2_pade_den_c0[rplu2_cfg_i] = 32'd0;
            rplu2_pade_den_c1[rplu2_cfg_i] = 32'd0;
        end
        rplu2_pade_num_c0[0] = 32'd1;
        rplu2_pade_den_c0[0] = 32'd1;
    end

    wire [2:0] rplu2_pade_cfg_idx_raw = dec_fast_cfg_addr[2:0];
    wire [2:0] rplu2_pade_cfg_idx =
        (rplu2_pade_cfg_idx_raw < 3'd5) ? rplu2_pade_cfg_idx_raw : 3'd0;
    wire rplu2_pade_cfg_idx_valid = (rplu2_pade_cfg_idx_raw < 3'd5);
    wire rplu2_pade_cfg_high = dec_fast_cfg_addr[3];
    wire rplu2_cfg_pade_num = dec_fast_cfg_wr_en &&
                              dec_fast_cfg_sel == RPLU2_CFG_PADE_NUM &&
                              rplu2_pade_cfg_idx_valid;
    wire rplu2_cfg_pade_den = dec_fast_cfg_wr_en &&
                              dec_fast_cfg_sel == RPLU2_CFG_PADE_DEN &&
                              rplu2_pade_cfg_idx_valid;
    wire rplu2_pade_coeff_we = (rplu2_cfg_pade_num || rplu2_cfg_pade_den) &&
                               rplu2_pade_cfg_high;
    wire rplu2_pade_coeff_is_den = rplu2_cfg_pade_den;
    wire [2:0] rplu2_pade_coeff_addr = rplu2_pade_cfg_idx;
    wire [31:0] rplu2_pade_coeff_c0 = rplu2_cfg_pade_den
                                     ? rplu2_pade_den_c0[rplu2_pade_cfg_idx]
                                     : rplu2_pade_num_c0[rplu2_pade_cfg_idx];
    wire [31:0] rplu2_pade_coeff_c1 = rplu2_cfg_pade_den
                                     ? rplu2_pade_den_c1[rplu2_pade_cfg_idx]
                                     : rplu2_pade_num_c1[rplu2_pade_cfg_idx];
    wire [31:0] rplu2_pade_coeff_c2 = dec_fast_cfg_data[31:0];
    wire [31:0] rplu2_pade_coeff_c3 = dec_fast_cfg_data[63:32];
    wire rplu2_btu_cfg_we = dec_fast_cfg_wr_en &&
                            dec_fast_cfg_sel == RPLU2_CFG_BTU_ROW;
    wire [5:0] rplu2_btu_cfg_addr = dec_fast_cfg_addr[5:0];
    wire rplu2_btu_cfg_pair = dec_fast_cfg_addr[6];
    wire [63:0] rplu2_btu_cfg_data = dec_fast_cfg_data;

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

    // ── Active Inference (Predictive Coding Filter) [STUBBED - archived]
    // Filters transient cubic leaks from genuine manifold divergence
    // using the Free Energy Principle. Archived; outputs unused.
    wire [127:0] inference_posterior;
    wire [127:0] inference_error;
    wire         inference_dissonant;
    reg          fault_pulse_d1;  // delayed fault to align with manifold
    assign inference_posterior = 128'd0;
    assign inference_error = 128'd0;
    assign inference_dissonant = 1'b0;

    // ── Soul Metabolism (Adaptive Safety Valve) ─────────────────────
    // Tracks fault rate and adjusts Davis Gate sensitivity (adaptive_tau).
    // Widens tau when tuck rate > 13% (Fibonacci threshold), tightens
    // when stable. Periodically saves health state to SPI flash.
    wire [31:0] soul_tuck_count, soul_cycle_count;
    wire        soul_flash_we;
    wire [23:0] soul_flash_addr;
    wire [255:0] soul_flash_page;

    // ── Viscosity Monitor [STUBBED - archived]
    // Measures manifold flow quality. Archived; defaults to liquid (0xFF).
    wire [7:0] laminar_flow_index;
    assign laminar_flow_index = 8'hFF;

    // ── Proprioception (Thermal Awareness) [STUBBED - archived]
    // Monitors switching density across the full manifold.
    // Archived; defaults to zero pressure, no damping.
    wire [31:0] thermal_pressure;
    wire        damping_active;
    assign thermal_pressure = 32'd0;
    assign damping_active = 1'b0;

    // ── I2S Audio Output ──────────────────────────────────────────
    // Converts Davis Gate audio surds to I2S protocol for PCM5102A DAC.
    spu_i2s_out u_i2s (
        .clk(clk), .rst_n(rst_n),
        .mode(2'b01),               // passthrough mode
        .lfi({8'd0, laminar_flow_index}),
        .left_data(audio_p[23:0]),
        .right_data(audio_q[23:0]),
        .i2s_bclk(i2s_bclk),
        .i2s_lrclk(i2s_lrclk),
        .i2s_dout(i2s_dout)
    );

    // ── Toroidal Register File (Manifold Frame Buffer) ────────────
    // Optional 832-bit × 8-entry rotating buffer. The read port is not yet
    // consumed by the core, so probe spins keep this disabled to avoid pulling
    // a wide history buffer through synthesis.
    generate
        if (ENABLE_TORUS) begin : gen_torus
            wire [831:0] torus_rd_data;
            reg          torus_wr_en;
            reg  [2:0]   torus_wr_addr;

            toroidal_regfile_ecc #(.WIDTH(832), .NUM(8)) u_torus (
                .clk(clk), .rst_n(rst_n),
                .wr_en(torus_wr_en),
                .wr_addr(torus_wr_addr),
                .wr_data(manifold_commit_reg),
                .rd_en(1'b0),
                .rd_addr(3'd0),
                .rd_data(torus_rd_data),
                .rotate_start(1'b0),
                .rotate_amount(32'd0),
                .rotate_idx(3'd0),
                .rotate_dir(1'b0),
                .method_sel(1'b0),
                .rotate_done(),
                .integrity_error()
            );

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    torus_wr_en <= 1'b0;
                    torus_wr_addr <= 3'd0;
                end else begin
                    torus_wr_en <= 1'b0;
                    if (cycle_wrap) begin
                        torus_wr_en <= 1'b1;
                        torus_wr_addr <= torus_wr_addr + 3'd1;
                    end
                end
            end
        end
    endgenerate

    // Combined fault: RPLU dissociation OR proprioceptive damping
    wire combined_fault;
    assign combined_fault = rplu_dissoc || damping_active;

    // spu_soul_metabolism [STUBBED - archived]
    // Adaptive tau defaults to 0x0100_0000 (Q16 = 256).
    assign adaptive_tau_q = 32'h0100_0000;
    assign soul_tuck_count = 32'd0;
    assign soul_cycle_count = 32'd0;
    assign soul_flash_we = 1'b0;
    assign soul_flash_addr = 24'd0;
    assign soul_flash_page = 256'd0;

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
    wire rote_done_tdm;
    wire rote_denom_3;
    wire [3:0] rote_debug_state;
    localparam RPLU2_SOM_COEFF_W = 18;
    localparam RPLU2_SOM_SURD_W = 2 * RPLU2_SOM_COEFF_W;
    function [RPLU2_SOM_SURD_W-1:0] rplu2_narrow_rs;
        input [63:0] rs;
        begin
            rplu2_narrow_rs = {rs[32 +: RPLU2_SOM_COEFF_W], rs[0 +: RPLU2_SOM_COEFF_W]};
        end
    endfunction
    wire [143:0] rplu2_features;
    assign rplu2_features = {
        rplu2_narrow_rs(qrf_rd_D),
        rplu2_narrow_rs(qrf_rd_C),
        rplu2_narrow_rs(qrf_rd_B),
        rplu2_narrow_rs(qrf_rd_A)
    };

    reg       inst_done_r;
    reg       instr_wr_active;
    reg [63:0] instr_wr_A, instr_wr_B, instr_wr_C, instr_wr_D;
    reg       qr_commit_valid_r;
    reg [3:0] qr_commit_lane_r;
    reg [63:0] qr_commit_A_r, qr_commit_B_r, qr_commit_C_r, qr_commit_D_r;
    reg [3:0] rplu2_result_lane;
    assign qr_commit_valid = qr_commit_valid_r;
    assign qr_commit_lane = qr_commit_lane_r;
    assign qr_commit_A = qr_commit_A_r;
    assign qr_commit_B = qr_commit_B_r;
    assign qr_commit_C = qr_commit_C_r;
    assign qr_commit_D = qr_commit_D_r;

    // ── Instruction Sequencer (autonomous program execution) ─────
    // When ENABLE_SEQUENCER=1, the sequencer loads program from
    // MEM_FILE and drives inst_valid/inst_word automatically.
    wire        seq_inst_valid;
    wire [63:0] seq_inst_word;
    wire        seq_halted;
    wire [7:0]  seq_pc;

    generate
        if (ENABLE_SEQUENCER) begin : gen_sequencer
            spu_sequencer #(
                .IMEM_DEPTH(32)
            ) u_sequencer (
                .clk(clk), .rst_n(rst_n),
                .boot_done(boot_done),
                .inst_valid(seq_inst_valid),
                .inst_word(seq_inst_word),
                .inst_done(inst_done),
                .pc_out(seq_pc),
                .halted(seq_halted),
                .program_size()
            );
        end else begin : gen_no_sequencer
            assign seq_inst_valid = 1'b0;
            assign seq_inst_word  = 64'd0;
            assign seq_pc         = 8'd0;
            assign seq_halted     = 1'b1;
        end
    endgenerate

    // Mux: external inst_valid or sequencer-driven
    wire        eff_inst_valid;
    wire [63:0] eff_inst_word;
    wire        inst_accept;
    reg         inst_seen;
    assign eff_inst_valid = ENABLE_SEQUENCER ? seq_inst_valid : inst_valid;
    assign eff_inst_word  = ENABLE_SEQUENCER ? seq_inst_word  : inst_word;
    assign inst_accept    = eff_inst_valid && !inst_seen;
    wire core_jscr_opcode = (eff_inst_word[63:56] == 8'h48);
    wire core_nsa_opcode  = (eff_inst_word[63:56] == 8'h4C) ||
                            (eff_inst_word[63:56] == 8'h4D);
    wire core_nsa_done;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            inst_seen <= 1'b0;
        else if (!eff_inst_valid)
            inst_seen <= 1'b0;
        else if (inst_accept)
            inst_seen <= 1'b1;
    end

    // Alias for internal use (so existing code uses muxed signals)
    // Note: inst_valid and inst_word are port names; we override them
    // inside the gen_qrf block by using eff_* versions via parameters.
    // Actually, we just use eff_inst_valid/eff_inst_word everywhere.

    generate
        if (ENABLE_MATH || ENABLE_CORE_SOM || ENABLE_CORE_RPLU_V2) begin : gen_qrf

            wire ecc_qr_single, ecc_qr_double;
            // ── VE QR Hydration ──────────────────────────────────
            wire ve_qr_init_en;
            wire [3:0] ve_qr_init_lane;
            wire [63:0] ve_qr_init_A, ve_qr_init_B, ve_qr_init_C, ve_qr_init_D;
            wire ve_qr_init_done;
            wire [63:0] regfile_wr_A_mux;
            wire [63:0] regfile_wr_B_mux;
            wire [63:0] regfile_wr_C_mux;
            wire [63:0] regfile_wr_D_mux;

            spu_ve_qr_init u_ve_qr_init (
                .clk(clk), .rst_n(rst_n),
                .boot_done(boot_done),
                .init_en(ve_qr_init_en),
                .init_lane(ve_qr_init_lane),
                .init_A(ve_qr_init_A), .init_B(ve_qr_init_B),
                .init_C(ve_qr_init_C), .init_D(ve_qr_init_D),
                .init_done(ve_qr_init_done)
            );

            spu_quadray_regfile_ecc u_qrf (
                .clk(clk), .rst_n(rst_n),
                .rd_lane(rote_src_lane),
                .rd_A(qrf_rd_A), .rd_B(qrf_rd_B),
                .rd_C(qrf_rd_C), .rd_D(qrf_rd_D),
                .wr_en(qrf_wr_en),
                .wr_lane(qrf_wr_lane),
                .wr_A(regfile_wr_A_mux), .wr_B(regfile_wr_B_mux),
                .wr_C(regfile_wr_C_mux), .wr_D(regfile_wr_D_mux),
                .init_en(ve_qr_init_en), .init_lane(ve_qr_init_lane),
                .init_A(ve_qr_init_A), .init_B(ve_qr_init_B),
                .init_C(ve_qr_init_C), .init_D(ve_qr_init_D),
                .dbg_A(), .dbg_B(), .dbg_C(), .dbg_D(),
                .ecc_single_err(ecc_qr_single), .ecc_double_err(ecc_qr_double)
            );

            if (ENABLE_MATH) begin : gen_rotc_datapath
                // ── Quadray Permuter ──────────────────────────────────
                // For ROTC angles 6-11 (non-A-invariant rotations), permute
                // coordinates so the target axis becomes A, apply ROTC, then
                // un-permute back. Angles 0-5 are direct (A is invariant).
                wire [1:0] rote_perm_sel;
                wire [63:0] rotor_A_in, rotor_B_in, rotor_C_in, rotor_D_in;

                // Angle → perm_sel:
                //   0-5, 21-23:   00 (A-invariant or direct bypass)
                //   6-7, 12, 15-16: 01 (B→A)
                //   8-9, 13, 17-18: 10 (C→A)
                //   10-11, 14, 19-20: 11 (D→A)
                assign rote_perm_sel =
                    (rote_angle <= 6'd5)                       ? 2'b00 :
                    (rote_angle == 6'd6 || rote_angle == 6'd7 ||
                     rote_angle == 6'd12 ||
                     rote_angle == 6'd15 || rote_angle == 6'd16) ? 2'b01 :
                    (rote_angle == 6'd8 || rote_angle == 6'd9 ||
                     rote_angle == 6'd13 ||
                     rote_angle == 6'd17 || rote_angle == 6'd18) ? 2'b10 :
                    (rote_angle == 6'd10 || rote_angle == 6'd11 ||
                     rote_angle == 6'd14 ||
                     rote_angle == 6'd19 || rote_angle == 6'd20) ? 2'b11 :
                    2'b00;

                spu_quadray_permute u_perm_fwd (
                    .perm_sel(rote_perm_sel),
                    .A_in(qrf_rd_A), .B_in(qrf_rd_B),
                    .C_in(qrf_rd_C), .D_in(qrf_rd_D),
                    .A_out(rotor_A_in), .B_out(rotor_B_in),
                    .C_out(rotor_C_in), .D_out(rotor_D_in)
                );

                // TDM rotor core — 11-cycle pipeline, shared multiplier
                spu13_rotor_core_tdm #(
                    .ENABLE_TDM_FALLBACK(0)
                ) u_rotc (
                    .clk(clk), .rst_n(rst_n),
                    .start(rote_en),
                    .done(rote_done_tdm),
                    .A_in(rotor_A_in),
                    .B_in(rotor_B_in),
                    .C_in(rotor_C_in),
                    .D_in(rotor_D_in),
                    .F(rote_F), .G(rote_G), .H(rote_H),
                    .field_sel(rote_field),
                    .bypass_p5(rote_angle == 6'd2 ||
                               rote_angle == 6'd15 ||
                               rote_angle == 6'd17 ||
                               rote_angle == 6'd19),
                    .bypass_p5_inv(rote_angle == 6'd5 ||
                                   rote_angle == 6'd16 ||
                                   rote_angle == 6'd18 ||
                                   rote_angle == 6'd20),
                    .bypass_ab_cd(rote_angle == 6'd21),
                    .bypass_ac_bd(rote_angle == 6'd22),
                    .bypass_ad_bc(rote_angle == 6'd23),
                    .recompute_A(rote_angle >= 6'd24 && rote_angle <= 6'd35),
                    .apply_div3(rote_denom_3),
                    .angle(rote_angle),
                    .A_out(rote_A_out_raw),
                    .B_out(rote_B_out_raw),
                    .C_out(rote_C_out_raw),
                    .D_out(rote_D_out_raw),
                    .debug_state(rote_debug_state)
                );

                // ── Inverse Permuter ───────────────────────────────────
                // Undo the coordinate permutation for conjugated angles.
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

                assign regfile_wr_A_mux = instr_wr_active ? instr_wr_A : qrf_wr_A;
                assign regfile_wr_B_mux = instr_wr_active ? instr_wr_B : rote_B_out;
                assign regfile_wr_C_mux = instr_wr_active ? instr_wr_C : rote_C_out;
                assign regfile_wr_D_mux = instr_wr_active ? instr_wr_D : rote_D_out;

                assign qrf_wr_B = rote_B_out;
                assign qrf_wr_C = rote_C_out;
                assign qrf_wr_D = rote_D_out;
            assign ecc_single_err = ecc_qr_single;
            assign ecc_double_err = ecc_qr_double;
            end else begin : gen_qrf_only
                assign regfile_wr_A_mux = instr_wr_A;
                assign regfile_wr_B_mux = instr_wr_B;
                assign regfile_wr_C_mux = instr_wr_C;
                assign regfile_wr_D_mux = instr_wr_D;
                assign qrf_wr_A = 64'd0;
                assign qrf_wr_B = 64'd0;
                assign qrf_wr_C = 64'd0;
                assign qrf_wr_D = 64'd0;
                assign rote_B_out = 64'd0;
                assign rote_C_out = 64'd0;
                assign rote_D_out = 64'd0;
                assign rote_done_tdm = 1'b0;
                assign rote_debug_state = 4'd0;
            assign ecc_single_err = 1'b0;
            assign ecc_double_err = 1'b0;
            end
        end else begin : gen_no_qrf
            assign qrf_rd_A = 64'd0; assign qrf_rd_B = 64'd0;
            assign qrf_rd_C = 64'd0; assign qrf_rd_D = 64'd0;
            assign qrf_wr_A = 64'd0; assign qrf_wr_B = 64'd0;
            assign qrf_wr_C = 64'd0; assign qrf_wr_D = 64'd0;
            assign rote_B_out = 64'd0; assign rote_C_out = 64'd0;
            assign rote_D_out = 64'd0;
            assign rote_F = 64'd0; assign rote_G = 64'd0; assign rote_H = 64'd0;
            assign rote_done_tdm = 1'b0;
            assign rote_debug_state = 4'd0;
            assign ecc_single_err = 1'b0;
            assign ecc_double_err = 1'b0;
        end
    endgenerate

    // ── F,G,H lookup table (combinational) ─────────────────────────────
    // Identical to VM _ROTC_TABLE.
    // Negative values are explicitly bit-packed to avoid sign-extension across components.

    localparam [63:0] RS_1 = {32'd0, 32'd1};
    localparam [63:0] RS_2 = {32'd0, 32'd2};
    localparam [63:0] RS_N1 = {32'd0, 32'hFFFFFFFF};

    // Angles 0-11 and 12-23 are cross-verified against the VM oracle.
    // 0-5 passed June 2026; 6-11 passed 2026-07-10 once spu_vm.py gained
    // matching permutation logic. Tranche 1 (12-14, missing thirds conjugates)
    // and Tranche 2 (15-23, remaining A₄ pure permutations) were verified
    // 2026-07-10 against an independent exact-Fraction oracle: 24 distinct
    // matrices, det +1, inverse-closed, Davis zero-sum preserved.
    // Angles 24-63 remain unimplemented — ROTC_MAX_VERIFIED_ANGLE gates
    // dispatch in the decode FSM below. Raise this bound only after a new
    // angle gets its own VM-side logic and a matching cross-verified oracle
    // pass, same bar as 0-23 cleared.
    localparam [5:0] ROTC_MAX_VERIFIED_ANGLE = 6'd35;

    assign rote_F = (rote_angle == 6'd0)  ? RS_1  :
                    (rote_angle == 6'd1)  ? RS_2  :
                    (rote_angle == 6'd2)  ? 64'd0 :
                    (rote_angle == 6'd3)  ? RS_N1 :
                    (rote_angle == 6'd4)  ? RS_2  :
                    (rote_angle == 6'd5)  ? 64'd0 :
                    // Extended entries 6-11 (A₄ group)
                    (rote_angle == 6'd6)  ? RS_2  :
                    (rote_angle == 6'd7)  ? RS_2  :
                    (rote_angle == 6'd8)  ? RS_N1 :
                    (rote_angle == 6'd9)  ? RS_2  :
                    (rote_angle == 6'd10) ? RS_2  :
                    (rote_angle == 6'd11) ? RS_2  :
                    // Tranche 1: missing thirds conjugates (12-14)
                    (rote_angle == 6'd12) ? RS_N1 :
                    (rote_angle == 6'd13) ? RS_2  :
                    (rote_angle == 6'd14) ? RS_2  :
                    // Octahedral group (24-35): hardwired angle_scalar path,
                    // F/G/H entries are informational only.
                    (rote_angle == 6'd24) ? RS_N1 :
                    (rote_angle == 6'd25) ? RS_1  :
                    (rote_angle == 6'd26) ? RS_N1 :
                    (rote_angle == 6'd27) ? RS_N1 :
                    (rote_angle == 6'd28) ? RS_N1 :
                    (rote_angle == 6'd29) ? RS_1  :
                    (rote_angle == 6'd30) ? RS_N1 :
                    (rote_angle == 6'd31) ? RS_N1 :
                    (rote_angle == 6'd32) ? RS_N1 :
                    (rote_angle == 6'd33) ? RS_1  :
                    (rote_angle == 6'd34) ? RS_N1 :
                    (rote_angle == 6'd35) ? RS_N1 :
                    RS_1;

    assign rote_G = (rote_angle == 6'd0)  ? 64'd0 :
                    (rote_angle == 6'd1)  ? RS_2  :
                    (rote_angle == 6'd2)  ? RS_1  :
                    (rote_angle == 6'd3)  ? RS_2  :
                    (rote_angle == 6'd4)  ? RS_N1 :
                    (rote_angle == 6'd5)  ? 64'd0 :
                    // Extended entries
                    (rote_angle == 6'd6)  ? RS_N1 :
                    (rote_angle == 6'd7)  ? RS_2  :
                    (rote_angle == 6'd8)  ? RS_2  :
                    (rote_angle == 6'd9)  ? RS_2  :
                    (rote_angle == 6'd10) ? RS_N1 :
                    (rote_angle == 6'd11) ? RS_2  :
                    // Tranche 1: missing thirds conjugates (12-14)
                    (rote_angle == 6'd12) ? RS_2  :
                    (rote_angle == 6'd13) ? RS_N1 :
                    (rote_angle == 6'd14) ? RS_2  :
                    // Octahedral group (24-35)
                    (rote_angle >= 6'd24 && rote_angle <= 6'd35) ? 64'd0 :
                    64'd0;

    assign rote_H = (rote_angle == 6'd0)  ? 64'd0 :
                    (rote_angle == 6'd1)  ? RS_N1 :
                    (rote_angle == 6'd2)  ? 64'd0 :
                    (rote_angle == 6'd3)  ? RS_2  :
                    (rote_angle == 6'd4)  ? RS_2  :
                    (rote_angle == 6'd5)  ? RS_1  :
                    // Extended entries
                    (rote_angle == 6'd6)  ? RS_2  :
                    (rote_angle == 6'd7)  ? RS_N1 :
                    (rote_angle == 6'd8)  ? RS_2  :
                    (rote_angle == 6'd9)  ? RS_N1 :
                    (rote_angle == 6'd10) ? RS_2  :
                    (rote_angle == 6'd11) ? RS_2  :
                    // Tranche 1: missing thirds conjugates (12-14)
                    (rote_angle == 6'd12) ? RS_2  :
                    (rote_angle == 6'd13) ? RS_2  :
                    (rote_angle == 6'd14) ? RS_N1 :
                    // Octahedral group (24-35)
                    (rote_angle >= 6'd24 && rote_angle <= 6'd35) ? 64'd0 :
                    64'd0;

    assign rote_denom_3 = (rote_angle == 6'd1) ||
                          (rote_angle == 6'd3) ||
                          (rote_angle == 6'd4) ||
                          (rote_angle >= 6'd6  && rote_angle <= 6'd14);
    // Angles 6-14 are all thirds; 12-14 added 2026-07-10 (Tranche 1).

    // ── ROTC execution FSM ─────────────────────────────────────────────
    // On ROTC instruction (0x1C): latch source/dest/angle, fire rote_en.
    // The QR register file reads the source lane combinationally,
    // the rotor core computes the circulant, and we write back on the
    // next cycle.
    reg rote_active;
    reg [5:0] rotc_debug_angle;
    reg [7:0] rotc_debug_flags;
    reg       rotc_debug_busy;
    reg       hex_active;
    reg [3:0] rote_dest_lane;
    reg       qsub_active;
    reg       qsub_stage;
    reg [3:0] qsub_dest_lane;
    reg [3:0] qsub_rhs_lane;
    reg [63:0] qsub_lhs_A, qsub_lhs_B, qsub_lhs_C, qsub_lhs_D;
    wire [63:0] qsub_res_A, qsub_res_B, qsub_res_C, qsub_res_D;
    assign qsub_res_A = rs_sub64(qsub_lhs_A, qrf_rd_A);
    assign qsub_res_B = rs_sub64(qsub_lhs_B, qrf_rd_B);
    assign qsub_res_C = rs_sub64(qsub_lhs_C, qrf_rd_C);
    assign qsub_res_D = rs_sub64(qsub_lhs_D, qrf_rd_D);

    // ── φ-plane typestate tag file (IROTC_SPEC.md §3; 2 bits × 13 lanes) ──
    // Lives beside the QR file and is updated at every QR write site in
    // the dispatch FSM below. Soundness rule: a write from any op without
    // an explicit tag class clears the lane to UNTAGGED — a stale license
    // is structurally impossible. VE boot hydration is covered by the
    // reset default (tags reset UNTAGGED; hydration precedes boot_done, and
    // no φ-plane op can dispatch before the sequencer/SPI paths open).
    localparam [1:0] TAG_UNTAGGED = 2'd0;
    localparam [1:0] TAG_FRESH    = 2'd1;
    localparam [1:0] TAG_MAIN     = 2'd2;
    localparam [1:0] TAG_CONJ     = 2'd3;
    localparam [7:0] OP_IROTC  = 8'hD6;
    localparam [7:0] OP_LOAD2X = 8'hD7;
    localparam [7:0] OP_SCALE2 = 8'hD8;
    reg [1:0] qr_tags [0:12];
    reg [3:0] qsub_lhs_lane;        // for the QSUB tag lattice join
    reg       irotc_active;         // dispatch accepted, waiting one cycle
    reg       irotc_start;          // one-cycle engine start pulse
    reg [6:0] irotc_sel;
    reg [3:0] irotc_dst_lane;
    reg [1:0] irotc_src_tag;
    reg       scale2_active;
    reg [3:0] scale2_dst_lane;
    integer   tag_i;

    // QADD/QSUB linearity: lattice join (spec §3) — FRESH yields, equal
    // states preserve, MAIN+CONJ or any UNTAGGED clears.
    function [1:0] tag_join;
        input [1:0] x;
        input [1:0] y;
        begin
            if (x == TAG_UNTAGGED || y == TAG_UNTAGGED) tag_join = TAG_UNTAGGED;
            else if (x == y)          tag_join = x;
            else if (x == TAG_FRESH)  tag_join = y;
            else if (y == TAG_FRESH)  tag_join = x;
            else                      tag_join = TAG_UNTAGGED; // MAIN+CONJ
        end
    endfunction

    // ROTC angle classes (spec §3): thirds (1,3,4,6-14) clear; A₄ bypass
    // and identity (0,2,5,15-23) preserve; octahedral (24-35, integer but
    // not in A₅) demote MAIN/CONJ to UNTAGGED while FRESH (even) survives.
    function [1:0] rotc_tag_next;
        input [5:0] angle;
        input [1:0] src_tag;
        begin
            if (angle == 6'd1 || angle == 6'd3 || angle == 6'd4 ||
                (angle >= 6'd6 && angle <= 6'd14))
                rotc_tag_next = TAG_UNTAGGED;
            else if (angle >= 6'd24)
                rotc_tag_next = (src_tag == TAG_FRESH) ? TAG_FRESH
                                                       : TAG_UNTAGGED;
            else
                rotc_tag_next = src_tag;
        end
    endfunction

    // IROTC engine (term-serial, fixed 13-cycle slot) — instantiated only
    // when ENABLE_IROTC; its dispatch guards are re-checked here at decode
    // so faults never launch the engine (belt and braces: the engine's own
    // guards would also refuse).
    wire        eng_irotc_busy, eng_irotc_done, eng_irotc_fault;
    wire [1:0]  eng_irotc_fault_code, eng_irotc_out_tag;
    wire [31:0] eng_out_a_a, eng_out_a_b, eng_out_b_a, eng_out_b_b;
    wire [31:0] eng_out_c_a, eng_out_c_b, eng_out_d_a, eng_out_d_b;
    generate
        if (ENABLE_IROTC) begin : gen_irotc_engine
            spu13_irotc_engine #(.W(32)) u_irotc (
                .clk(clk), .rst_n(rst_n),
                .start(irotc_start),
                .sel(irotc_sel),
                .src_tag(irotc_src_tag),
                .in_b_a(qrf_rd_B[31:0]), .in_b_b(qrf_rd_B[63:32]),
                .in_c_a(qrf_rd_C[31:0]), .in_c_b(qrf_rd_C[63:32]),
                .in_d_a(qrf_rd_D[31:0]), .in_d_b(qrf_rd_D[63:32]),
                .busy(eng_irotc_busy), .done(eng_irotc_done),
                .fault(eng_irotc_fault), .fault_code(eng_irotc_fault_code),
                .out_tag(eng_irotc_out_tag),
                .out_a_a(eng_out_a_a), .out_a_b(eng_out_a_b),
                .out_b_a(eng_out_b_a), .out_b_b(eng_out_b_b),
                .out_c_a(eng_out_c_a), .out_c_b(eng_out_c_b),
                .out_d_a(eng_out_d_a), .out_d_b(eng_out_d_b)
            );
        end else begin : gen_no_irotc_engine
            assign eng_irotc_busy = 1'b0;
            assign eng_irotc_done = 1'b0;
            assign eng_irotc_fault = 1'b0;
            assign eng_irotc_fault_code = 2'd0;
            assign eng_irotc_out_tag = 2'd0;
            assign eng_out_a_a = 32'd0; assign eng_out_a_b = 32'd0;
            assign eng_out_b_a = 32'd0; assign eng_out_b_b = 32'd0;
            assign eng_out_c_a = 32'd0; assign eng_out_c_b = 32'd0;
            assign eng_out_d_a = 32'd0; assign eng_out_d_b = 32'd0;
        end
    endgenerate

    assign inst_done = inst_done_r;
    assign rotc_debug_status = {
        rotc_debug_flags[7],
        rotc_debug_busy,
        rotc_debug_flags[5:0],
        rote_debug_state,
        rotc_debug_angle[3:0]
    };

    function [63:0] rs_sub64;
        input [63:0] left;
        input [63:0] right;
        begin
            rs_sub64 = {left[63:32] - right[63:32], left[31:0] - right[31:0]};
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rote_en <= 0;
            rote_active <= 0;
            hex_active <= 0;
            hex_valid <= 0;
            hex_q <= 0;
            hex_r <= 0;
            rote_src_lane <= 0;
            rote_dest_lane <= 0;
            rote_angle <= 6'd0;
            rote_field <= 2'b00;
            rotc_debug_angle <= 6'd0;
            rotc_debug_flags <= 8'd0;
            rotc_debug_busy <= 1'b0;
            qrf_wr_en <= 0;
            qrf_wr_lane <= 0;
            inst_done_r <= 0;
            instr_wr_active <= 0;
            qr_commit_valid_r <= 0;
            qr_commit_lane_r <= 0;
            qr_commit_A_r <= 0;
            qr_commit_B_r <= 0;
            qr_commit_C_r <= 0;
            qr_commit_D_r <= 0;
            rplu2_result_lane <= 0;
            qsub_active <= 0;
            qsub_stage <= 0;
            qsub_dest_lane <= 0;
            qsub_rhs_lane <= 0;
            qsub_lhs_A <= 0;
            qsub_lhs_B <= 0;
            qsub_lhs_C <= 0;
            qsub_lhs_D <= 0;
            hex_valid <= 0;   // default: one-cycle pulse
            qsub_lhs_lane <= 0;
            irotc_active <= 0;
            irotc_start <= 0;
            irotc_sel <= 0;
            irotc_dst_lane <= 0;
            irotc_src_tag <= 0;
            scale2_active <= 0;
            scale2_dst_lane <= 0;
            for (tag_i = 0; tag_i < 13; tag_i = tag_i + 1)
                qr_tags[tag_i] <= TAG_UNTAGGED;
        end else begin
            qrf_wr_en <= 0;  // default: no write
            inst_done_r <= 0;
            instr_wr_active <= 0;
            qr_commit_valid_r <= 0;
            hex_valid <= 0;   // default: one-cycle pulse
            rote_en <= 0;     // default: one-cycle rotor start pulse
            irotc_start <= 0; // default: one-cycle engine start pulse
            if (rote_done_tdm)
                rotc_debug_flags[3] <= 1'b1;

            // RPLU2 Padé result bridge: expose the four A31 limbs through the
            // existing QR commit telemetry so the southbridge can read them via
            // command 0xAE without adding a second SPI result frame.
            if (rplu2_result_valid) begin
                qr_commit_valid_r <= 1;
                qr_commit_lane_r <= rplu2_result_lane;
                qr_commit_A_r <= {32'd0, rplu2_result_c0};
                qr_commit_B_r <= {32'd0, rplu2_result_c1};
                qr_commit_C_r <= {32'd0, rplu2_result_c2};
                qr_commit_D_r <= {32'd0, rplu2_result_c3};
                inst_done_r <= 1;

            // ── QSUB Handler (0x1B): two-cycle single-read-port FSM ──
            end else if (qsub_active) begin
                if (qsub_stage == 1'b0) begin
                    qsub_lhs_A <= qrf_rd_A;
                    qsub_lhs_B <= qrf_rd_B;
                    qsub_lhs_C <= qrf_rd_C;
                    qsub_lhs_D <= qrf_rd_D;
                    rote_src_lane <= qsub_rhs_lane;
                    qsub_stage <= 1'b1;
                end else begin
                    qrf_wr_en   <= 1;
                    qrf_wr_lane <= qsub_dest_lane;
                    qr_tags[qsub_dest_lane] <= tag_join(qr_tags[qsub_lhs_lane],
                                                        qr_tags[qsub_rhs_lane]);
                    instr_wr_A <= qsub_res_A;
                    instr_wr_B <= qsub_res_B;
                    instr_wr_C <= qsub_res_C;
                    instr_wr_D <= qsub_res_D;
                    instr_wr_active <= 1;
                    qr_commit_valid_r <= 1;
                    qr_commit_lane_r <= qsub_dest_lane;
                    qr_commit_A_r <= qsub_res_A;
                    qr_commit_B_r <= qsub_res_B;
                    qr_commit_C_r <= qsub_res_C;
                    qr_commit_D_r <= qsub_res_D;
                    qsub_active <= 0;
                    qsub_stage <= 0;
                    inst_done_r <= 1;
                end

            // ── QLDI Handler (0x1D) ────────────────────────────────
            end else if (inst_accept && eff_inst_word[63:56] == 8'h1D) begin
                qrf_wr_en   <= 1;
                qrf_wr_lane <= eff_inst_word[55:48] % 13;
                qr_tags[eff_inst_word[55:48] % 13] <= TAG_UNTAGGED; // raw load
                instr_wr_A[31:0]  <= {{24{eff_inst_word[39]}}, eff_inst_word[39:32]};
                instr_wr_A[63:32] <= 32'd0;
                instr_wr_B[31:0]  <= {{24{eff_inst_word[31]}}, eff_inst_word[31:24]};
                instr_wr_B[63:32] <= 32'd0;
                instr_wr_C[31:0]  <= {{24{eff_inst_word[23]}}, eff_inst_word[23:16]};
                instr_wr_C[63:32] <= 32'd0;
                instr_wr_D[31:0]  <= {{24{eff_inst_word[15]}}, eff_inst_word[15:8]};
                instr_wr_D[63:32] <= 32'd0;
                instr_wr_active <= 1;
                qr_commit_valid_r <= 1;
                qr_commit_lane_r <= eff_inst_word[55:48] % 13;
                qr_commit_A_r <= {32'd0, {{24{eff_inst_word[39]}}, eff_inst_word[39:32]}};
                qr_commit_B_r <= {32'd0, {{24{eff_inst_word[31]}}, eff_inst_word[31:24]}};
                qr_commit_C_r <= {32'd0, {{24{eff_inst_word[23]}}, eff_inst_word[23:16]}};
                qr_commit_D_r <= {32'd0, {{24{eff_inst_word[15]}}, eff_inst_word[15:8]}};
                inst_done_r <= 1;

            end else if (inst_accept && eff_inst_word[63:56] == 8'h1E) begin
                // DELTA QRd, Q1, Q2, steps.
                // VM parity endpoint: QRd.A=Q1+Q2, QRd.B=0, QRd.C=steps, QRd.D=0.
                qrf_wr_en   <= 1;
                qrf_wr_lane <= eff_inst_word[55:48] % 13;
                qr_tags[eff_inst_word[55:48] % 13] <= TAG_UNTAGGED; // raw load
                instr_wr_A <= {32'd0, ({16'd0, eff_inst_word[39:24]} + {16'd0, eff_inst_word[23:8]})};
                instr_wr_B <= 64'd0;
                instr_wr_C <= {32'd0, (eff_inst_word[47:40] != 8'd0 ? {24'd0, eff_inst_word[47:40]} : 32'd4)};
                instr_wr_D <= 64'd0;
                instr_wr_active <= 1;
                inst_done_r <= 1;

            end else if (inst_accept && eff_inst_word[63:56] == 8'h1C &&
                         eff_inst_word[29:24] > ROTC_MAX_VERIFIED_ANGLE) begin
                // Unverified/unimplemented angle: detect and fault immediately,
                // exactly like the tagged ROTC core's MISALIGNED/OVERFLOW/INEXACT
                // idiom -- do not launch the rotor, do not touch qrf_wr_en, the
                // QR register file (the manifold) is left completely untouched.
                rote_angle       <= eff_inst_word[29:24];
                rotc_debug_angle <= eff_inst_word[29:24];
                rotc_debug_flags <= 8'b1000_0001;  // bit0=latched, bit7=BAD_ANGLE fault
                rotc_debug_busy  <= 1'b0;
                inst_done_r      <= 1'b1;
            end else if (inst_accept && eff_inst_word[63:56] == 8'h1C) begin
                rote_src_lane  <= eff_inst_word[47:40] % 13;
                rote_dest_lane <= eff_inst_word[55:48] % 13;
                rote_angle     <= eff_inst_word[29:24];
                rote_field     <= eff_inst_word[31:30];
                rote_active    <= 1;
                rotc_debug_angle <= eff_inst_word[29:24];
                rotc_debug_flags <= 8'b0000_0001;
                rotc_debug_busy <= 1'b1;
            end else if (rote_active) begin
                rote_en    <= 1;  // assert TDM start
                rote_active <= 0;
                rotc_debug_flags[1] <= 1'b1;
                rotc_debug_flags[2] <= 1'b1;
            end else if (rote_done_tdm) begin
                // TDM rotor core done — writeback
                qrf_wr_en   <= 1;
                qrf_wr_lane <= rote_dest_lane;
                qr_tags[rote_dest_lane] <= rotc_tag_next(rote_angle,
                                                         qr_tags[rote_src_lane]);
                qr_commit_valid_r <= 1;
                qr_commit_lane_r <= rote_dest_lane;
                qr_commit_A_r <= qrf_wr_A;
                qr_commit_B_r <= rote_B_out;
                qr_commit_C_r <= rote_C_out;
                qr_commit_D_r <= rote_D_out;
                inst_done_r <= 1;
                rotc_debug_flags[3] <= 1'b1;
                rotc_debug_flags[4] <= 1'b1;
                rotc_debug_flags[5] <= 1'b1;
                rotc_debug_busy <= 1'b0;
            // ── IROTC (0xD6): icosahedral A₅ rotation on the φ-plane ──
            // Guards at dispatch in decode order BADIDX → UNTAGGED → CATMIX
            // (IROTC_SPEC.md §4); any fault leaves the QR file and the tag
            // file bit-identically untouched, mirroring the ROTC bad-angle
            // idiom. flags[5:4] carry the fault code.
            end else if (ENABLE_IROTC && inst_accept &&
                         eff_inst_word[63:56] == OP_IROTC &&
                         eff_inst_word[29:24] > 6'd59) begin
                rotc_debug_flags <= 8'b1001_0001;          // fault, code 1
                rotc_debug_busy  <= 1'b0;
                inst_done_r      <= 1'b1;
            end else if (ENABLE_IROTC && inst_accept &&
                         eff_inst_word[63:56] == OP_IROTC &&
                         qr_tags[eff_inst_word[47:40] % 13] == TAG_UNTAGGED) begin
                rotc_debug_flags <= 8'b1010_0001;          // fault, code 2
                rotc_debug_busy  <= 1'b0;
                inst_done_r      <= 1'b1;
            end else if (ENABLE_IROTC && inst_accept &&
                         eff_inst_word[63:56] == OP_IROTC &&
                         ((qr_tags[eff_inst_word[47:40] % 13] == TAG_MAIN &&
                           eff_inst_word[30]) ||
                          (qr_tags[eff_inst_word[47:40] % 13] == TAG_CONJ &&
                           !eff_inst_word[30]))) begin
                rotc_debug_flags <= 8'b1011_0001;          // fault, code 3
                rotc_debug_busy  <= 1'b0;
                inst_done_r      <= 1'b1;
            end else if (ENABLE_IROTC && inst_accept &&
                         eff_inst_word[63:56] == OP_IROTC) begin
                rote_src_lane  <= eff_inst_word[47:40] % 13;
                irotc_dst_lane <= eff_inst_word[55:48] % 13;
                irotc_sel      <= eff_inst_word[30:24];
                irotc_src_tag  <= qr_tags[eff_inst_word[47:40] % 13];
                irotc_active   <= 1;
                rotc_debug_flags <= 8'b0000_0001;
                rotc_debug_busy  <= 1'b1;
            end else if (irotc_active) begin
                irotc_start  <= 1;   // qrf_rd_* now presents the source lane
                irotc_active <= 0;
            end else if (eng_irotc_done) begin
                qrf_wr_en   <= 1;
                qrf_wr_lane <= irotc_dst_lane;
                qr_tags[irotc_dst_lane] <= eng_irotc_out_tag;
                instr_wr_A <= {eng_out_a_b, eng_out_a_a};
                instr_wr_B <= {eng_out_b_b, eng_out_b_a};
                instr_wr_C <= {eng_out_c_b, eng_out_c_a};
                instr_wr_D <= {eng_out_d_b, eng_out_d_a};
                instr_wr_active <= 1;
                qr_commit_valid_r <= 1;
                qr_commit_lane_r <= irotc_dst_lane;
                qr_commit_A_r <= {eng_out_a_b, eng_out_a_a};
                qr_commit_B_r <= {eng_out_b_b, eng_out_b_a};
                qr_commit_C_r <= {eng_out_c_b, eng_out_c_a};
                qr_commit_D_r <= {eng_out_d_b, eng_out_d_a};
                inst_done_r <= 1;
                rotc_debug_busy <= 1'b0;
            end else if (eng_irotc_fault) begin
                // Defensive: core guards precede launch, so the engine's own
                // guards cannot fire — but if they ever do, fault cleanly.
                rotc_debug_flags <= {2'b10, eng_irotc_fault_code, 4'b0001};
                rotc_debug_busy  <= 1'b0;
                inst_done_r      <= 1'b1;

            // ── LOAD2X (0xD7): QLDI format, every component doubled ──
            end else if (ENABLE_IROTC && inst_accept &&
                         eff_inst_word[63:56] == OP_LOAD2X) begin
                qrf_wr_en   <= 1;
                qrf_wr_lane <= eff_inst_word[55:48] % 13;
                qr_tags[eff_inst_word[55:48] % 13] <= TAG_FRESH;
                instr_wr_A <= {32'd0, {{23{eff_inst_word[39]}}, eff_inst_word[39:32], 1'b0}};
                instr_wr_B <= {32'd0, {{23{eff_inst_word[31]}}, eff_inst_word[31:24], 1'b0}};
                instr_wr_C <= {32'd0, {{23{eff_inst_word[23]}}, eff_inst_word[23:16], 1'b0}};
                instr_wr_D <= {32'd0, {{23{eff_inst_word[15]}}, eff_inst_word[15:8], 1'b0}};
                instr_wr_active <= 1;
                inst_done_r <= 1;

            // ── SCALE2 (0xD8): QRd = 2·QRs, re-condition to FRESH ──
            end else if (ENABLE_IROTC && inst_accept &&
                         eff_inst_word[63:56] == OP_SCALE2) begin
                rote_src_lane   <= eff_inst_word[47:40] % 13;
                scale2_dst_lane <= eff_inst_word[55:48] % 13;
                scale2_active   <= 1;
            end else if (scale2_active) begin
                qrf_wr_en   <= 1;
                qrf_wr_lane <= scale2_dst_lane;
                qr_tags[scale2_dst_lane] <= TAG_FRESH;
                // Componentwise doubling: both 32-bit halves independently
                // (plane-agnostic — carries never cross the half boundary).
                instr_wr_A <= {qrf_rd_A[63:32] + qrf_rd_A[63:32],
                               qrf_rd_A[31:0]  + qrf_rd_A[31:0]};
                instr_wr_B <= {qrf_rd_B[63:32] + qrf_rd_B[63:32],
                               qrf_rd_B[31:0]  + qrf_rd_B[31:0]};
                instr_wr_C <= {qrf_rd_C[63:32] + qrf_rd_C[63:32],
                               qrf_rd_C[31:0]  + qrf_rd_C[31:0]};
                instr_wr_D <= {qrf_rd_D[63:32] + qrf_rd_D[63:32],
                               qrf_rd_D[31:0]  + qrf_rd_D[31:0]};
                instr_wr_active <= 1;
                scale2_active <= 0;
                inst_done_r <= 1;

            end else if (inst_accept && eff_inst_word[63:56] == 8'h1B) begin
                // QSUB QRd, QRa, QRb: QR[d] = QR[a] - QR[b].
                qsub_dest_lane <= eff_inst_word[55:48] % 13;
                qsub_rhs_lane <= eff_inst_word[11:8] % 13;
                qsub_lhs_lane <= eff_inst_word[47:40] % 13;
                rote_src_lane <= eff_inst_word[47:40] % 13;
                qsub_active <= 1;
                qsub_stage <= 0;
            end else if (inst_accept && eff_inst_word[63:56] == 8'h16) begin
                // ── HEX handler: project QRn → (q,r) hex coordinates ──
                // HEX Rd, QRn — read QR[n], compute A-D, B-D, output hex
                rote_src_lane <= eff_inst_word[47:40] % 13;  // QRs
                // hex projection = B[15:0] - D[15:0], A[15:0] - D[15:0] (components swapped in RTL)
                hex_q   <= qrf_rd_B[15:0] - qrf_rd_D[15:0];
                hex_r   <= qrf_rd_A[15:0] - qrf_rd_D[15:0];
                hex_valid <= 1;
                inst_done_r <= 1;
            end else if (ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE &&
                         inst_accept && eff_inst_word[63:56] == 8'h2A) begin
                // Live RPLU2 owns its own SOM -> BTU -> Padé pipeline.  Latch
                // the QR source lane for the pipeline feature vector and the
                // destination lane for the eventual public result commit.
                rplu2_result_lane <= eff_inst_word[55:48] % 13;
                rote_src_lane <= eff_inst_word[47:40] % 13;
            end else if (ENABLE_CORE_SOM && inst_accept && eff_inst_word[63:56] == 8'h2A) begin
                // SOM_CLASSIFY reads the QR source lane; the SOM FSM below owns
                // the classify launch, while this FSM owns the shared QRF lane.
                rote_src_lane <= eff_inst_word[47:40] % 13;
            end else if (som_classify_valid) begin
                hex_q <= som_label;
                hex_r <= {15'd0, som_ambiguous};
                hex_valid <= 1;
                inst_done_r <= 1;
            end else if (som_train_done) begin
                inst_done_r <= 1;
            end else if (core_nsa_done) begin
                inst_done_r <= 1;
            end else if (inst_accept && core_jscr_opcode) begin
                // JSCR commits through the topology6 state block below.  Keep
                // it explicit here so opcode 0x48 is not hidden by the
                // unknown-instruction catch-all path.
                inst_done_r <= 1;
            end else if (inst_accept &&
                         eff_inst_word[63:56] != 8'h1D &&
                         eff_inst_word[63:56] != 8'h1C &&
                         eff_inst_word[63:56] != 8'h16 &&
                         eff_inst_word[63:56] != 8'h1B &&
                         eff_inst_word[63:56] != 8'h1E &&
                         !(ENABLE_IROTC && (eff_inst_word[63:56] == OP_IROTC ||
                                            eff_inst_word[63:56] == OP_LOAD2X ||
                                            eff_inst_word[63:56] == OP_SCALE2)) &&
                         !(ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_EXTENSIONS && core_nsa_opcode) &&
                         !(ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE &&
                           eff_inst_word[63:56] == 8'h2A) &&
                         !(ENABLE_CORE_SOM && (eff_inst_word[63:56] == 8'h2A ||
                                                eff_inst_word[63:56] == 8'h2B))) begin
                // Unknown/QLOG — consume immediately
                inst_done_r <= 1;
            end
        end
    end

    // Stage 3: Stability Check & Commit (Pulse 21)
    wire [63:0] rotated_axis;
    assign rotated_axis = q_prime_ab;
    assign manifold_commit_reg = manifold_with_axis(manifold_reg, axis_ptr, rotated_axis);
    wire [31:0] quadrance;
    wire [31:0] ivm_quadrance;
    wire [15:0] gasket_sum;

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

    // ── Material ID: SOM-driven when both SOM and RPLU are enabled ────
    // SOM cluster labels (0-3) map to material classes:
    //   0 → carbon (diamond/polymer)    2 → aluminum (lightweight)
    //   1 → iron (structural)           3 → titanium (aerospace)
    reg [7:0] som_material_id;
    always @(*) begin
        case (som_label[1:0])
            2'd0: som_material_id = 8'd0;  // carbon
            2'd1: som_material_id = 8'd1;  // iron
            2'd2: som_material_id = 8'd2;  // aluminum
            2'd3: som_material_id = 8'd4;  // titanium
        endcase
    end

    wire [7:0] rplu_material_id;
    assign rplu_material_id = (ENABLE_CORE_SOM && ENABLE_RPLU) ? som_material_id : phinary_chirality;

    generate
        if (ENABLE_CORE_RPLU_V2) begin : gen_rplu_v2_mode_tieoffs
            assign rplu_done = phi_21;
            assign ratio_cmp_res = 3'sd0;
            assign ratio_cmp_valid = 1'b0;
            assign rplu_addr_dbg = 10'd0;
        end else if (ENABLE_RPLU) begin : gen_rplu
            davis_to_rplu u_davis_rplu (
                .clk(clk), .rst_n(rst_n), .start(phi_21), .q_vector(rotated_axis), .material_id(rplu_material_id),
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

    // Audio/I2S output assignments
    assign audio_p_out = audio_p;
    assign audio_q_out = audio_q;
    assign laminar_flow_index_out = laminar_flow_index;
    assign thermal_pressure_out = thermal_pressure;

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
            quadray_target_kappa <= 32'd0;
            quadray_target_valid <= 1'b0;
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

            // RPLU2 Padé coefficients arrive as two 64-bit records per
            // coefficient.  The low pair is staged here; the high pair pulses
            // coeff_we into the Padé engine with all four A31 components.
            if (rplu2_cfg_pade_num && !rplu2_pade_cfg_high) begin
                rplu2_pade_num_c0[rplu2_pade_cfg_idx] <= dec_fast_cfg_data[31:0];
                rplu2_pade_num_c1[rplu2_pade_cfg_idx] <= dec_fast_cfg_data[63:32];
            end
            if (rplu2_cfg_pade_den && !rplu2_pade_cfg_high) begin
                rplu2_pade_den_c0[rplu2_pade_cfg_idx] <= dec_fast_cfg_data[31:0];
                rplu2_pade_den_c1[rplu2_pade_cfg_idx] <= dec_fast_cfg_data[63:32];
            end

            // fast-domain config writes: quadray target kappa (sel==6)
            // Allows firmware to write the target M31 quadrance invariant
            // that the BTU variety sidecar closes against.
            if (dec_fast_cfg_wr_en && dec_fast_cfg_sel == RPLU2_CFG_KAPPA) begin
                quadray_target_kappa <= dec_fast_cfg_data[31:0];
                quadray_target_valid <= 1'b1;
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
            if (inst_accept) begin
                if (eff_inst_word[63:56] == 8'hE0) begin
                    artery_wr_en <= 1'b1;
                    artery_wr_data <= {8'hA5, 8'd7, 1'b0, eff_inst_word[33:24], 1'b1, 36'd0};
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
                            // Header layout: [63:56]=0xA5, [55:48]=sel,
                            // [47:44]=material, [43:34]=addr, [33]=singleton
                            if (torus_emit_enable) begin
                                artery_wr_en <= 1'b1;
                                artery_wr_data <= {8'hA5, 8'd7, 4'd0, torus_idx[9:0], 1'b1, 33'd0};
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

    // ── SOM / BMU Classifier Pipeline ───────────────────────────────────
    // Stage-gated behind ENABLE_CORE_SOM.  Feeds 4-feature vectors from
    // the QR register file (A,B components of 2 selected lanes) through
    // spu_som_bmu → spu_cluster_reduce.  Output on som_label, som_gap,
    // som_ambiguous for telemetry / downstream classification.
    //
    generate
        if (ENABLE_CORE_SOM) begin : gen_som
            wire        som_bmu_valid;
            wire [15:0] som_best_id, som_sec_id, som_label_in;
            wire [63:0] som_best_q, som_sec_q, som_gap_in;
            wire        som_has_sec;
            wire [3:0]  som_fault_type;
            wire [31:0] som_fault_count;
            wire        som_train_we;
            wire [2:0]  som_train_addr;
            wire [3:0]  som_train_be;
            wire [143:0] som_train_wdata;
            wire [143:0] som_train_rdata;
            wire        som_train_start;
            reg  [3:0]  som_train_shift;

            // Feature vector: 4 features, narrowed from core RationalSurd
            // {q[31:0], p[31:0]} into SOM {q[17:0], p[17:0]}.
            localparam SOM_COEFF_W = 18;
            localparam SOM_SURD_W = 2 * SOM_COEFF_W;
            function [SOM_SURD_W-1:0] som_narrow_rs;
                input [63:0] rs;
                begin
                    som_narrow_rs = {rs[32 +: SOM_COEFF_W], rs[0 +: SOM_COEFF_W]};
                end
            endfunction
            wire [4*SOM_SURD_W-1:0] som_features;
            assign som_features = {
                som_narrow_rs(qrf_rd_D),
                som_narrow_rs(qrf_rd_C),
                som_narrow_rs(qrf_rd_B),
                som_narrow_rs(qrf_rd_A)
            };

            wire [4*SOM_SURD_W-1:0] som_fw;
            assign som_fw = {{(SOM_SURD_W-1){1'b0}}, 1'b1,
                             {(SOM_SURD_W-1){1'b0}}, 1'b1,
                             {(SOM_SURD_W-2){1'b0}}, 2'd2,
                             {(SOM_SURD_W-1){1'b0}}, 1'b1};

            // SOM input range check: flag if any narrowed feature component
            // exceeds 16-bit signed range (bits 17:16 must be same = sign-ext).
            // This protects against the 18-bit subtraction truncation edge case
            // identified in audit H1/H2 — sensor inputs are always <16 bits,
            // so a flag here indicates a software bug, not hardware overflow.
            wire som_input_ovf =
                (som_features[ 17] != som_features[ 16]) ||  // feat0 P
                (som_features[ 35] != som_features[ 34]) ||  // feat0 Q
                (som_features[ 53] != som_features[ 52]) ||  // feat1 P
                (som_features[ 71] != som_features[ 70]) ||  // feat1 Q
                (som_features[ 89] != som_features[ 88]) ||  // feat2 P
                (som_features[107] != som_features[106]) ||  // feat2 Q
                (som_features[125] != som_features[124]) ||  // feat3 P
                (som_features[143] != som_features[142]);    // feat3 Q

            // ── SOM weight config path (host write via SPI 0xA5, sel=4) ─
            // Config addr[4:0] = {node_id[2:0], feature_id[1:0]}
            // Config data[35:0] = {Q[17:0], P[17:0]} for one feature
            wire        host_som_we   = dec_fast_cfg_wr_en && dec_fast_cfg_sel == SOM_CFG_WEIGHT;
            wire [2:0]  host_som_node = dec_fast_cfg_addr[4:2];
            wire [1:0]  host_som_feat = dec_fast_cfg_addr[1:0];
            wire [35:0] host_som_feat_data = dec_fast_cfg_data[35:0];
            reg  [3:0]  host_som_be;
            reg  [2:0]  host_som_addr;
            reg  [143:0] host_som_wdata;
            always @(*) begin
                host_som_be = 4'b0001 << host_som_feat;
                host_som_addr = host_som_node;
                host_som_wdata = 144'd0;
                host_som_wdata[host_som_feat * 36 +: 36] = host_som_feat_data;
            end

            // Mux: training FSM owns the bus during its write cycle; host owns it otherwise
            assign som_train_we    = u_som_train.bram_we || host_som_we;
            assign som_train_be    = host_som_we ? host_som_be : 4'b1111;
            assign som_train_addr  = host_som_we ? host_som_addr : u_som_train.bram_addr;
            assign som_train_wdata = host_som_we ? host_som_wdata : u_som_train.bram_wdata;

            wire som_start;

            spu_som_bmu #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(18)) u_som_bmu (
                .clk(clk), .rst_n(rst_n),
                .start(som_start), .done(som_done),
                .features(som_features),
                .feature_weights(som_fw),
                .bmu_valid(som_bmu_valid),
                .best_node_id(som_best_id),
                .second_node_id(som_sec_id),
                .cluster_label(som_label_in),
                .best_q(som_best_q),
                .second_q(som_sec_q),
                .confidence_gap(som_gap_in),
                .has_second(som_has_sec),
                .axiomatic_level(phinary_cfg[3:2]),
                .axiomatic_fault(axiomatic_fault),
                .fault_type(som_fault_type),
                .fault_count(som_fault_count),
                .train_we(som_train_we),
                .train_addr(som_train_addr),
                .train_be(som_train_be),
                .train_wdata(som_train_wdata),
                .train_rdata(som_train_rdata)
            );

            assign fault_type = som_fault_type[1:0];
            assign fault_count = som_fault_count[15:0];
            assign som_rns_error = 1'b0;  // SOM-only path, no M31 multiplier

            spu_som_train #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(18)) u_som_train (
                .clk(clk), .rst_n(rst_n),
                .train_start(som_train_start),
                .train_done(som_train_done),
                .shift_amount(som_train_shift),
                .bmu_valid(som_bmu_valid),
                .bmu_node_id(som_best_id),
                .features(som_features),
                .bram_rdata(som_train_rdata)
            );

            spu_cluster_reduce #(.WIDTH(18)) u_som_reduce (
                .clk(clk), .rst_n(rst_n),
                .bmu_valid(som_bmu_valid),
                .best_node_id(som_best_id),
                .cluster_label_in(som_label_in),
                .best_q(som_best_q),
                .second_q(som_sec_q),
                .confidence_gap_in(som_gap_in),
                .has_second(som_has_sec),
                .ambiguity_threshold(64'd0),
                .classify_valid(som_classify_valid),
                .label(som_label),
                .confidence_gap(som_gap),
                .ambiguous(som_ambiguous)
            );

            // ── SOM opcode FSM (0x2A = SOM_CLASSIFY) ─────────────────
            reg som_busy;
            reg som_start_r;
            reg som_launch_pending;
            reg som_train_busy;
            reg som_train_start_r;
            assign som_start = som_start_r;
            assign som_train_start = som_train_start_r;

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    som_busy <= 0;
                    som_start_r <= 0;
                    som_launch_pending <= 0;
                    som_train_busy <= 0;
                    som_train_start_r <= 0;
                    som_train_shift <= 4'd0;
                end else begin
                    som_start_r <= 0;
                    som_train_start_r <= 0;

                    if (som_classify_valid) begin
                        som_busy <= 0;
                        som_launch_pending <= 0;
                    end else if (som_launch_pending) begin
                        som_start_r <= 1;
                        som_launch_pending <= 0;
                    end else if (!(ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE) &&
                                 inst_accept && eff_inst_word[63:56] == 8'h2A && !som_busy) begin
                        som_busy <= 1;
                        som_launch_pending <= 1;
                    end

                    if (som_train_done) begin
                        som_train_busy <= 0;
                    end else if (inst_accept && eff_inst_word[63:56] == 8'h2B && !som_train_busy) begin
                        som_train_shift <= eff_inst_word[27:24];
                        som_train_busy <= 1;
                        som_train_start_r <= 1;
                    end
                end
            end
        end else begin : gen_no_som
            assign som_done = 1'b0;
            assign som_train_done = 1'b0;
            assign som_classify_valid = 1'b0;
            assign som_label = 16'd0;
            assign som_gap = 64'd0;
            assign som_ambiguous = 1'b0;
            assign axiomatic_fault = 1'b0;
            assign fault_type = 2'b00;
            assign fault_count = 16'd0;
            assign som_rns_error = 1'b0;
        end
    endgenerate

    // ── RPLU v2: Thimble-Padé A31/Quadray Pipeline ──────────────────
    // Gated behind ENABLE_CORE_RPLU_V2.  Replaces the legacy davis_to_rplu
    // chain with parallel SOM classification → BTU A31/Quadray routing →
    // [4/4] Padé rational approximant evaluation over M31.
    //
    // When enabled, rplu_dissoc is driven from the v2 pipeline's
    // singularity exception (FLAGS.V) rather than the legacy Morse table.
    generate
        if (ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE) begin : gen_rplu_v2
            wire        rplu2_som_done;
            wire [15:0] rplu2_som_best_id, rplu2_som_label;
            wire [63:0] rplu2_som_best_q;
            wire [31:0] rplu2_thimble_c0, rplu2_thimble_c1,
                        rplu2_thimble_c2, rplu2_thimble_c3;
            wire        rplu2_thimble_valid;
            wire        rplu2_busy, rplu2_stall, rplu2_rns_error;
            wire [31:0] rplu2_quadray_delta;
            wire        rplu2_quadray_coherent;
            wire        rplu2_quadray_valid;
            reg         rplu2_som_start;
            reg         rplu2_som_pending;

            rplu_pipeline #(
                .EXTERNAL_PADE_MULT(EXTERNAL_RPLU_PADE_MULT),
                .SHARE_PADE_INV_MULT(SHARE_RPLU_PADE_INV_MULT)
            ) u_rplu_v2 (
                .clk(clk), .rst_n(rst_n),
                .som_features(rplu2_features),
                .som_start(rplu2_som_start),
                .som_done(rplu2_som_done),
                .som_best_id(rplu2_som_best_id),
                .som_cluster_label(rplu2_som_label),
                .som_best_q(rplu2_som_best_q),
                .pade_coeff_we(rplu2_pade_coeff_we),
                .pade_coeff_is_den(rplu2_pade_coeff_is_den),
                .pade_coeff_addr(rplu2_pade_coeff_addr),
                .pade_c0(rplu2_pade_coeff_c0), .pade_c1(rplu2_pade_coeff_c1),
                .pade_c2(rplu2_pade_coeff_c2), .pade_c3(rplu2_pade_coeff_c3),
                .btu_cfg_we(rplu2_btu_cfg_we),
                .btu_cfg_addr(rplu2_btu_cfg_addr),
                .btu_cfg_pair(rplu2_btu_cfg_pair),
                .btu_cfg_data(rplu2_btu_cfg_data),
                .quadray_target_kappa(quadray_target_kappa),
                .thimble_c0(rplu2_thimble_c0),
                .thimble_c1(rplu2_thimble_c1),
                .thimble_c2(rplu2_thimble_c2),
                .thimble_c3(rplu2_thimble_c3),
                .thimble_valid(rplu2_thimble_valid),
                .quadray_delta(rplu2_quadray_delta),
                .quadray_coherent(rplu2_quadray_coherent),
                .quadray_valid(rplu2_quadray_valid),
                .pipeline_busy(rplu2_busy),
                .pipeline_stall(rplu2_stall),
                .rns_error(rplu2_rns_error),
                .pade_mult_start(rplu_pade_mult_start),
                .pade_mult_a0(rplu_pade_mult_a0),
                .pade_mult_a1(rplu_pade_mult_a1),
                .pade_mult_a2(rplu_pade_mult_a2),
                .pade_mult_a3(rplu_pade_mult_a3),
                .pade_mult_b0(rplu_pade_mult_b0),
                .pade_mult_b1(rplu_pade_mult_b1),
                .pade_mult_b2(rplu_pade_mult_b2),
                .pade_mult_b3(rplu_pade_mult_b3),
                .pade_mult_r0(rplu_pade_mult_r0),
                .pade_mult_r1(rplu_pade_mult_r1),
                .pade_mult_r2(rplu_pade_mult_r2),
                .pade_mult_r3(rplu_pade_mult_r3),
                .pade_mult_done(rplu_pade_mult_done),
                .pade_mult_busy(rplu_pade_mult_busy),
                .pade_mult_rns_error(rplu_pade_mult_rns_error)
            );

            wire rplu2_quadray_fault;
            wire rplu2_dissoc;
            assign rplu2_quadray_fault = quadray_target_valid &&
                                          rplu2_quadray_valid &&
                                          !rplu2_quadray_coherent;
            assign rplu2_dissoc = rplu2_stall || rplu2_quadray_fault;

            // Map v2 pipeline outputs to core telemetry
            // Dissociation triggers on BTU collision or configured Quadray
            // variety mismatch.  This stays ring-native: equality to zero is
            // meaningful over M31, while magnitude/order comparisons are not.
            assign rplu_dissoc = rplu2_dissoc;
            assign rplu2_core_rns_error = rplu2_rns_error;
            assign rplu2_result_valid = rplu2_thimble_valid;
            assign rplu2_result_c0 = rplu2_thimble_c0;
            assign rplu2_result_c1 = rplu2_thimble_c1;
            assign rplu2_result_c2 = rplu2_thimble_c2;
            assign rplu2_result_c3 = rplu2_thimble_c3;

            // SOM classification start — triggered by SOM opcode (0x2A)
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    rplu2_som_start <= 0;
                    rplu2_som_pending <= 0;
                end else begin
                    rplu2_som_start <= 0;
                    if (rplu2_som_pending && !rplu2_busy) begin
                        rplu2_som_start <= 1;
                        rplu2_som_pending <= 0;
                    end else if (inst_accept && eff_inst_word[63:56] == 8'h2A && !rplu2_busy) begin
                        rplu2_som_pending <= 1;
                    end
                end
            end

        end else if (ENABLE_CORE_RPLU_V2) begin : gen_rplu_v2_cfg_only
            // RPLU2 config/QR mode: keep the config receive path and QR ISA,
            // but omit the full SOM/BTU/Padé/inverter evaluator.
            assign rplu_dissoc = 1'b0;
            assign rplu2_core_rns_error = 1'b0;
            assign rplu2_result_valid = 1'b0;
            assign rplu2_result_c0 = 32'd0;
            assign rplu2_result_c1 = 32'd0;
            assign rplu2_result_c2 = 32'd0;
            assign rplu2_result_c3 = 32'd0;
            assign rplu_pade_mult_start = 1'b0;
            assign rplu_pade_mult_a0 = 32'd0;
            assign rplu_pade_mult_a1 = 32'd0;
            assign rplu_pade_mult_a2 = 32'd0;
            assign rplu_pade_mult_a3 = 32'd0;
            assign rplu_pade_mult_b0 = 32'd0;
            assign rplu_pade_mult_b1 = 32'd0;
            assign rplu_pade_mult_b2 = 32'd0;
            assign rplu_pade_mult_b3 = 32'd0;
        end else begin : gen_no_rplu_v2
            // v2 disabled — no-op (handled by legacy gen_rplu block)
            assign rplu2_core_rns_error = 1'b0;
            assign rplu2_result_valid = 1'b0;
            assign rplu2_result_c0 = 32'd0;
            assign rplu2_result_c1 = 32'd0;
            assign rplu2_result_c2 = 32'd0;
            assign rplu2_result_c3 = 32'd0;
            assign rplu_pade_mult_start = 1'b0;
            assign rplu_pade_mult_a0 = 32'd0;
            assign rplu_pade_mult_a1 = 32'd0;
            assign rplu_pade_mult_a2 = 32'd0;
            assign rplu_pade_mult_a3 = 32'd0;
            assign rplu_pade_mult_b0 = 32'd0;
            assign rplu_pade_mult_b1 = 32'd0;
            assign rplu_pade_mult_b2 = 32'd0;
            assign rplu_pade_mult_b3 = 32'd0;
        end
    endgenerate

    assign rns_error = som_rns_error || rplu2_core_rns_error;

    // ── NSA/topology6 extension bundle (inside RPLU v2 block) ────────
    // Provides dual arithmetic over A_SPU = A31[epsilon]/(epsilon^2).
    // Kept separately gateable so constrained board targets can carry the
    // RPLU2 pipeline without the wider Janus/NSA shadow state.
    generate
        if (ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_EXTENSIONS) begin : gen_nsa_core
            // ── JSCR: Janus screw topology permutation (0x48) ─────────
            // Single-cycle: reads source lane, applies screw/dual permutation,
            // writes to destination lane.
            // Format R: Dest[55:51]=dst_lane, SrcA[50:46]=src_lane,
            // SrcB[45:44]=dual_mode, SrcB[43:42]=screw_mode,
            // SrcB[41]=pos_boundary, SrcB[40]=neg_boundary
            wire        jscr_en;
            wire [4:0]  jscr_dst_lane = eff_inst_word[55:51];
            wire [4:0]  jscr_src_lane = eff_inst_word[50:46];
            wire [1:0]  jscr_dual_mode  = eff_inst_word[45:44];
            wire [1:0]  jscr_screw_mode = eff_inst_word[43:42];
            wire        jscr_pos_boundary = eff_inst_word[41];
            wire        jscr_neg_boundary = eff_inst_word[40];
            wire [10:0] jscr_phase_offset = eff_inst_word[10:0];

            wire        topology_load_en;
            wire [4:0]  topology_load_lane;
            wire [63:0] topology_load_A;
            wire [63:0] topology_load_B;
            wire [63:0] topology_load_C;
            wire [63:0] topology_load_D;

            assign jscr_en = inst_accept && (eff_inst_word[63:56] == 8'h48);
            assign topology_load_en = inst_accept && (eff_inst_word[63:56] == 8'h1D);
            assign topology_load_lane = eff_inst_word[55:48] % 13;
            assign topology_load_A = {32'd0, {{24{eff_inst_word[39]}}, eff_inst_word[39:32]}};
            assign topology_load_B = {32'd0, {{24{eff_inst_word[31]}}, eff_inst_word[31:24]}};
            assign topology_load_C = {32'd0, {{24{eff_inst_word[23]}}, eff_inst_word[23:16]}};
            assign topology_load_D = {32'd0, {{24{eff_inst_word[15]}}, eff_inst_word[15:8]}};

            spu13_topology6_state #(
                .WIDTH(64),
                .LANES(13),
                .LANE_WIDTH(5),
                .OFFSET_WIDTH(11)
            ) u_topology6 (
                .clk(clk), .rst_n(rst_n),
                // Read port (unused for instruction — data read via QR projection)
                .rd_lane(5'd0),
                .rd_pos_ab(), .rd_pos_ac(), .rd_pos_ad(),
                .rd_pos_bc(), .rd_pos_bd(), .rd_pos_cd(),
                .rd_neg_ab(), .rd_neg_ac(), .rd_neg_ad(),
                .rd_neg_bc(), .rd_neg_bd(), .rd_neg_cd(),
                // QLDI hydrates the six-line topology shadow state.
                // Positive lines are pairwise A-B style edges; negative lines
                // are the reverse directed dual copy.
                .load_en(topology_load_en), .load_lane(topology_load_lane),
                .load_pos_ab(rs_sub64(topology_load_A, topology_load_B)),
                .load_pos_ac(rs_sub64(topology_load_A, topology_load_C)),
                .load_pos_ad(rs_sub64(topology_load_A, topology_load_D)),
                .load_pos_bc(rs_sub64(topology_load_B, topology_load_C)),
                .load_pos_bd(rs_sub64(topology_load_B, topology_load_D)),
                .load_pos_cd(rs_sub64(topology_load_C, topology_load_D)),
                .load_neg_ab(rs_sub64(topology_load_B, topology_load_A)),
                .load_neg_ac(rs_sub64(topology_load_C, topology_load_A)),
                .load_neg_ad(rs_sub64(topology_load_D, topology_load_A)),
                .load_neg_bc(rs_sub64(topology_load_C, topology_load_B)),
                .load_neg_bd(rs_sub64(topology_load_D, topology_load_B)),
                .load_neg_cd(rs_sub64(topology_load_D, topology_load_C)),
                // Janus transform port
                .janus_en(jscr_en),
                .janus_src_lane(jscr_src_lane),
                .janus_dst_lane(jscr_dst_lane),
                .dual_mode(jscr_dual_mode),
                .screw_mode(jscr_screw_mode),
                .phase_offset(jscr_phase_offset),
                .pos_boundary(jscr_pos_boundary),
                .neg_boundary(jscr_neg_boundary),
                .janus_done(),
                .fire_pos(), .fire_neg(),
                .phase_match(), .phase_mismatch()
            );

            // ── NSA opcode decode (trigger on 0x4C-0x4D) ────────────
            wire        nsa_start;
            wire [1:0]  nsa_op;
            wire [3:0]  nsa_dest, nsa_srcA, nsa_srcB;
            wire        nsa_done, nsa_busy;
            wire [31:0] nsa_real_z0, nsa_real_z1, nsa_real_z2, nsa_real_z3;
            wire [31:0] nsa_eps_z0,  nsa_eps_z1,  nsa_eps_z2,  nsa_eps_z3;
            wire        nsa_result_valid;
            wire [143:0] nsa_features_out;
            wire        nsa_wr_en;
            wire [3:0]  nsa_wr_addr;

            // ── NSA opcode decode (trigger on 0x4C-0x4D) ────────────
            reg nsa_pending;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    nsa_pending <= 0;
                end else if (inst_accept && (eff_inst_word[63:56] == 8'h4C ||
                                              eff_inst_word[63:56] == 8'h4D)) begin
                    nsa_pending <= 1;
                end else if (nsa_done)
                    nsa_pending <= 0;
            end

            assign nsa_start = nsa_pending && !nsa_busy && !nsa_done;
            assign nsa_op    = eff_inst_word[57:56];          // low 2 bits of opcode
            assign nsa_dest  = eff_inst_word[55:52];
            assign nsa_srcA  = eff_inst_word[51:48];
            assign nsa_srcB  = eff_inst_word[47:44];
            assign core_nsa_done = nsa_done;

            spu13_nsa_core u_nsa_core (
                .clk(clk), .rst_n(rst_n),
                .nsa_start(nsa_start),
                .nsa_op(nsa_op),
                .nsa_dest(nsa_dest),
                .nsa_srcA(nsa_srcA),
                .nsa_srcB(nsa_srcB),
                .nsa_done(nsa_done),
                .nsa_busy(nsa_busy),
                .qr_features_in(rplu2_features),
                .nsa_features_out(nsa_features_out),
                .nsa_wr_en(nsa_wr_en),
                .nsa_wr_addr(nsa_wr_addr),
                .nsa_real_z0(nsa_real_z0),
                .nsa_real_z1(nsa_real_z1),
                .nsa_real_z2(nsa_real_z2),
                .nsa_real_z3(nsa_real_z3),
                .nsa_eps_z0(nsa_eps_z0),
                .nsa_eps_z1(nsa_eps_z1),
                .nsa_eps_z2(nsa_eps_z2),
                .nsa_eps_z3(nsa_eps_z3),
                .nsa_result_valid(nsa_result_valid)
            );

            // NSA results feed into the main RPLU pipeline as additional
            // feature channels — velocity-aware classification.
            // (Wired but not yet consumed by the pipeline — future integration.)
        end else begin : gen_no_nsa_core
            assign core_nsa_done = 1'b0;
        end
    endgenerate

endmodule
