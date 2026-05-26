// SPU-13 Sovereign Core (v1.8 - TDM-Optimized)
// Objective: 13-axis Manifold via Fibonacci-Synchronized Pipeline.
// Architecture: TDM Davis Law Gasket + TDM Rotor Vault + Artery Interface.

`include "spu_arch_defines.vh"

module spu13_core #(
    parameter DEVICE = "GW2A",  // "GW1N" | "GW2A" | "GW5A" | "SIM"
    parameter ENABLE_RPLU = 1,
    parameter ENABLE_LATTICE = 1,
    parameter ENABLE_MATH = 1,
    parameter ENABLE_SEQUENCER = 1,
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
    output reg                    artery_wr_en,
    output reg [63:0]             artery_wr_data,

    output wire [3:0]   current_axis_ptr,
    output wire [63:0]  current_axis_data,

    // Instruction input (optional).
    input  wire                    inst_valid,
    input  wire [63:0]             inst_word,
    output wire                    inst_done,

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
    output wire signed [31:0]        audio_q_out
);

    // 1. Manifold State Buffering
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
    wire [831:0] annealed_manifold;
    reg          anneal_enable;
    reg [4:0]    laminar_cycle_count;

    spu_annealer u_annealer (
        .clk(clk), .reset(!rst_n),
        .enable(anneal_enable),
        .reg_in(manifold_reg),
        .reg_out(annealed_manifold)
    );

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
                    anneal_enable <= 1;
                    laminar_cycle_count <= 0;
                end
            end else begin
                laminar_cycle_count <= 0;
            end
        end
    end

    // ── Active Inference (Predictive Coding Filter) ─────────────────
    wire [127:0] inference_posterior;
    wire [127:0] inference_error;
    wire         inference_dissonant;

    spu_active_inference u_inference (
        .clk(clk), .reset(!rst_n),
        .prior_state(manifold_reg[127:0]),
        .prior_precision(adaptive_tau_q[15:0]),
        .sensory_in(manifold_commit_reg[127:0]),
        .sensory_valid(phi_21),
        .posterior_state(inference_posterior),
        .prediction_error(inference_error),
        .is_dissonant(inference_dissonant)
    );

    // ── Soul Metabolism (Adaptive Safety Valve) ─────────────────────
    wire [31:0] adaptive_tau_q;
    wire [31:0] soul_tuck_count, soul_cycle_count;
    wire        soul_flash_we;
    wire [23:0] soul_flash_addr;
    wire [255:0] soul_flash_page;

    // ── Viscosity Monitor ─────────────────────────────────────────
    wire [7:0] laminar_flow_index;
    spu_viscosity_monitor u_viscosity (
        .clk(clk), .reset(!rst_n),
        .abcd_vector(manifold_reg[127:0]),
        .laminar_flow_index(laminar_flow_index)
    );

    // ── Proprioception (Thermal Awareness) ─────────────────────────
    wire [31:0] thermal_pressure;
    wire        damping_active;
    spu_proprioception u_proprio (
        .clk(clk), .reset(!rst_n),
        .manifold_state(manifold_reg),
        .thermal_pressure(thermal_pressure),
        .damping_active(damping_active)
    );

    // ── I2S Audio Output ──────────────────────────────────────────
    spu_i2s_out u_i2s (
        .clk(clk), .rst_n(rst_n),
        .mode(2'b01),
        .lfi(laminar_flow_index),
        .left_data(audio_p[23:0]),
        .right_data(audio_q[23:0]),
        .i2s_bclk(i2s_bclk),
        .i2s_lrclk(i2s_lrclk),
        .i2s_dout(i2s_dout)
    );

    // ── Toroidal Register File (Manifold Frame Buffer) ────────────
    wire [831:0] torus_rd_data;
    reg          torus_wr_en;
    reg  [2:0]   torus_wr_addr;

    toroidal_regfile #(.WIDTH(832), .NUM(8)) u_torus (
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
        .rotate_done()
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            torus_wr_en <= 0;
            torus_wr_addr <= 0;
        end else begin
            torus_wr_en <= 0;
            if (cycle_wrap) begin
                torus_wr_en <= 1;
                torus_wr_addr <= torus_wr_addr + 1;
            end
        end
    end

    wire combined_fault;
    assign combined_fault = rplu_dissoc || damping_active;

    spu_soul_metabolism #(.CLK_HZ(24_000_000)) u_metabolism (
        .clk(clk), .reset(!rst_n),
        .q_state(manifold_reg[127:0]),
        .fault_pulse(combined_fault),
        .is_idle(~|stability_bits),
        .adaptive_tau_q(adaptive_tau_q),
        .tuck_count(soul_tuck_count),
        .cycle_count(soul_cycle_count),
        .flash_we(soul_flash_we),
        .flash_addr(soul_flash_addr),
        .soul_page(soul_flash_page),
        .flash_ready(1'b0)
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

    wire phinary_enable = phinary_cfg[0];
    wire [7:0] phinary_chirality = phinary_cfg[8:1];

    // 3. Stage 1: Rotor & Axis Fetch (Pulse 8)
    wire [31:0] current_rotor;
    wire [7:0]  current_octave;
    wire [2:0]  current_step;
    generate
        if (ENABLE_MATH) begin : gen_rotor_vault
            spu_rotor_vault u_vault (
                .clk(clk), .reset(!rst_n),
                .axis_id(axis_ptr[3:0]),
                .rot_en(phi_8),
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

    wire [31:0] rotor_p_q12 = {16'b0, current_rotor[31:16]} << 12;
    wire [31:0] rotor_q_q12 = {16'b0, current_rotor[15:0]}  << 12;
    wire [63:0] rotor_q12_internal = {rotor_p_q12, rotor_q_q12};
    wire [63:0] rotor_q12 = manual_rotor_en ? manual_rotor_data : rotor_q12_internal;

    wire [63:0] lattice_axis_out;
    wire [3:0]  lattice_axis_shift;
    wire        lattice_axis_overflow;

    generate
        if (ENABLE_LATTICE) begin : gen_lattice
            laminar_node #(.WIDTH(64)) u_lattice_axis (
                .clk(clk), .rst_n(rst_n),
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

    wire [(`MANIFOLD_AXES*4)-1:0] scale_table;
    wire [`MANIFOLD_AXES-1:0]      overflow_table;
    reg scale_write_en;
    reg [3:0] scale_write_shift;
    reg       scale_write_overflow;

    rational_surd5_scale_manager #(.NODES(`MANIFOLD_AXES)) u_scale (
        .clk(clk), .rst_n(rst_n),
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
    wire [63:0] q_prime_ab;
    generate
        if (ENABLE_MATH) begin : gen_cross_rotor
            spu_cross_rotor #(.DEVICE(DEVICE)) u_rotor (
                .clk(clk), .reset(!rst_n),
                .q_axis(current_axis_data),
                .r_rotor(rotor_q12),
                .q_prime(q_prime_ab)
            );
        end else begin : gen_no_cross_rotor
            assign q_prime_ab = current_axis_data;
        end
    endgenerate

    // ── Quadray Register File + ROTC Circulant ─────────────────────────
    wire [63:0] qrf_rd_A, qrf_rd_B, qrf_rd_C, qrf_rd_D;
    wire [63:0] qrf_wr_A, qrf_wr_B, qrf_wr_C, qrf_wr_D;
    reg         qrf_wr_en;
    reg  [3:0]  qrf_wr_lane;
    reg         rote_en;
    reg  [5:0]  rote_angle;
    reg  [1:0]  rote_field;
    reg  [3:0]  rote_src_lane;
    reg [63:0]  instr_wr_A, instr_wr_B, instr_wr_C, instr_wr_D;
    reg         instr_wr_active;

    // ── Decoded Instruction Fields (combinational) ──────────────────────
    wire [7:0] inst_op = eff_inst_word[63:56];
    wire [3:0] inst_lane_dest = eff_inst_word[55:48] % 13;
    wire [3:0] inst_lane_src  = eff_inst_word[47:40] % 13;

    // QLDI Immediate data (sign-extended P components, Q=0)
    wire [63:0] qldi_A = {32'd0, {{24{eff_inst_word[39]}}, eff_inst_word[39:32]}};
    wire [63:0] qldi_B = {32'd0, {{24{eff_inst_word[31]}}, eff_inst_word[31:24]}};
    wire [63:0] qldi_C = {32'd0, {{24{eff_inst_word[23]}}, eff_inst_word[23:16]}};
    wire [63:0] qldi_D = {32'd0, {{24{eff_inst_word[15]}}, eff_inst_word[15:8]}};

    // Effective read lane (combinational mux for same-cycle read)
    wire [3:0] rote_src_lane_eff = (eff_inst_valid && (inst_op == 8'h1C || inst_op == 8'h16))
                                   ? inst_lane_src : rote_src_lane;

    // Write data mux (combinational)
    wire [63:0] regfile_wr_A_mux = (eff_inst_valid && inst_op == 8'h1D) ? qldi_A : (instr_wr_active ? instr_wr_A : qrf_wr_A);
    wire [63:0] regfile_wr_B_mux = (eff_inst_valid && inst_op == 8'h1D) ? qldi_B : (instr_wr_active ? instr_wr_B : qrf_wr_B);
    wire [63:0] regfile_wr_C_mux = (eff_inst_valid && inst_op == 8'h1D) ? qldi_C : (instr_wr_active ? instr_wr_C : qrf_wr_C);
    wire [63:0] regfile_wr_D_mux = (eff_inst_valid && inst_op == 8'h1D) ? qldi_D : (instr_wr_active ? instr_wr_D : qrf_wr_D);

    // ── Instruction Sequencer ──────────────────────────────────────────
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

    wire        eff_inst_valid = ENABLE_SEQUENCER ? seq_inst_valid : inst_valid;
    wire [63:0] eff_inst_word  = ENABLE_SEQUENCER ? seq_inst_word  : inst_word;

    generate
        if (ENABLE_MATH) begin : gen_qrf
            wire ve_qr_init_en;
            wire [3:0] ve_qr_init_lane;
            wire [63:0] ve_qr_init_A, ve_qr_init_B, ve_qr_init_C, ve_qr_init_D;
            wire ve_qr_init_done;

            spu_ve_qr_init u_ve_qr_init (
                .clk(clk), .rst_n(rst_n),
                .boot_done(boot_done),
                .init_en(ve_qr_init_en), .init_lane(ve_qr_init_lane),
                .init_A(ve_qr_init_A), .init_B(ve_qr_init_B),
                .init_C(ve_qr_init_C), .init_D(ve_qr_init_D),
                .init_done(ve_qr_init_done)
            );

            spu_quadray_regfile u_qrf (
                .clk(clk), .rst_n(rst_n),
                .rd_lane(rote_src_lane_eff),
                .rd_A(qrf_rd_A), .rd_B(qrf_rd_B), .rd_C(qrf_rd_C), .rd_D(qrf_rd_D),
                .wr_en(qrf_wr_en), .wr_lane(qrf_wr_lane),
                .wr_A(regfile_wr_A_mux), .wr_B(regfile_wr_B_mux),
                .wr_C(regfile_wr_C_mux), .wr_D(regfile_wr_D_mux),
                .init_en(ve_qr_init_en), .init_lane(ve_qr_init_lane),
                .init_A(ve_qr_init_A), .init_B(ve_qr_init_B),
                .init_C(ve_qr_init_C), .init_D(ve_qr_init_D),
                .dbg_A(), .dbg_B(), .dbg_C(), .dbg_D()
            );

            wire [1:0] rote_perm_sel = (rote_angle < 6) ? 2'b00 :
                                       (rote_angle < 8) ? 2'b01 :
                                       (rote_angle < 10) ? 2'b10 : 2'b11;

            wire [63:0] rotor_A_in, rotor_B_in, rotor_C_in, rotor_D_in;
            spu_quadray_permute u_perm_fwd (
                .perm_sel(rote_perm_sel),
                .A_in(qrf_rd_A), .B_in(qrf_rd_B), .C_in(qrf_rd_C), .D_in(qrf_rd_D),
                .A_out(rotor_A_in), .B_out(rotor_B_in), .C_out(rotor_C_in), .D_out(rotor_D_in)
            );

            wire rote_done;
            wire [63:0] rote_A_out_raw, rote_B_out_raw, rote_C_out_raw, rote_D_out_raw;
            spu13_rotor_core_tdm u_rotc (
                .clk(clk), .rst_n(rst_n),
                .start(rote_en), .done(rote_done),
                .A_in(rotor_A_in), .B_in(rotor_B_in), .C_in(rotor_C_in), .D_in(rotor_D_in),
                .F(rote_F), .G(rote_G), .H(rote_H),
                .field_sel(rote_field),
                .bypass_p5(rote_angle == 6'd2),
                .A_out(rote_A_out_raw), .B_out(rote_B_out_raw),
                .C_out(rote_C_out_raw), .D_out(rote_D_out_raw)
            );

            wire [1:0] rote_inv_sel = (rote_perm_sel == 2'b01) ? 2'b11 :
                                      (rote_perm_sel == 2'b11) ? 2'b01 : rote_perm_sel;
            spu_quadray_permute u_perm_inv (
                .perm_sel(rote_inv_sel),
                .A_in(rote_A_out_raw), .B_in(rote_B_out_raw), .C_in(rote_C_out_raw), .D_in(rote_D_out_raw),
                .A_out(qrf_wr_A), .B_out(qrf_wr_B), .C_out(qrf_wr_C), .D_out(qrf_wr_D)
            );

            wire [63:0] rote_B_out = qrf_wr_B;
            wire [63:0] rote_C_out = qrf_wr_C;
            wire [63:0] rote_D_out = qrf_wr_D;
        end else begin : gen_no_qrf
            assign qrf_rd_A = 0; assign qrf_rd_B = 0; assign qrf_rd_C = 0; assign qrf_rd_D = 0;
            assign qrf_wr_A = 0; assign qrf_wr_B = 0; assign qrf_wr_C = 0; assign qrf_wr_D = 0;
            assign rote_done = 1;
        end
    endgenerate

    wire signed [63:0] rote_F, rote_G, rote_H;
    assign rote_F = (rote_angle == 6'd0)  ? 64'sd1  :
                    (rote_angle == 6'd1)  ? 64'sd2  :
                    (rote_angle == 6'd2)  ? -64'sd1 :
                    (rote_angle == 6'd3)  ? -64'sd1 :
                    (rote_angle == 6'd4)  ? 64'sd2  :
                    (rote_angle == 6'd5)  ? 64'sd2  :
                    (rote_angle < 6'd12)  ? 64'sd2  : 64'sd1;

    assign rote_G = (rote_angle == 6'd0)  ? 64'sd0  :
                    (rote_angle == 6'd1)  ? 64'sd2  :
                    (rote_angle == 6'd2)  ? 64'sd2  :
                    (rote_angle == 6'd3)  ? -64'sd1 :
                    (rote_angle == 6'd4)  ? -64'sd1 :
                    (rote_angle == 6'd5)  ? 64'sd2  :
                    (rote_angle < 6'd12)  ? 64'sd2  : 64'sd0;

    assign rote_H = (rote_angle == 6'd0)  ? 64'sd0  :
                    (rote_angle == 6'd1)  ? -64'sd1 :
                    (rote_angle == 6'd2)  ? 64'sd2  :
                    (rote_angle == 6'd3)  ? -64'sd1 :
                    (rote_angle == 6'd4)  ? 64'sd2  :
                    (rote_angle == 6'd5)  ? -64'sd1 :
                    (rote_angle < 6'd12)  ? 64'sd2  : 64'sd0;

    reg rote_active;
    reg [3:0] rote_dest_lane;
    reg       inst_done_r;
    assign inst_done = inst_done_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rote_en <= 0; rote_active <= 0;
            hex_valid <= 0; hex_q <= 0; hex_r <= 0;
            rote_src_lane <= 0; rote_dest_lane <= 0;
            rote_angle <= 0; rote_field <= 0;
            qrf_wr_en <= 0; qrf_wr_lane <= 0;
            inst_done_r <= 0; instr_wr_active <= 0;
        end else begin
            qrf_wr_en <= 0; inst_done_r <= 0;
            rote_en <= 0; hex_valid <= 0;
            instr_wr_active <= 0;

            if (eff_inst_valid) begin
                case (inst_op)
                    8'h1D: begin // QLDI
                        qrf_wr_en   <= 1;
                        qrf_wr_lane <= inst_lane_dest;
                        instr_wr_A  <= qldi_A;
                        instr_wr_B  <= qldi_B;
                        instr_wr_C  <= qldi_C;
                        instr_wr_D  <= qldi_D;
                        instr_wr_active <= 1;
                        inst_done_r <= 1;
                    end
                    8'h1C: begin // ROTC
                        rote_src_lane  <= inst_lane_src;
                        rote_dest_lane <= inst_lane_dest;
                        rote_angle     <= eff_inst_word[29:24];
                        rote_field     <= eff_inst_word[31:30];
                        rote_active    <= 1;
                        rote_en        <= 1;
                    end
                    8'h16: begin // HEX
                        rote_src_lane <= inst_lane_src;
                        hex_q   <= qrf_rd_A[15:0] - qrf_rd_D[15:0];
                        hex_r   <= qrf_rd_B[15:0] - qrf_rd_D[15:0];
                        hex_valid <= 1;
                        inst_done_r <= 1;
                    end
                    default: inst_done_r <= 1;
                endcase
            end else if (rote_active) begin
                if (rote_done) begin
                    qrf_wr_en   <= 1;
                    qrf_wr_lane <= rote_dest_lane;
                    rote_active <= 0;
                    inst_done_r <= 1;
                end
            end
        end
    end

    // Stage 3: Stability Check & Commit
    wire [63:0] rotated_axis = q_prime_ab;
    wire [`MANIFOLD_WIDTH-1:0] manifold_commit_reg = manifold_with_axis(manifold_reg, axis_ptr, rotated_axis);
    wire [31:0] quadrance, ivm_quadrance;
    wire [15:0] gasket_sum;
    wire signed [31:0] audio_p, audio_q;

    generate
        if (ENABLE_MATH) begin : gen_davis_gate
            davis_gate_dsp #(.DEVICE(DEVICE)) u_gate (
                .clk(clk), .rst_n(rst_n), .q_vector(rotated_axis),
                .quadrance(quadrance), .ivm_quadrance(ivm_quadrance),
                .gasket_sum(gasket_sum), .audio_p(audio_p), .audio_q(audio_q)
            );
        end else begin : gen_no_davis_gate
            assign quadrance = current_axis_data[63:32] >> 12;
            assign gasket_sum = current_axis_data[63:48] + current_axis_data[47:32];
        end
    endgenerate

    wire rplu_dissoc, rplu_done;
    wire [9:0] rplu_addr_dbg;
    generate
        if (ENABLE_RPLU) begin : gen_rplu
            davis_to_rplu u_davis_rplu (
                .clk(clk), .rst_n(rst_n), .start(phi_21), .q_vector(rotated_axis), .material_id(phinary_chirality),
                .cfg_wr_en(dec_fast_cfg_wr_en), .cfg_wr_sel(dec_fast_cfg_sel), .cfg_wr_material(dec_fast_cfg_material), .cfg_wr_addr(dec_fast_cfg_addr), .cfg_wr_data(dec_fast_cfg_data),
                .dissoc(rplu_dissoc), .done(rplu_done),
                .ratio_cmp_res(ratio_cmp_res), .ratio_cmp_valid(ratio_cmp_valid), .r_addr_dbg(rplu_addr_dbg)
            );
        end else begin : gen_no_rplu
            assign rplu_dissoc = 0; assign rplu_done = phi_21;
        end
    endgenerate

    reg [12:0] rplu_dissoc_bits;
    reg [3:0]  rplu_axis_pending;

    assign gasket_sum_out = gasket_sum;
    assign quadrance_out  = quadrance;
    assign cycle_wrap     = (axis_ptr == 4'd12);
    assign rplu_dissoc_out = rplu_dissoc;
    assign rplu_dissoc_mask_out = rplu_dissoc_bits;
    assign rplu_addr_out = rplu_addr_dbg;
    assign audio_p_out = audio_p; assign audio_q_out = audio_q;
    assign laminar_flow_index_out = laminar_flow_index;
    assign thermal_pressure_out = thermal_pressure;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rplu_dissoc_bits <= 0; rplu_axis_pending <= 0;
        end else begin
            if (phi_21) rplu_axis_pending <= axis_ptr;
            if (rplu_done && rplu_axis_pending <= 12) rplu_dissoc_bits[rplu_axis_pending] <= rplu_dissoc;
        end
    end

    wire axis_stable = (quadrance > 0) && !rplu_dissoc;
    reg [12:0] stability_bits;
    reg [9:0] torus_idx;
    reg        torus_emit_enable;

    reg [2:0] hydration_state;
    localparam H_IDLE = 0, H_INHALE = 1, H_BLOOM = 2, H_EXHALE = 3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hydration_state <= H_IDLE;
            mem_burst_rd <= 0; mem_burst_wr <= 0; mem_addr <= 0;
            stability_bits <= 13'h1FFF; is_janus_point <= 1;
            scale_write_en <= 0; artery_wr_en <= 0; artery_wr_data <= 0;
            audio_mode <= 0; torus_idx <= 0; torus_emit_enable <= 0;
            // Seed the 13-axis manifold with Quadray Identities (A=2.0 in Q12)
            // This ensures Davis Gate sees Quadrance > 0 immediately.
            manifold_lane[0]  <= 64'h0000_0000_2000_0000;
            manifold_lane[1]  <= 64'h0000_0000_2000_0000;
            manifold_lane[2]  <= 64'h0000_0000_2000_0000;
            manifold_lane[3]  <= 64'h0000_0000_2000_0000;
            manifold_lane[4]  <= 64'h0000_0000_2000_0000;
            manifold_lane[5]  <= 64'h0000_0000_2000_0000;
            manifold_lane[6]  <= 64'h0000_0000_2000_0000;
            manifold_lane[7]  <= 64'h0000_0000_2000_0000;
            manifold_lane[8]  <= 64'h0000_0000_2000_0000;
            manifold_lane[9]  <= 64'h0000_0000_2000_0000;
            manifold_lane[10] <= 64'h0000_0000_2000_0000;
            manifold_lane[11] <= 64'h0000_0000_2000_0000;
            manifold_lane[12] <= 64'h0000_0000_2000_0000;
        end else if (prime_we && !boot_done) begin
            case (prime_addr)
                4'd0,4'd1,4'd2,4'd3,4'd4,4'd5,4'd6,4'd7,4'd8,4'd9,4'd10,4'd11,4'd12:
                    manifold_lane[prime_addr] <= {32'd0, ({8'd0, prime_data} << 12)};
            endcase
        end else begin
            artery_wr_en <= 0; scale_write_en <= 0;
            if (dec_fast_cfg_wr_en && dec_fast_cfg_sel == 7) begin
                torus_idx <= dec_fast_cfg_data[9:0]; torus_emit_enable <= dec_fast_cfg_data[10];
            end
            case (hydration_state)
                H_IDLE: if (phi_8) hydration_state <= H_BLOOM;
                H_INHALE: begin
                    if (mem_burst_done || !ENABLE_MATH) begin // Bypass if no memory
                        mem_burst_rd <= 0;
                        if (ENABLE_MATH) begin
                            manifold_lane[0] <= mem_rd_manifold[63:0];   manifold_lane[1] <= mem_rd_manifold[127:64];
                            manifold_lane[2] <= mem_rd_manifold[191:128]; manifold_lane[3] <= mem_rd_manifold[255:192];
                            manifold_lane[4] <= mem_rd_manifold[319:256]; manifold_lane[5] <= mem_rd_manifold[383:320];
                            manifold_lane[6] <= mem_rd_manifold[447:384]; manifold_lane[7] <= mem_rd_manifold[511:448];
                            manifold_lane[8] <= mem_rd_manifold[575:512]; manifold_lane[9] <= mem_rd_manifold[639:576];
                            manifold_lane[10]<= mem_rd_manifold[703:640]; manifold_lane[11]<= mem_rd_manifold[767:704];
                            manifold_lane[12]<= mem_rd_manifold[831:768];
                        end
                        hydration_state <= H_BLOOM;
                    end
                end
                H_BLOOM: if (phi_21) begin
                    manifold_lane[axis_ptr] <= rotated_axis;
                    stability_bits[axis_ptr] <= axis_stable && !rplu_dissoc_bits[axis_ptr];
                    scale_write_en <= 1; scale_write_shift <= lattice_axis_shift; scale_write_overflow <= lattice_axis_overflow;
                    if (axis_ptr == 12) begin
                        is_janus_point <= &stability_bits;
                        if (ENABLE_MATH && boot_done) begin // Only exhale if SDRAM might exist
                             mem_burst_wr <= 1; mem_wr_manifold <= manifold_commit_reg;
                             hydration_state <= H_EXHALE;
                        end else begin
                             hydration_state <= H_BLOOM; // Stay in bloom
                        end
                    end
                end
                H_EXHALE: if (mem_burst_done) begin
                    mem_burst_wr <= 0; mem_burst_rd <= 1;
                    hydration_state <= H_INHALE;
                end
            endcase
        end
    end
    assign bloom_complete = (hydration_state == H_IDLE);
endmodule
