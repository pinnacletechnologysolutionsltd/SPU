// SPU-13 NANO CORE (v1.7 Stress-Ready)
// Target: iCE40UP5K (iCeSugar Nano)
// Objective: Support axis-specific stress injection for certification.
// Discovery: Bee Davis, "The Geometry of Sameness"

module spu_nano_core #(
    parameter [63:0] DEFAULT_TAU_Q = 64'h00000000_00040000 
)(
    input  wire         clk,
    input  wire         reset,
    input  wire [127:0] reg_curr,   
    input  wire [2:0]   opcode,     
    input  wire [1:0]   prime_phase, // Now used as Axis Selector (00=A, 01=B, 10=C, 11=D)
    input  wire         sign_flip,
    input  wire [63:0]  dynamic_tau_q, 
    output reg  [127:0] reg_out,    
    output reg          fault_detected
);

    // --- 1. Internal Units ---
    wire signed [31:0] A_in = reg_curr[31:0];
    wire signed [31:0] B_in = reg_curr[63:32];
    wire signed [31:0] C_in = reg_curr[95:64];
    wire signed [31:0] D_in = reg_curr[127:96];

    // Axis-Specific Displacement (The Stress Injector)
    // We add a fixed "Laminar Sip" (0x0100) to the targeted axis.
    wire [31:0] inc_val = 32'h00000100;
    wire [31:0] v_inc_A = A_in + inc_val;
    wire [31:0] v_inc_B = B_in + inc_val;
    wire [31:0] v_inc_C = C_in + inc_val;
    wire [31:0] v_inc_D = D_in + inc_val;

    // Unit A: Nano-Rotor
    wire signed [31:0] rot_A = B_in;
    wire signed [31:0] rot_B = C_in;
    wire signed [31:0] rot_C = D_in;
    wire signed [31:0] rot_D = A_in;

    // Unit C: Active Annealer (ANNE)
    wire signed [31:0] anne_A = A_in - (A_in >>> 4);
    wire signed [31:0] anne_B = B_in - (B_in >>> 4);
    wire signed [31:0] anne_C = C_in - (C_in >>> 4);
    wire signed [31:0] anne_D = D_in - (D_in >>> 4);

    // --- 2. Proposed State Selection ---
    reg signed [31:0] p_A, p_B, p_C, p_D;
    always @(*) begin
        case (opcode)
            3'b000: begin // VADD - Axis Specific Displacement
                p_A = (prime_phase == 2'b00) ? v_inc_A : A_in;
                p_B = (prime_phase == 2'b01) ? v_inc_B : B_in;
                p_C = (prime_phase == 2'b10) ? v_inc_C : C_in;
                p_D = (prime_phase == 2'b11) ? v_inc_D : D_in;
            end
            3'b001: begin p_A = rot_A; p_B = rot_B; p_C = rot_C; p_D = rot_D; end
            3'b111: begin p_A = anne_A; p_B = anne_B; p_C = anne_C; p_D = anne_D; end
            default: begin p_A = A_in; p_B = B_in; p_C = C_in; p_D = D_in; end
        endcase
    end

    // --- 3. The Pipelined Gasket ---
    wire over_curvature;
    spu_davis_gate #(
        .TAU_Q(DEFAULT_TAU_Q)
    ) u_gate (
        .a(p_A[31:16]), .b(p_B[31:16]), .c(p_C[31:16]), .d(p_D[31:16]),
        .over_curvature(over_curvature)
    );

    wire signed [31:0] residual = p_A + p_B + p_C + p_D;
    wire is_leaking = (residual != 32'd0);
    wire signed [31:0] correction = residual >>> 2;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            reg_out <= 128'b0;
            fault_detected <= 1'b0;
        end else begin
            fault_detected <= is_leaking | over_curvature;
            reg_out <= {p_D - correction, p_C - correction, p_B - correction, p_A - correction};
        end
    end

endmodule
