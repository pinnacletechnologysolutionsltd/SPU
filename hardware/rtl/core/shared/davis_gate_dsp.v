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

    // IVM pairwise differences: (ci-cj) for i<j
    assign diffAB = $signed(A) - $signed(B);
    assign diffAC = $signed(A) - $signed(C);
    assign diffAD = $signed(A) - $signed(D);
    assign diffBC = $signed(B) - $signed(C);
    assign diffBD = $signed(B) - $signed(D);
    assign diffCD = $signed(C) - $signed(D);

    // Quadrance & IVM multipliers
    generate
        if (DEVICE == "GW2A" || DEVICE == "GW5A" || DEVICE == "GOWIN") begin : gen_gowin_dsp
            // Quadrance Squares
            wire signed [35:0] p_A2, p_B2, p_C2, p_D2;
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_A2 (.clk(clk), .a({{2{A[15]}}, A}), .b({{2{A[15]}}, A}), .p(p_A2));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_B2 (.clk(clk), .a({{2{B[15]}}, B}), .b({{2{B[15]}}, B}), .p(p_B2));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_C2 (.clk(clk), .a({{2{C[15]}}, C}), .b({{2{C[15]}}, C}), .p(p_C2));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_D2 (.clk(clk), .a({{2{D[15]}}, D}), .b({{2{D[15]}}, D}), .p(p_D2));

            reg signed [31:0] A2_r, B2_r, C2_r, D2_r;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    A2_r <= 32'd0; B2_r <= 32'd0; C2_r <= 32'd0; D2_r <= 32'd0;
                end else begin
                    A2_r <= p_A2[31:0];
                    B2_r <= p_B2[31:0];
                    C2_r <= p_C2[31:0];
                    D2_r <= p_D2[31:0];
                end
            end
            assign A2 = A2_r;
            assign B2 = B2_r;
            assign C2 = C2_r;
            assign D2 = D2_r;

            // IVM pair squares
            wire signed [35:0] p_AB, p_AC, p_AD, p_BC, p_BD, p_CD;
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_AB (.clk(clk), .a({{2{diffAB[15]}}, diffAB[15:0]}), .b({{2{diffAB[15]}}, diffAB[15:0]}), .p(p_AB));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_AC (.clk(clk), .a({{2{diffAC[15]}}, diffAC[15:0]}), .b({{2{diffAC[15]}}, diffAC[15:0]}), .p(p_AC));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_AD (.clk(clk), .a({{2{diffAD[15]}}, diffAD[15:0]}), .b({{2{diffAD[15]}}, diffAD[15:0]}), .p(p_AD));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_BC (.clk(clk), .a({{2{diffBC[15]}}, diffBC[15:0]}), .b({{2{diffBC[15]}}, diffBC[15:0]}), .p(p_BC));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_BD (.clk(clk), .a({{2{diffBD[15]}}, diffBD[15:0]}), .b({{2{diffBD[15]}}, diffBD[15:0]}), .p(p_BD));
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_CD (.clk(clk), .a({{2{diffCD[15]}}, diffCD[15:0]}), .b({{2{diffCD[15]}}, diffCD[15:0]}), .p(p_CD));

            reg signed [31:0] ivm_accum_r;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) ivm_accum_r <= 32'd0;
                else ivm_accum_r <= p_AB[31:0] + p_AC[31:0] + p_AD[31:0] + p_BC[31:0] + p_BD[31:0] + p_CD[31:0];
            end
            assign ivm_accum = ivm_accum_r;
        end else begin : gen_sim_math
            assign A2 = $signed(A) * $signed(A);
            assign B2 = $signed(B) * $signed(B);
            assign C2 = $signed(C) * $signed(C);
            assign D2 = $signed(D) * $signed(D);
            assign ivm_accum = ($signed(diffAB) * $signed(diffAB)) + ($signed(diffAC) * $signed(diffAC)) + ($signed(diffAD) * $signed(diffAD))
                             + ($signed(diffBC) * $signed(diffBC)) + ($signed(diffBD) * $signed(diffBD)) + ($signed(diffCD) * $signed(diffCD));
        end
    endgenerate

    // Quadrance: A^2 + 3*B^2 + C^2 + D^2
    assign quad_accum = A2 + (B2 * 3) + C2 + D2;
    assign quadrance = quad_accum[31:0];
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
