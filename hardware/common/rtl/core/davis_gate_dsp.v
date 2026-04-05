// davis_gate_dsp.v (v2.1 — Multi-Target: GOWIN / SIM)
// 4-axis Quadray Davis Law Gasket: quadrance check + IVM basis rotation.
// Replaces iCE40 SB_MAC16 with gowin_mult18 (DEVICE-parameterised).
// DEVICE="SIM" uses inferred multiply — fully simulatable with iverilog.
//
// v2.1: Added ivm_quadrance output — pairwise Quadray metric Σᵢ<ⱼ(cᵢ-cⱼ)²
//   This matches spu_wildberger.h Layer 8 and C++ Quadray::quadrance().
//   The original 'quadrance' output (A²+3B²+C²+D²) is preserved unchanged
//   as the Q(√3) stiffness / Davis stability measure.
//
// Distinction:
//   quadrance     = A²+3B²+C²+D²          (surd stiffness, positive definite)
//   ivm_quadrance = Σᵢ<ⱼ(cᵢ-cⱼ)²         (IVM distance metric, matches C++)
//   For (A,B,C,D)=(4,3,2,1): quadrance=48, ivm_quadrance=20
//
// CC0 1.0 Universal.

module davis_gate_dsp #(
    parameter DEVICE = "GW2A"  // "GW1N" | "GW2A" | "GW5A" | "SIM"
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire [63:0] q_vector,     // 4×16-bit Quadray input  {A, B, C, D}
    output wire [63:0] q_rotated,    // 60° IVM basis rotation  {B, C, D, A}
    output wire [31:0] quadrance,    // Q(√3) stiffness: A²+3B²+C²+D²
    output wire [31:0] ivm_quadrance,// IVM pairwise metric: Σᵢ<ⱼ(cᵢ-cⱼ)²
    output wire [15:0] gasket_sum    // Davis Zero-Sum check: A+B+C+D (→0)
);

    wire [15:0] A = q_vector[63:48];
    wire [15:0] B = q_vector[47:32];
    wire [15:0] C = q_vector[31:16];
    wire [15:0] D = q_vector[15:0];

    // 1. Gasket Sum — combinational LUT, no DSP needed
    assign gasket_sum = A + B + C + D;

    // 2. Quadrance via 4× gowin_mult18
    //    Q(√3) components are signed Q12 — sign-extend to 18-bit so that
    //    squaring negative values (e.g. A=0xF800=-0.5) is bit-exact.
    wire signed [17:0] A18 = {{2{A[15]}}, A};
    wire signed [17:0] B18 = {{2{B[15]}}, B};
    wire signed [17:0] C18 = {{2{C[15]}}, C};
    wire signed [17:0] D18 = {{2{D[15]}}, D};

    wire signed [35:0] A2_36, B2_36, C2_36, D2_36;

    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_sq_A (
        .clk(clk), .rst_n(rst_n), .ce(1'b1),
        .A(A18), .B(A18), .C(36'sd0), .P(A2_36)
    );
    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_sq_B (
        .clk(clk), .rst_n(rst_n), .ce(1'b1),
        .A(B18), .B(B18), .C(36'sd0), .P(B2_36)
    );
    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_sq_C (
        .clk(clk), .rst_n(rst_n), .ce(1'b1),
        .A(C18), .B(C18), .C(36'sd0), .P(C2_36)
    );
    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_sq_D (
        .clk(clk), .rst_n(rst_n), .ce(1'b1),
        .A(D18), .B(D18), .C(36'sd0), .P(D2_36)
    );

    // Lower 32 bits hold the full square for any 16-bit input
    wire [31:0] A2 = A2_36[31:0];
    wire [31:0] B2 = B2_36[31:0];
    wire [31:0] C2 = C2_36[31:0];
    wire [31:0] D2 = D2_36[31:0];

    // Q(√3) quadrance invariant: A² + 3B² + C² + D²  (surd stiffness)
    wire [31:0] B2_3 = B2 + (B2 << 1);
    assign quadrance = A2 + B2_3 + C2 + D2;

    // IVM pairwise quadrance: Σᵢ<ⱼ (cᵢ-cⱼ)²  — 6 difference-square terms.
    // Matches C++ Quadray::quadrance() exactly. Uses 6 additional DSP18s
    // in synthesis; shares A2/B2/C2/D2 to halve the multiply count via:
    //   (A-B)² = A²-2AB+B², (A-C)²=A²-2AC+C², ...
    // Here computed combinationally from the already-squared terms + cross terms.
    wire signed [31:0] AB = $signed(A) * $signed(B);
    wire signed [31:0] AC = $signed(A) * $signed(C);
    wire signed [31:0] AD = $signed(A) * $signed(D);
    wire signed [31:0] BC = $signed(B) * $signed(C);
    wire signed [31:0] BD = $signed(B) * $signed(D);
    wire signed [31:0] CD = $signed(C) * $signed(D);

    // (cᵢ-cⱼ)² = cᵢ²-2cᵢcⱼ+cⱼ²;  Σᵢ<ⱼ = 3(A²+B²+C²+D²) - 2(AB+AC+AD+BC+BD+CD)
    wire [31:0] sum_sq       = A2 + B2 + C2 + D2;
    wire signed [31:0] cross = AB + AC + AD + BC + BD + CD;
    wire [31:0] three_sum_sq = sum_sq + sum_sq + sum_sq;
    wire [31:0] two_cross    = $unsigned(cross + cross);
    assign ivm_quadrance     = three_sum_sq - two_cross;

    // 3. 60° IVM basis rotation: A→B→C→D→A (pure wiring, zero latency)
    assign q_rotated[63:48] = B;
    assign q_rotated[47:32] = C;
    assign q_rotated[31:16] = D;
    assign q_rotated[15:0]  = A;

endmodule
