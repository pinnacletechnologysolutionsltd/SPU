// spu_cross_rotor.v (v1.1 - Cross-Quaternary SQR Refraction)
// Objective: Perform Q(sqrt3) multiplication: (A + B*sqrt3) * (Ra + Rb*sqrt3)
// Field: Rational Field Q(sqrt3).
// Optimization: Uses parallel multipliers for low-latency Laminar execution.
// Scaling: Q12 (1.0 = 16'h1000).

module spu_cross_rotor (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] q_axis,   // {A[15:0], B[15:0]} - RationalSurd
    input  wire [31:0] r_rotor,  // {Ra[15:0], Rb[15:0]} - SQR Rotor
    output wire [31:0] q_prime  // {A_new[15:0], B_new[15:0]}
);

    wire signed [15:0] A  = $signed(q_axis[31:16]);
    wire signed [15:0] B  = $signed(q_axis[15:0]);
    wire signed [15:0] Ra = $signed(r_rotor[31:16]);
    wire signed [15:0] Rb = $signed(r_rotor[15:0]);

    // Intermediate Products (The "Laminar" Refraction)
    reg signed [31:0] prod_aa, prod_bb, prod_ab, prod_ba;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            prod_aa <= 32'h0;
            prod_bb <= 32'h0;
            prod_ab <= 32'h0;
            prod_ba <= 32'h0;
        end else begin
            // Stage 1: DSP Multiplication
            prod_aa <= A * Ra;
            prod_bb <= B * Rb;
            prod_ab <= A * Rb;
            prod_ba <= B * Ra;
        end
    end

    // Final Cross-Product Assembly (Combinatorial Stage 2)
    // A_prime = (A*Ra) - (3*B*Rb)
    // B_prime = (A*Rb) + (B*Ra)
    
    // Scale back from Q12*Q12 = Q24 to Q12
    // 3*B*Rb = (B*Rb << 1) + (B*Rb)
    wire signed [31:0] nA_full = prod_aa - ((prod_bb << 1) + prod_bb);
    wire signed [31:0] nB_full = prod_ab + prod_ba;


    assign q_prime[31:16] = nA_full[27:12]; // Q12 shift
    assign q_prime[15:0]  = nB_full[27:12];

endmodule
