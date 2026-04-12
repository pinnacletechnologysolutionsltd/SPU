// SPU-13 Integrated Core (v3.3.89 Phyllotaxis)
// Implements Fibonacci-Spiral Interconnects for Organic Data-Flow.
// Guard: Geometry Fluidizer integrated to purge Cubic Jitter.
// Bridge: Rational Trigonometry integrated for bit-exact Quadrance Audits.
// Flow: Fluid Solver and Isotropic Annealer integrated into the Dispatch.
// Proprioception: Thermal Feedback for Self-Regulated Homeostasis.
// Integrity: Laminar Gate dispatch for Null Hysteresis power signature.
// Interaction: strike_in port for topological pressure injection.

module spu_core (
    input  wire         clk,
    input  wire         reset,
    input  wire [831:0] reg_curr,
    input  wire [3071:0] neighbors,
    input  wire [127:0] strike_in,
    input  wire [2:0]   opcode,
    input  wire [1:0]   prime_phase,
    input  wire         sign_flip,
    // runtime cfg inputs (dec_fast from spu_system)
    input  wire         dec_fast_cfg_wr_en,
    input  wire [2:0]   dec_fast_cfg_sel,
    input  wire         dec_fast_cfg_material,
    input  wire [9:0]   dec_fast_cfg_addr,
    input  wire [63:0]  dec_fast_cfg_data,
    output wire [831:0] reg_out,
    output wire         fault_detected
);
    // Algebraic Interpretation: 26 registers of {a, b} (RationalSurd)
    // reg_curr[i*32 + 15:0]  -> a (Rational part)
    // reg_curr[i*32 + 31:16] -> b (Surd part)
    
    // Wire definitions for RationalSurd arithmetic
    wire [15:0] a_in [0:25];
    wire [15:0] b_in [0:25];
    
    genvar i;
    generate
        for (i = 0; i < 26; i = i + 1) begin : unfold_registers
            assign a_in[i] = reg_curr[i*32 +: 16];
            assign b_in[i] = reg_curr[i*32 + 16 +: 16];
        end
    endgenerate

    // cleaned_reg: pass-through alias of reg_curr (fluidizer stage).
    // damping_active: static off (future: dynamic damping control).
    wire [831:0] cleaned_reg;
    assign cleaned_reg = reg_curr;
    wire         damping_active;
    assign damping_active = 1'b0;

    // 3. Geometry Fluidization (Dynamic Damping)
    wire [831:0] fluid_reg;
    generate
        for (i = 0; i < 26; i = i + 1) begin : fluidizer_lanes
            spu_geometry_fluidizer fluidizer (
                .brick_coord_in(cleaned_reg[i*32 +: 12]), 
                .dampen(damping_active),
                .laminar_coord_out(fluid_reg[i*32 +: 12])
            );
            assign fluid_reg[i*32+12 +: 20] = cleaned_reg[i*32+12 +: 20];
        end
    endgenerate

    // 4. High-Dimensional Logic Units
    wire [255:0] sperm_x4_out;
    wire [831:0] sperm_13_out;
    wire [127:0] smul_13_out;
    wire [63:0]  quadrance_out;
    wire [831:0] fluid_out;
    wire [831:0] annealed_out;
    wire [255:0] bypass_out;
    wire [127:0] snap_q_out;

    spu_fractal_bypass u_bypass (
        .q_in(fluid_reg[255:0]), .phase(prime_phase), .q_out(bypass_out)
    );

    spu_rational_snap u_snap (
        .x(fluid_reg[31:0]), .y(fluid_reg[63:32]), .z(fluid_reg[95:64]),
        .a(snap_q_out[31:0]), .b(snap_q_out[63:32]), .c(snap_q_out[95:64]), .d(snap_q_out[127:96])
    );

    spu_permute x4_unit (
        .clk(clk), .reset(reset), 
        .q_in(bypass_out), .prime_phase(prime_phase), 
        .sign_flip(sign_flip), .q_out(sperm_x4_out)
    );

    spu_permute_13 x13_unit (.q_in(fluid_reg), .q_out(sperm_13_out));

    spu_smul_13 phi_multiplier (
        .clk(clk), .reset(reset),
        .a1(fluid_reg[15:0]),  .b1(fluid_reg[31:16]),
        .a2(fluid_reg[47:32]), .b2(fluid_reg[63:48]),
        .res_a(smul_13_out[15:0]), .res_b(smul_13_out[31:16]),
        .ready()
    );

    spu_rational_trig trig_unit (
        .a(fluid_reg[31:0]), .b(fluid_reg[63:32]), .c(fluid_reg[95:64]), .d(fluid_reg[127:96]),
        .quadrance(quadrance_out), .spread_60_fixed(),
        .a_cubic_laminar(), .b_cubic_laminar(), .c_cubic_laminar(), .d_cubic_laminar()
    );

    wire [831:0] gram_data_out = 832'b0; // gram_controller stub

    spu_fluid_solver u_solver (
        .clk(clk), .reset(reset), .velocity_in(fluid_reg), .neighbors(neighbors),
        .velocity_out(fluid_out), .laminar_lock(),
        .cfg_wr_en(dec_fast_cfg_wr_en), .cfg_wr_sel(dec_fast_cfg_sel),
        .cfg_wr_material(dec_fast_cfg_material), .cfg_wr_addr(dec_fast_cfg_addr),
        .cfg_wr_data(dec_fast_cfg_data)
    );

    spu_annealer u_annealer (
        .clk(clk), .reset(reset), .enable(opcode == 3'b111), .reg_in(fluid_reg), .reg_out(annealed_out)
    );

    // 5. Hardware Validator: Forensic Identity Audit
    wire forensic_fault;
    spu_validator u_validator (
        .clk(clk), .reset(reset),
        .manifold_state(fluid_reg),
        .current_quadrance(quadrance_out),
        .fault_detected(forensic_fault)
    );

    // 6. Algebraic Polynomial Selector (Dispatch)
    // Replaces case(opcode) with parallel polynomial selection.
    // Each op_decoded[i] is a 1-hot signal from an opcode decoder.
    wire [7:0] op_decoded;
    assign op_decoded = 8'b1 << opcode;

    // Polynomial Dispatcher: out = Sum(Op_i * Result_i) over field
    reg [831:0] next_state;
    always @(*) begin
        next_state = (op_decoded[0] ? {fluid_reg[831:128], snap_q_out} : 832'b0) |
                     (op_decoded[1] ? {fluid_reg[831:256], sperm_x4_out} : 832'b0) |
                     (op_decoded[2] ? {fluid_reg[831:128], smul_13_out} : 832'b0) |
                     (op_decoded[3] ? {fluid_reg[831:64],  quadrance_out} : 832'b0) |
                     (op_decoded[4] ? gram_data_out : 832'b0) |
                     (op_decoded[5] ? fluid_out : 832'b0) |
                     (op_decoded[6] ? sperm_13_out : 832'b0) |
                     (op_decoded[7] ? annealed_out : 832'b0);
        
        // Default state if no opcode is active
        if (opcode > 3'b111) next_state = fluid_reg;
    end

    // 7. Laminar Dispatch (Null Hysteresis Switch)
    wire [12:0] gate_valid;
    wire [12:0] lane_faults = 13'b0; // stub: no per-lane fault reporting yet
    generate
        for (i = 0; i < 13; i = i + 1) begin : dispatch_lanes
            spu_laminar_gate u_gate (
                .clk(clk), .reset(reset),
                .data_in(next_state[i*64 +: 64]),
                .janus_flip(sign_flip),
                .data_out(reg_out[i*64 +: 64]),
                .laminar_valid(gate_valid[i])
            );
        end
    endgenerate

    assign fault_detected = (|lane_faults) | forensic_fault | (!(&gate_valid));

endmodule
