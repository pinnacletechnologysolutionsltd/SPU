// SPU-13 Sovereign Core (v1.7 - Strictly Phi-Gated TDM)
// Objective: 13-axis Manifold via Fibonacci-Synchronized Pipeline.
// Architecture: TDM Davis Law Gasket + SQR Rotor Vault + Artery Interface.

`include "spu_arch_defines.vh"

module spu13_core #(
    parameter DEVICE = "GW2A"  // "GW1N" | "GW2A" | "GW5A" | "SIM"
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
    input  wire         dec_fast_cfg_material,
    input  wire [9:0]   dec_fast_cfg_addr,
    input  wire [63:0]  dec_fast_cfg_data,
    // Phinary config (bits: [0]=enable, [1]=chirality)
    input  wire [15:0]  phinary_cfg,

    // Sovereign Memory Interface
    `MANIFOLD_SIGS,

    // 13-Axis Manifold Snapshot (for Artery TX)
    output wire [3:0]   current_axis_ptr,
    output wire [63:0]  current_axis_data,
    output reg [`MANIFOLD_WIDTH-1:0] manifold_out,
    output wire                      bloom_complete,
    output wire [(`MANIFOLD_AXES*4)-1:0] scale_table_out,
    output wire [`MANIFOLD_AXES-1:0]      scale_overflow_out,
    output reg                       is_janus_point
);

    // 1. Manifold State Buffering
    reg [`MANIFOLD_WIDTH-1:0] manifold_reg;
    initial manifold_reg = 0;

    // 2. TDM Axis Pointer
    reg [3:0] axis_ptr;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) axis_ptr <= 0;
        else if (phi_21) begin
            axis_ptr <= (axis_ptr == 4'd12) ? 4'd0 : axis_ptr + 4'd1;
        end
    end

    assign current_axis_ptr = axis_ptr;
    assign current_axis_data = manifold_reg[axis_ptr*64 +: 64];

    // Phinary control exported from top-level config
    wire phinary_enable;
    assign phinary_enable = phinary_cfg[0];
    wire phinary_chirality;
    assign phinary_chirality = phinary_cfg[1];

    // 3. Stage 1: Rotor & Axis Fetch (Pulse 8)
    // Vault v2.0: Pell Octave tracking — rot_en driven by sequencer pulse.
    // In SPU-13 context, ROT fires once per axis per sovereign cycle.
    wire [31:0] current_rotor;
    wire [7:0]  current_octave;
    wire [2:0]  current_step;
    spu_rotor_vault u_vault (
        .clk(clk),
        .reset(!rst_n),
        .axis_id(axis_ptr[3:0]),
        .rot_en(1'b0),          // sequencer drives rot_en; stub=0 for read-only
        .rotor_out(current_rotor),
        .octave_out(current_octave),
        .step_out(current_step)
    );

    // Scale raw Pell integers (from vault) to Q12 for the cross-rotor.
    // Steps 0-7: P in {1,2,7,26,97,362,1351,5042} — all fit in 32-bit Q12
    //            (max P*4096 = 5042*4096 = 20,652,032 < 2^25, safe in int32).
    wire [31:0] rotor_p_q12;
    assign rotor_p_q12 = {16'b0, current_rotor[31:16]} << 12;
    wire [31:0] rotor_q_q12;
    assign rotor_q_q12 = {16'b0, current_rotor[15:0]}  << 12;
    wire [63:0] rotor_q12;
    assign rotor_q12 = {rotor_p_q12, rotor_q_q12};

    // SPU-13 laminar lattice instantiation (13 laminar_node primitives)
    wire [`MANIFOLD_WIDTH-1:0] lattice_manifold;
    wire [(`MANIFOLD_AXES*4)-1:0] lattice_shifts;
    wire [`MANIFOLD_AXES-1:0]      lattice_overflows;

    spu13_lattice #(.WIDTH(64), .NODES(13)) u_spu13 (
        .clk(clk),
        .rst_n(rst_n),
        .enable(phinary_enable),
        .manifold_in(manifold_reg),
        .manifold_out(lattice_manifold),
        .scale_shifts(lattice_shifts),
        .scale_overflows(lattice_overflows)
    );

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

    // Stage 2: The SQR Cross-Product (Pulse 13)
    // Manifold axis format: {A[31:0], B[31:0]} — full 64-bit axis is the surd.
    wire [63:0] q_prime_ab;
    spu_cross_rotor u_rotor (
        .clk(clk),
        .reset(!rst_n),
        .q_axis(current_axis_data),  // {A[31:0], B[31:0]} full axis
        .r_rotor(rotor_q12),         // Q12-scaled Pell rotor
        .q_prime(q_prime_ab)
    );

    // Stage 3: Stability Check & Commit (Pulse 21)
    wire [63:0] rotated_axis;
    assign rotated_axis = q_prime_ab;
    wire [31:0] quadrance;
    wire [31:0] ivm_quadrance;
    wire [15:0] gasket_sum;
    wire signed [31:0] audio_p;
    wire signed [31:0] audio_q;
    
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

    wire [31:0] quadrance_err;
    assign quadrance_err = (quadrance > 32'h0100_0000) ? (quadrance - 32'h0100_0000) : (32'h0100_0000 - quadrance);
    wire axis_stable;
    assign axis_stable = (quadrance_err <= 32'h0000_1000);


    reg [12:0] stability_bits;

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
            manifold_out <= 0;
            stability_bits <= 13'h1FFF;
            is_janus_point <= 1'b1;
            scale_write_en <= 1'b0;
            scale_write_shift <= 4'd0;
            scale_write_overflow <= 1'b0;
        end else begin
            case (hydration_state)
                H_IDLE: begin
                    if (phi_8 && mem_ready) begin
                        mem_burst_rd <= 1; mem_addr <= 24'h0;
                        hydration_state <= H_INHALE;
                    end
                end
                H_INHALE: begin
                    if (mem_burst_done) begin
                        mem_burst_rd <= 0;
                        manifold_reg <= mem_rd_manifold;
                        hydration_state <= H_BLOOM;
                    end
                end
                H_BLOOM: begin
                    // Commit current axis on Pulse 21
                    if (phi_21) begin
                        manifold_reg[axis_ptr*64 +: 64] <= rotated_axis;
                        stability_bits[axis_ptr] <= axis_stable;

                        // Capture scale shift for this axis into global scale manager
                        scale_write_en <= 1'b1;
                        scale_write_shift <= lattice_shifts[axis_ptr*4 +: 4];
                        scale_write_overflow <= lattice_overflows[axis_ptr];
                        
                        // If we just finished axis 12, move to Exhale
                        if (axis_ptr == 4'd12) begin
                            manifold_out <= manifold_reg;
                            is_janus_point <= &stability_bits;
                            mem_burst_wr <= 1;
                            mem_wr_manifold <= manifold_reg;
                            hydration_state <= H_EXHALE;
                        end
                    end else begin
                        scale_write_en <= 1'b0;
                    end
                end
                H_EXHALE: begin
                    if (mem_burst_done) begin
                        mem_burst_wr <= 0;
                        hydration_state <= H_IDLE;
                    end
                end
            endcase
        end
    end

    assign bloom_complete = (hydration_state == H_IDLE);

endmodule
