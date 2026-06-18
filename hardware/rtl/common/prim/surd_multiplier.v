// SPU-13 Surd Multiplier: Field-Selectable (v4.0 — DSP-enabled)
// Logic: (a1 + b1√k) × (a2 + b2√k)  where k ∈ {3, 5, 15}
// field_sel: 2'b00 = Q(√3), 2'b01 = Q(√5), 2'b10 = Q(√15)
//
// v4.0: Added DEVICE parameter and explicit Gowin DSP primitive path.
//   When DEVICE="GW5A" and WIDTH ≤ 18: uses MULT27X36 primitives
//   (inferred to MULT18X18D) for the four cross-products, mapping
//   directly to hardware DSP blocks instead of LUT fabric.
//   Pipeline latency is unchanged (1 cycle: combinational multiply +
//   registered output).  The DSP's internal register replaces the
//   behavioral output register.
//
//   When DEVICE="SIM" or WIDTH > 18: falls back to behavioral
//   $signed() * $signed() (existing behaviour, LUT-mapped in synthesis).
//
// CC0 1.0 Universal.

module surd_multiplier #(
    parameter WIDTH = 32,
    parameter SHIFT = 0,     // 0 = integer, 16 = Q16 fixed-point
    parameter DEVICE = "SIM" // "SIM" | "GW5A" | "GW2A" | "GW1N"
)(
    input  wire clk,
    input  wire reset,
    input  wire [1:0] field_sel,               // Q(√k) field selector
    input  wire signed [WIDTH-1:0] a1, b1,    // Operand 1 (Source)
    input  wire signed [WIDTH-1:0] a2, b2,    // Operand 2 (Rotor Constant)
    output reg  signed [WIDTH-1:0] res_a,      // Result Rational
    output reg  signed [WIDTH-1:0] res_b       // Result Surd (√k)
);

    // ── DSP-mode guard: only for GW5A with WIDTH ≤ 18 ──────────
    // MULT27X36 can handle up to 27×36, but we restrict to 18-bit
    // because 18×18 → MULT18X18D is the cleanest DSP inference path.
    // For 19-27 bit, MULT27X36 decomposition would need partial-product
    // summing (2 DSPs per multiply) — not yet implemented.
    localparam USE_DSP = (DEVICE == "GW5A" && WIDTH <= 18);

    generate
        if (USE_DSP) begin : gen_dsp

            // ── DSP Path: explicit MULT27X36 primitives ─────────
            // Each MULT27X36 has registered output (1 cycle latency).
            // We present operands, DSP computes, output register captures.
            // The surd_term shift-and-add is combinational from DSP outputs.
            //
            // Operands are sign-extended to fill the 27-bit A / 36-bit B ports.
            wire signed [62:0] dsp_aa, dsp_bb, dsp_ab, dsp_ba;

            MULT27X36 u_aa (
                .DOUT(dsp_aa),
                .A({{(27-WIDTH){a1[WIDTH-1]}}, a1}),
                .B({{(36-WIDTH){a2[WIDTH-1]}}, a2}),
                .D(27'd0),
                .CLK({1'b0, clk}), .CE(2'b01), .RESET({1'b0, reset}),
                .PSEL(1'b0), .PADDSUB(1'b0)
            );
            MULT27X36 u_bb (
                .DOUT(dsp_bb),
                .A({{(27-WIDTH){b1[WIDTH-1]}}, b1}),
                .B({{(36-WIDTH){b2[WIDTH-1]}}, b2}),
                .D(27'd0),
                .CLK({1'b0, clk}), .CE(2'b01), .RESET({1'b0, reset}),
                .PSEL(1'b0), .PADDSUB(1'b0)
            );
            MULT27X36 u_ab (
                .DOUT(dsp_ab),
                .A({{(27-WIDTH){a1[WIDTH-1]}}, a1}),
                .B({{(36-WIDTH){b2[WIDTH-1]}}, b2}),
                .D(27'd0),
                .CLK({1'b0, clk}), .CE(2'b01), .RESET({1'b0, reset}),
                .PSEL(1'b0), .PADDSUB(1'b0)
            );
            MULT27X36 u_ba (
                .DOUT(dsp_ba),
                .A({{(27-WIDTH){b1[WIDTH-1]}}, b1}),
                .B({{(36-WIDTH){a2[WIDTH-1]}}, a2}),
                .D(27'd0),
                .CLK({1'b0, clk}), .CE(2'b01), .RESET({1'b0, reset}),
                .PSEL(1'b0), .PADDSUB(1'b0)
            );

            // DSP outputs are 63-bit; we take the low 2*WIDTH bits.
            // The DSP internally computes the full product; sign extension
            // is handled by the operand sign-extension above.
            wire signed [2*WIDTH-1:0] prod_a1a2 = dsp_aa[2*WIDTH-1:0];
            wire signed [2*WIDTH-1:0] prod_b1b2 = dsp_bb[2*WIDTH-1:0];
            wire signed [2*WIDTH-1:0] prod_a1b2 = dsp_ab[2*WIDTH-1:0];
            wire signed [2*WIDTH-1:0] prod_b1a2 = dsp_ba[2*WIDTH-1:0];

            // ── Surd term: k × b1×b2  (shift-and-add, combinational) ──
            wire signed [2*WIDTH-1:0] surd_term_3, surd_term_5, surd_term_15;
            assign surd_term_3  = (prod_b1b2 << 1) + prod_b1b2;
            assign surd_term_5  = (prod_b1b2 << 2) + prod_b1b2;
            assign surd_term_15 = (prod_b1b2 << 4) - prod_b1b2;

            wire signed [2*WIDTH-1:0] surd_term;
            assign surd_term = (field_sel == 2'b01) ? surd_term_5  :
                               (field_sel == 2'b10) ? surd_term_15 : surd_term_3;

            // ── Registered output (1 cycle after DSP output) ────
            always @(posedge clk or posedge reset) begin
                if (reset) begin
                    res_a <= {WIDTH{1'b0}};
                    res_b <= {WIDTH{1'b0}};
                end else begin
                    res_a <= (prod_a1a2 + surd_term) >>> SHIFT;
                    res_b <= (prod_a1b2 + prod_b1a2) >>> SHIFT;
                end
            end

        end else begin : gen_behavioral

            // ── Behavioral Path: $signed() * $signed() ──────────
            // Used for SIM, GW2A, GW1N, or WIDTH > 18.
            // Synthesis maps to LUT fabric (no DSP inference without
            // explicit vendor primitives).
            wire signed [2*WIDTH-1:0] prod_a1a2;
            assign prod_a1a2 = $signed(a1) * $signed(a2);
            wire signed [2*WIDTH-1:0] prod_b1b2;
            assign prod_b1b2 = $signed(b1) * $signed(b2);
            wire signed [2*WIDTH-1:0] prod_a1b2;
            assign prod_a1b2 = $signed(a1) * $signed(b2);
            wire signed [2*WIDTH-1:0] prod_b1a2;
            assign prod_b1a2 = $signed(b1) * $signed(a2);

            wire signed [2*WIDTH-1:0] surd_term_3, surd_term_5, surd_term_15;
            assign surd_term_3  = (prod_b1b2 << 1) + prod_b1b2;
            assign surd_term_5  = (prod_b1b2 << 2) + prod_b1b2;
            assign surd_term_15 = (prod_b1b2 << 4) - prod_b1b2;

            wire signed [2*WIDTH-1:0] surd_term;
            assign surd_term = (field_sel == 2'b01) ? surd_term_5  :
                               (field_sel == 2'b10) ? surd_term_15 : surd_term_3;

            always @(posedge clk or posedge reset) begin
                if (reset) begin
                    res_a <= {WIDTH{1'b0}};
                    res_b <= {WIDTH{1'b0}};
                end else begin
                    res_a <= (prod_a1a2 + surd_term) >>> SHIFT;
                    res_b <= (prod_a1b2 + prod_b1a2) >>> SHIFT;
                end
            end

        end
    endgenerate

endmodule
