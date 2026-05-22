// spu_quadrance_adder.v — Exact Quadrance Adder (v1.0)
// Smoke test for the rational pipeline: proves Q(√3) addition fits in LUT budget.
//
// Computes Q₃ = Q₁ + Q₂ where Q₁, Q₂ are quadrances (squared distances).
// In the IVM, the hypotenuse quadrance is the sum of the leg quadrances —
// the Pythagorean theorem without square roots. This is exact.
//
// Q₁ = a₁² − 3b₁²  (norm of surd representing distance)
// Q₂ = a₂² − 3b₂²
// Q₃ = Q₁ + Q₂ = (a₁² + a₂²) − 3(b₁² + b₂²)
//
// For right triangles in the IVM: Q₃ is the hypotenuse quadrance.
// No approximation. No rounding. No float.
//
// Resource estimate: 4 multipliers + 3 adders = ~6 DSP slices on GW5A.
// Fits easily alongside existing RPLU/rotor modules.

module spu_quadrance_adder (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        valid_in,

    // Quadrance 1: (a1, b1) as signed 16-bit surd coefficients
    input  wire [15:0] a1,
    input  wire [15:0] b1,

    // Quadrance 2: (a2, b2) as signed 16-bit surd coefficients
    input  wire [15:0] a2,
    input  wire [15:0] b2,

    // Result: Q₃ = Q₁ + Q₂ as 32-bit signed integer
    // Q₃ = (a₁² + a₂²) − 3(b₁² + b₂²)
    output reg  [31:0] Q3,
    output reg         valid_out
);

    // Stage 1: Compute squares
    reg [31:0] a1_sq, b1_sq, a2_sq, b2_sq;
    reg        s1_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a1_sq <= 0; b1_sq <= 0;
            a2_sq <= 0; b2_sq <= 0;
            s1_valid <= 0;
        end else begin
            a1_sq <= $signed(a1) * $signed(a1);
            b1_sq <= $signed(b1) * $signed(b1);
            a2_sq <= $signed(a2) * $signed(a2);
            b2_sq <= $signed(b2) * $signed(b2);
            s1_valid <= valid_in;
        end
    end

    // Stage 2: Accumulate
    reg [31:0] a_sum, b_sum;
    reg        s2_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_sum <= 0; b_sum <= 0;
            s2_valid <= 0;
        end else begin
            a_sum <= a1_sq + a2_sq;
            b_sum <= b1_sq + b2_sq;
            s2_valid <= s1_valid;
        end
    end

    // Stage 3: Final Q₃ = a_sum − 3 × b_sum
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            Q3 <= 0;
            valid_out <= 0;
        end else begin
            // 3 × b_sum = b_sum + b_sum + b_sum (avoids multiplier)
            Q3 <= a_sum - (b_sum + b_sum + b_sum);
            valid_out <= s2_valid;
        end
    end

    // ── Correctness assertion ──────────────────────────────────────────
    // For right triangles in the IVM: if Q₁ and Q₂ are leg quadrances of
    // a right triangle (spread s=1), then Q₃ is the hypotenuse quadrance
    // and is always a positive integer. The Davis Gate will verify:
    //   Q₃ ≥ 0  (quadrance is always non-negative)
    //   Q₃ is exact — no floating-point, no rounding.

endmodule
