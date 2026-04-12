// SPU-13 Unified Isotropic ALU (v2.11.5)
// Implements ALU_SPEC Sections 1-15: DQFA Core, Balancer, Hysteresis-Zero.

module spu1_alu (
    input  wire         clk,
    input  wire         reset,
    input  wire [831:0] reg_curr,
    input  wire [2:0]   opcode,
    input  wire [1:0]   prime_phase,
    input  wire         sign_flip,
    input  wire         perturb_enable,
    output wire [831:0] reg_next,
    output wire         henosis_stable,
    output wire         fault_detected
);

    // 1. Internal Logic Layers
    wire [831:0] cleaned_reg;
    wire [831:0] permute_out;
    wire [831:0] anneal_out;
    wire [831:0] laminar_out;
    
    // 2. Sovereign Core Components
    spu_core u_core_logic (
        .clk(clk), .reset(reset),
        .reg_curr(reg_curr),
        .neighbors(3072'b0),
        .opcode(opcode),
        .prime_phase(prime_phase),
        .sign_flip(sign_flip),
        .reg_out(permute_out),
        .fault_detected(fault_detected)
    );

    // 3. Isotropic Annealer (Lattice Lock Guard)
    spu_annealer u_annealer (
        .clk(clk), .reset(reset),
        .enable(perturb_enable),
        .reg_in(permute_out),
        .reg_out(anneal_out)
    );

    // 4. Laminar Power Dispatcher (Hysteresis-Zero)
    spu_laminar_power #(.WIDTH(832)) u_laminar (
        .clk(clk), .reset(reset),
        .boot_phase(opcode), // Map opcode to boot-sequence during Phase Alignment
        .reg_in(anneal_out),
        .reg_out(laminar_out),
        .henosis_active(henosis_stable)
    );

    assign reg_next = laminar_out;

endmodule
