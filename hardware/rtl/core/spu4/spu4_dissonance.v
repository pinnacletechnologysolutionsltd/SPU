// spu4_dissonance.v — saturating Quadray residual (Davis gasket sum)
//
// dissonance[7:0] = min(|A+B+C+D|, 255)
//   0x00  laminar — the four axes sum to zero, the Davis identity holds
//   0xFF  saturated — residual is 255 or greater
//
// Exact integer arithmetic, no epsilon, no division, purely combinational.
//
// ── Why 19 bits ──────────────────────────────────────────────────────
// Four 16-bit signed addends span [-131072, +131068]. 18 bits *hold* that
// range, but the absolute-value step negates, and negating -131072 in 18-bit
// signed wraps back to -131072. So the intermediate is 19 bits.
//
// This computation lived duplicated in spu4_core.v and spu4_standalone_top.v,
// kept in step only by a comment saying they must not diverge. On 2026-08-15
// they did diverge — the wrapper had no dissonance port at all — and the
// shared width bug below had to be fixed in two places. It is one module now.
//
// ── The bug this module's width fixes (2026-08-16) ───────────────────
// The intermediate was 17 bits, so the sum wrapped modulo 131072 *before* the
// saturation test could see it, and a maximal residual reported as laminar:
//
//   A=B=C=D=0x8000  true sum -131072  ->  read 0x00  (claims perfectly laminar)
//   A=B=C=D=0x7FFF  true sum  131068  ->  read 0x04  (claims near-laminar)
//
// A saturating fault signal that reads clean under the largest possible fault
// is worse than no signal, because it is trusted. The width is load-bearing.
// Covered by hardware/tests/spu4/spu4_dissonance_width_tb.v.

module spu4_dissonance (
    input  wire signed [15:0] A,
    input  wire signed [15:0] B,
    input  wire signed [15:0] C,
    input  wire signed [15:0] D,
    output wire        [7:0]  dissonance
);

    // Sign-extend each 16-bit addend to 19 bits before summing, so the sum is
    // evaluated at 19 bits rather than in a narrower context.
    wire signed [18:0] gasket_sum_ext;
    assign gasket_sum_ext = {{3{A[15]}}, A} + {{3{B[15]}}, B}
                          + {{3{C[15]}}, C} + {{3{D[15]}}, D};

    wire [18:0] abs_sum;
    assign abs_sum = gasket_sum_ext[18] ? (~gasket_sum_ext + 19'd1)
                                        : gasket_sum_ext;

    assign dissonance = (abs_sum > 19'd255) ? 8'hFF : abs_sum[7:0];

endmodule
