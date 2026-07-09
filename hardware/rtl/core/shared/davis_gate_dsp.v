// davis_gate_dsp.v — Davis Gate: gasket sum, IVM quadrance, stiffness
//
// The quadrance output is the Davis stiffness:
//   stiffness = ivm_quadrance + gasket_sum² = 4·Σc²
// where ivm_quadrance = Σᵢ<ⱼ(cᵢ−cⱼ)² (6 pairwise terms).
//
// Normative formula: knowledge/SPU_LEXICON.md ("Davis Gate" entry, 2026-07-08).
// The gasket_sum = A+B+C+D path drives Henosis and is unaffected.
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

    // IVM quadrance + stiffness multipliers
    generate
        if (DEVICE == "GW2A" || DEVICE == "GW5A" || DEVICE == "GOWIN") begin : gen_gowin_dsp
            // ── IVM pair squares (6 DSPs, 2-cycle pipeline) ──────────────
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

            // ── Gasket sum square (1 DSP, 2-cycle to match ivm_accum) ────
            // Stage 1: register gasket_sum
            reg signed [15:0] gs_r1;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) gs_r1 <= 16'd0;
                else gs_r1 <= gasket_sum;
            end

            // Stage 1: gasket_sum² via DSP multiplier
            wire signed [35:0] p_gs_sq;
            spu_gowin_multiplier #(.DEVICE(DEVICE)) m_gs_sq (
                .clk(clk),
                .a({{2{gs_r1[15]}}, gs_r1}),
                .b({{2{gs_r1[15]}}, gs_r1}),
                .p(p_gs_sq)
            );

            // Stage 2: register square result
            reg signed [31:0] gs_sq_r2;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) gs_sq_r2 <= 32'd0;
                else gs_sq_r2 <= p_gs_sq[31:0];
            end

            // Stiffness = ivm_quadrance + gasket_sum²  (both at 2-cycle depth)
            assign quad_accum = ivm_accum + gs_sq_r2;

        end else begin : gen_sim_math
            // ── SIM path: combinational ──────────────────────────────────
            assign ivm_accum = ($signed(diffAB) * $signed(diffAB)) + ($signed(diffAC) * $signed(diffAC)) + ($signed(diffAD) * $signed(diffAD))
                             + ($signed(diffBC) * $signed(diffBC)) + ($signed(diffBD) * $signed(diffBD)) + ($signed(diffCD) * $signed(diffCD));

            // Stiffness = ivm_quadrance + gasket_sum²  (combinational)
            assign quad_accum = ivm_accum + ($signed(gasket_sum) * $signed(gasket_sum));
        end
    endgenerate

    assign quadrance     = quad_accum[31:0];
    assign ivm_quadrance = ivm_accum[31:0];

    // Rotate
    assign q_rotated[63:48] = B;
    assign q_rotated[47:32] = C;
    assign q_rotated[31:16] = D;
    assign q_rotated[15:0]  = A;

    // Audio outputs unused
    assign audio_p = 32'sd0;
    assign audio_q = 32'sd0;

endmodule
