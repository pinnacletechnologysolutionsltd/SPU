// SPU-13 Light Core (v1.0)
// Target: iCE40UP5K / Unified Fleet
// Objective: A programmable, low-gate-count SPU implementation.
// Logic: Supports SAS opcodes using simplified modules.

module spu_light_core (
    input  wire         clk,
    input  wire         reset,
    input  wire [255:0] reg_curr,   // 4x64-bit Quadray Vectors (A,B,C,D)
    input  wire [2:0]   opcode,     
    input  wire [1:0]   prime_phase,
    input  wire         sign_flip,  
    output reg  [255:0] reg_out,    
    output wire         fault_detected
);

    // --- 1. Internal Units ---
    wire [63:0] A_in = reg_curr[63:0];
    wire [63:0] B_in = reg_curr[127:64];
    wire [63:0] C_in = reg_curr[191:128];
    wire [63:0] D_in = reg_curr[255:192];

    // Unit A: Thomson Rotor (RROT)
    wire [63:0] rotor_A, rotor_B, rotor_C, rotor_D;
    spu13_rotor_core u_rotor (
        .clk(clk), .rst_n(!reset),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F(64'h00000000_00010000), // Identity by default, could be parameterized
        .G(64'h0), .H(64'h0),
        .bypass_p5(1'b0),
        .A_out(rotor_A), .B_out(rotor_B), .C_out(rotor_C), .D_out(rotor_D)
    );

    // Unit B: Quad Adder (VADD)
    // Simplified to 32-bit integer parts for the light core
    wire [31:0] add_A, add_B, add_C, add_D;
    assign add_A = A_in[31:0] + A_in[31:0]; // Recursive Self-Addition
    assign add_B = B_in[31:0] + B_in[31:0];
    assign add_C = C_in[31:0] + C_in[31:0];
    assign add_D = D_in[31:0] + D_in[31:0];

    // Unit C: Quadrance Calc (FQUD)
    wire [63:0] q_val;
    quadrance_calc u_qcalc (
        .a(A_in[23:0]), .b(B_in[23:0]), .c(C_in[23:0]), .d(D_in[23:0]),
        .q_out(q_val[47:0])
    );
    assign q_val[63:48] = 16'b0;

    // --- 2. Dispatch Mux ---
    always @(*) begin
        case (opcode)
            3'b000: reg_out = {D_in[63:32], add_D, C_in[63:32], add_C, B_in[63:32], add_B, A_in[63:32], add_A};
            3'b001: reg_out = {rotor_D, rotor_C, rotor_B, rotor_A};
            3'b011: reg_out = {192'b0, q_val};
            default: reg_out = reg_curr;
        endcase
    end

    assign fault_detected = 1'b0;

endmodule
