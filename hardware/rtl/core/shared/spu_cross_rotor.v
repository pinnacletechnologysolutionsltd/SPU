// spu_cross_rotor.v (v2.0 - 32-bit fields; supports Pell steps 0-7)
// Objective: Perform Q(sqrt3) multiplication: (A + B*sqrt3) * (Ra + Rb*sqrt3)
// Field: Rational Field Q(sqrt3).
// Scaling: Q12 (1.0 = 32'h00001000).
// Width: 32-bit per field; 64-bit products; Q24->Q12 via bits[43:12].

module spu_cross_rotor #(
    parameter DEVICE = "SIM"
) (
    input  wire        clk,
    input  wire        reset,
    input  wire [63:0] q_axis,   // {A[31:0], B[31:0]} - RationalSurd Q12
    input  wire [63:0] r_rotor,  // {Ra[31:0], Rb[31:0]} - SQR Rotor Q12
    output wire [63:0] q_prime   // {A_new[31:0], B_new[31:0]}
);

    wire signed [31:0] A;
    assign A = $signed(q_axis[63:32]);
    wire signed [31:0] B;
    assign B = $signed(q_axis[31:0]);
    wire signed [31:0] Ra;
    assign Ra = $signed(r_rotor[63:32]);
    wire signed [31:0] Rb;
    assign Rb = $signed(r_rotor[31:0]);

    // Stage 1: DSP Multiplication (registered)
    wire signed [63:0] prod_aa;
    wire signed [63:0] prod_bb;
    wire signed [63:0] prod_ab;
    wire signed [63:0] prod_ba;

    spu_gowin_mult32 #(.DEVICE(DEVICE)) u_mult_aa (
        .clk(clk),
        .reset(reset),
        .a(A),
        .b(Ra),
        .p(prod_aa)
    );

    spu_gowin_mult32 #(.DEVICE(DEVICE)) u_mult_bb (
        .clk(clk),
        .reset(reset),
        .a(B),
        .b(Rb),
        .p(prod_bb)
    );

    spu_gowin_mult32 #(.DEVICE(DEVICE)) u_mult_ab (
        .clk(clk),
        .reset(reset),
        .a(A),
        .b(Rb),
        .p(prod_ab)
    );

    spu_gowin_mult32 #(.DEVICE(DEVICE)) u_mult_ba (
        .clk(clk),
        .reset(reset),
        .a(B),
        .b(Ra),
        .p(prod_ba)
    );

    // Stage 2: Cross-product assembly (combinatorial)
    // (A + B*sqrt3)(Ra + Rb*sqrt3) = (A*Ra + 3*B*Rb) + (A*Rb + B*Ra)*sqrt3
    wire signed [63:0] nA_full;
    assign nA_full = prod_aa + ((prod_bb << 1) + prod_bb);
    wire signed [63:0] nB_full;
    assign nB_full = prod_ab + prod_ba;

    // Q12*Q12 = Q24; shift right 12 to restore Q12 (extract bits [43:12])
    assign q_prime[63:32] = nA_full[43:12];
    assign q_prime[31:0]  = nB_full[43:12];

endmodule
