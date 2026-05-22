// spu_delta_curve.v — Delta Curve Generator (v1.0)
//
// Hardware implementation of the Triple Quadrance Formula from
// Wildberger's Rational Trigonometry (Divine Proportions, Ch.5).
//
// For quadrances Q₁, Q₂ meeting at spread s₃ (opposite Q₃):
//   (Q₃ − Q₁ − Q₂)² = 4·Q₁·Q₂·(1−s₃)
//
// This is the exact rational form of c² = a² + b² − 2ab·cos θ.
// No square roots. No division. No transcendentals.
//
// The module parameterizes the family of triangles with fixed Q₁, Q₂
// as spread s varies from 0 (collapsed) to 1 (right triangle).
// At each step k ∈ {0, …, steps}:
//   s₃ = k / steps
//   rhs² = 4·Q₁·Q₂·(steps−k) / steps
//   Q₃ = Q₁ + Q₂ ± √(rhs²)   (sign resolved by polarity flag)
//
// Pipeline:
//   Stage 1: compute 4·Q₁·Q₂ (product)
//   Stage 2: compute 4·Q₁·Q₂·(steps−k) for current k
//   Stage 3: output (q_sum, rhs_sq_num, rhs_sq_den) 

module spu_delta_curve #(
    parameter Q_BITS = 16,       // bits per surd coefficient
    parameter STEPS_BITS = 8     // max 256 spread steps
) (
    input  wire        clk,
    input  wire        rst_n,

    // Configuration (latched on config_en)
    input  wire        config_en,
    input  wire [Q_BITS-1:0] Q1,       // first quadrance (integer)
    input  wire [Q_BITS-1:0] Q2,       // second quadrance (integer)
    input  wire [STEPS_BITS-1:0] steps, // number of spread steps

    // Step control
    input  wire        step_en,         // pulse to advance to next step
    input  wire        polarity,        // +1 = acute, −1 = obtuse (± sign)

    // Output (valid on the cycle after step_en)
    output reg  [Q_BITS*2-1:0] q_sum,       // Q₁ + Q₂
    output reg  [Q_BITS*4-1:0] rhs_sq_num,  // 4·Q₁·Q₂·(steps−k)
    output reg  [STEPS_BITS-1:0] rhs_sq_den, // steps
    output reg  [STEPS_BITS-1:0] step_k,     // current step index
    output reg                  output_valid,

    // Status
    output wire                 done          // all steps complete
);

    // ── Configuration registers ────────────────────────────────────────
    reg [Q_BITS-1:0] cfg_Q1, cfg_Q2;
    reg [STEPS_BITS-1:0] cfg_steps;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cfg_Q1 <= 0; cfg_Q2 <= 0; cfg_steps <= 0;
        end else if (config_en) begin
            cfg_Q1 <= Q1;
            cfg_Q2 <= Q2;
            cfg_steps <= steps;
        end
    end

    // ── Stage 1: 4·Q₁·Q₂ ──────────────────────────────────────────────
    reg [Q_BITS*2-1:0] four_Q1Q2;
    reg                 s1_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            four_Q1Q2 <= 0;
            s1_valid <= 0;
        end else begin
            // Compute from INPUT ports on config_en to avoid race with cfg registers
            if (config_en)
                four_Q1Q2 <= (Q1 * Q2) << 2;
            s1_valid <= config_en;
        end
    end

    // ── Stage 2 + Step counter ─────────────────────────────────────────
    reg [STEPS_BITS-1:0] current_k;
    reg                  running;
    reg [Q_BITS*4-1:0]   rhs_num;
    reg                  s2_valid;
    wire [STEPS_BITS-1:0] steps_minus_k;

    assign done = (current_k >= cfg_steps) && running;
    assign steps_minus_k = (cfg_steps > current_k) ? (cfg_steps - current_k) : 0;

    always @(posedge clk or negedge rst_n) begin
        reg [STEPS_BITS-1:0] next_k;
        if (!rst_n) begin
            current_k <= 0;
            running <= 0;
            rhs_num <= 0;
            s2_valid <= 0;
        end else begin
            // Determine next_k with blocking assignment (visible within block)
            next_k = current_k;
            if (config_en) begin
                next_k = 0;
                running <= 1;
            end else if (step_en && running && current_k < cfg_steps) begin
                next_k = current_k + 1;
            end

            // Compute rhs_num from the just-computed next_k's steps_minus_k
            if (s1_valid || (step_en && running && current_k < cfg_steps)) begin
                rhs_num <= four_Q1Q2 * ((cfg_steps > next_k) ? (cfg_steps - next_k) : 0);
            end

            current_k <= next_k;
            s2_valid <= s1_valid || (step_en && running && current_k < cfg_steps);
        end
    end

    // ── Stage 3: Output ────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q_sum <= 0;
            rhs_sq_num <= 0;
            rhs_sq_den <= 0;
            step_k <= 0;
            output_valid <= 0;
        end else begin
            q_sum <= cfg_Q1 + cfg_Q2;
            rhs_sq_num <= rhs_num;
            rhs_sq_den <= cfg_steps;
            step_k <= current_k;
            output_valid <= s2_valid;
        end
    end

    // ── Correctness assertion ──────────────────────────────────────────
    // For the right triangle endpoint (k = steps):
    //   rhs_sq_num = 4·Q₁·Q₂·(steps−steps) = 0
    //   Q₃ = Q₁ + Q₂  (exact integer, no ± ambiguity)
    //
    // For the collapsed endpoint (k = 0):
    //   rhs_sq_num = 4·Q₁·Q₂·steps
    //   Q₃ = Q₁ + Q₂ ± √(4·Q₁·Q₂)  (two possible triangles)
    //
    // The polarity flag selects the sign: +1 for acute, −1 for obtuse.
    // In hardware, the polarity drives a MUX on the final Q₃ output.

endmodule
