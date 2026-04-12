// Simplified simulatable davis_gate_dsp.v (simulation-friendly stub)
// Computes gasket_sum, quadrance and ivm_quadrance combinationally.
module davis_gate_dsp #(
    parameter DEVICE = "SIM"
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [63:0] q_vector,
    output wire [63:0] q_rotated,
    output wire [31:0] quadrance,
    output wire [31:0] ivm_quadrance,
    output wire [15:0] gasket_sum,
    output wire signed [31:0] audio_p,
    output wire signed [31:0] audio_q
);

    // Declarations
    wire signed [15:0] A;
    wire signed [15:0] B;
    wire signed [15:0] C;
    wire signed [15:0] D;

    wire signed [31:0] A2;
    wire signed [31:0] B2;
    wire signed [31:0] C2;
    wire signed [31:0] D2;

    wire signed [31:0] diffAB;
    wire signed [31:0] diffAC;
    wire signed [31:0] diffAD;
    wire signed [31:0] diffBC;
    wire signed [31:0] diffBD;
    wire signed [31:0] diffCD;

    wire signed [31:0] ivm_accum;
    wire signed [31:0] quad_accum;

    // Unpack inputs
    assign A = q_vector[63:48];
    assign B = q_vector[47:32];
    assign C = q_vector[31:16];
    assign D = q_vector[15:0];

    // Gasket sum
    assign gasket_sum = A + B + C + D;

    // Squares
    assign A2 = $signed(A) * $signed(A);
    assign B2 = $signed(B) * $signed(B);
    assign C2 = $signed(C) * $signed(C);
    assign D2 = $signed(D) * $signed(D);

    // Quadrance: A^2 + 3*B^2 + C^2 + D^2
    assign quad_accum = A2 + (B2 * 3) + C2 + D2;
    assign quadrance = quad_accum[31:0];

    // IVM pairwise quadrance: sum of (ci-cj)^2 for i<j
    assign diffAB = $signed(A) - $signed(B);
    assign diffAC = $signed(A) - $signed(C);
    assign diffAD = $signed(A) - $signed(D);
    assign diffBC = $signed(B) - $signed(C);
    assign diffBD = $signed(B) - $signed(D);
    assign diffCD = $signed(C) - $signed(D);

    assign ivm_accum = (diffAB * diffAB) + (diffAC * diffAC) + (diffAD * diffAD)
                     + (diffBC * diffBC) + (diffBD * diffBD) + (diffCD * diffCD);
    assign ivm_quadrance = ivm_accum[31:0];

    // Rotate
    assign q_rotated[63:48] = B;
    assign q_rotated[47:32] = C;
    assign q_rotated[31:16] = D;
    assign q_rotated[15:0]  = A;

    // Audio outputs unused in simulation stub
    assign audio_p = 32'sd0;
    assign audio_q = 32'sd0;

endmodule
