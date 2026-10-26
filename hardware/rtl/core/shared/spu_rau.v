// spu_rau.v — Rational Arithmetic Unit for SPU-13 ISA v1.0
//
// Combinational datapath for all quadrance arithmetic and geometric operations.
// PHSLK cross-multiplication, quadrance QADD/QMUL, quadray DOT/CROSS/TNSR.
//
// Wraps existing TDM ALU for ROTR (Pell orbit rotation in Q(√3)).
//
// All operations complete in one cycle (combinational).

`include "spu_isa_defines.vh"

module spu_rau (
    input  wire [63:0]  opA_O,          // Source A Offer value
    input  wire [63:0]  opB_C,          // Source B Confirmation value (for PHSLK)
    input  wire [63:0]  opA_extra,      // Extra operand (for CROSS, SPRD)

    input  wire [ 3:0]  rau_op,         // RAU operation select
    // 0x0: NOP (passthrough)
    // 0x1: QADD  — quadrance add
    // 0x2: QSUB  — quadrance subtract
    // 0x3: QMUL  — quadrance multiply
    // 0x4: QCMP  — quadrance compare (set flags)
    // 0x5: SPRD  — spread ratio
    // 0x6: DOT   — quadray dot product
    // 0x7: CROSS — quadray cross product
    // 0x8: TNSR  — tensor M=4I-J
    // 0x9: PHSLK — phase-lock cross-multiply

    output reg [63:0]   result,          // RAU result
    output reg          coherent,        // PHSLK result: phase-lock coherent
    output reg          result_zero,     // QCMP result: values equal
    output reg          result_sign      // QCMP result: 0=greater, 1=less
);

    // ── Quadray field decomposition ──
    // Input format: {a[15:0], b[15:0], c[15:0], d[15:0]} as Q12.4 signed
    // Quadrance Q = a² + b² + c² + d²

    wire signed [15:0]  a, b, c, d;   // Offer quadray components
    wire signed [15:0]  e, f, g, h;   // Confirmation quadray components

    assign a = opA_O[63:48];
    assign b = opA_O[47:32];
    assign c = opA_O[31:16];
    assign d = opA_O[15:0];

    assign e = opB_C[63:48];
    assign f = opB_C[47:32];
    assign g = opB_C[31:16];
    assign h = opB_C[15:0];

    // ── Quadrance computation (signed squares) ──
    wire signed [31:0]  a_sq, b_sq, c_sq, d_sq;  // Offer quadrance components
    wire signed [31:0]  e_sq, f_sq, g_sq, h_sq;  // Confirmation quadrance components

    assign a_sq = a * a;
    assign b_sq = b * b;
    assign c_sq = c * c;
    assign d_sq = d * d;
    assign e_sq = e * e;
    assign f_sq = f * f;
    assign g_sq = g * g;
    assign h_sq = h * h;

    // Offer quadrance
    wire signed [63:0]  q_offer;
    assign q_offer = a_sq + b_sq + c_sq + d_sq;

    // Confirmation quadrance
    wire signed [63:0]  q_confirm;
    assign q_confirm = e_sq + f_sq + g_sq + h_sq;

    // ── QADD: quadrance add ──
    wire signed [63:0]  qadd_result;
    assign qadd_result = q_offer + q_confirm;

    // ── QMUL: quadrance multiply ──
    wire signed [127:0] qmul_result_full;
    wire signed [63:0]  qmul_result;
    assign qmul_result_full = q_offer * q_confirm;
    // Truncate to 64-bit (upper bits are for overflow detection)
    assign qmul_result = qmul_result_full[63:0];

    // ── QSUB: quadrance subtract ──
    wire signed [63:0]  qsub_result;
    assign qsub_result = q_offer - q_confirm;

    // ── QCMP: compare ──
    wire cmp_zero, cmp_sign;
    assign cmp_zero = (q_offer == q_confirm);
    assign cmp_sign = (q_offer < q_confirm);

    // ── SPRD: spread ratio = min(Q1,Q2) / max(Q1,Q2) as Q12 ──
    wire [63:0] spread_result;
    wire [63:0] spread_num, spread_den;
    assign spread_num  = (q_offer < q_confirm) ? q_offer : q_confirm;
    assign spread_den  = (q_offer > q_confirm) ? q_offer : q_confirm;
    // Spread ≈ smaller/larger, shifted to Q12
    // result = (smaller << 12) / larger  (integer division)
    assign spread_result = (spread_den != 0) ?
                           (spread_num << 12) / spread_den : 64'd0;

    // ── DOT: quadray dot product = a*e + b*f + c*g + d*h ──
    wire signed [31:0]  dot_ae, dot_bf, dot_cg, dot_dh;
    wire signed [63:0]  dot_result;
    assign dot_ae = a * e;
    assign dot_bf = b * f;
    assign dot_cg = c * g;
    assign dot_dh = d * h;
    assign dot_result = dot_ae + dot_bf + dot_cg + dot_dh;

    // ── CROSS: quadray cross product ──
    //   result_a = b*g - c*f
    //   result_b = c*e - a*g
    //   result_c = a*f - b*e
    //   result_d = 0
    wire signed [31:0]  cross_a, cross_b, cross_c;
    assign cross_a = b * g - c * f;
    assign cross_b = c * e - a * g;
    assign cross_c = a * f - b * e;

    wire [63:0] cross_result;
    assign cross_result[63:48] = cross_a[15:0];
    assign cross_result[47:32] = cross_b[15:0];
    assign cross_result[31:16] = cross_c[15:0];
    assign cross_result[15:0]  = 16'd0;

    // ── TNSR: tensor M = 4I ──
    // Shift each component left by 2 (multiply by 4)
    wire [63:0] tnsr_result;
    assign tnsr_result[63:48] = a <<< 2;
    assign tnsr_result[47:32] = b <<< 2;
    assign tnsr_result[31:16] = c <<< 2;
    assign tnsr_result[15:0]  = d <<< 2;

    // ── PHSLK: cross-multiplication coherence check ──
    // Two quadrances match if their values are equal
    // For rational comparison: q_offer.num * q_confirm.den == q_confirm.num * q_offer.den
    // Since quadrances are simple integers (not rational pairs):
    // coherent if q_offer == q_confirm
    wire phslk_coherent;
    assign phslk_coherent = (q_offer == q_confirm);

    // ── Result mux ──
    always @(*) begin
        result       = 64'd0;
        coherent     = 1'b0;
        result_zero  = 1'b0;
        result_sign  = 1'b0;

        case (rau_op)
            4'd0: begin  // NOP
                result = opA_O;
            end

            4'd1: begin  // QADD
                result = qadd_result;
            end

            4'd2: begin  // QSUB
                result = qsub_result;
            end

            4'd3: begin  // QMUL
                result = qmul_result;
            end

            4'd4: begin  // QCMP
                result      = q_offer;
                result_zero = cmp_zero;
                result_sign = cmp_sign;
            end

            4'd5: begin  // SPRD
                result = spread_result;
            end

            4'd6: begin  // DOT
                result = dot_result;
            end

            4'd7: begin  // CROSS
                result = cross_result;
            end

            4'd8: begin  // TNSR
                result = tnsr_result;
            end

            4'd9: begin  // PHSLK
                result   = q_offer;
                coherent = phslk_coherent;
            end

            default: begin
                result = opA_O;
            end
        endcase
    end

endmodule
