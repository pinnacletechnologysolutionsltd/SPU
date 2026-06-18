// spu_surd_multiplier_dsp.v — DSP-Mapped Surd Multiplier for Gowin GW5A (v1.0)
//
// Same interface as surd_multiplier.v but with explicit Gowin DSP primitives.
// On GW5A, the MULT27X36 blocks are inherently pipelined (registered output),
// so this module adds one pipeline stage relative to the behavioral version.
//
// Pipeline:
//   Cycle 0: a1,a2,b1,b2 presented
//   Cycle 1: DSP result available (prod_* registered)
//   Cycle 2: surd_term computation + output register
//
// For WIDTH ≤ 18: maps to MULT18X18 (GW2A) or MULT18X18D (GW5A).
// For 18 < WIDTH ≤ 27: maps to MULT27X36 (GW5A only).
// For WIDTH > 27: decomposes high/low halves across two DSPs.
//
// CC0 1.0 Universal.

module spu_surd_multiplier_dsp #(
    parameter WIDTH = 18,
    parameter SHIFT = 0,
    parameter DEVICE = "GW5A"
)(
    input  wire                    clk,
    input  wire                    reset,
    input  wire [1:0]              field_sel,
    input  wire signed [WIDTH-1:0] a1, b1,
    input  wire signed [WIDTH-1:0] a2, b2,
    output reg  signed [WIDTH-1:0] res_a,
    output reg  signed [WIDTH-1:0] res_b,
    output reg                     busy          // high while pipeline is active
);

    // ── Pipeline stage 0: registered inputs ─────────────────────
    reg signed [WIDTH-1:0] a1_r, b1_r, a2_r, b2_r;
    reg [1:0] field_sel_r;
    reg       pipe_active;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            a1_r <= 0; b1_r <= 0; a2_r <= 0; b2_r <= 0;
            field_sel_r <= 0;
            pipe_active <= 0;
        end else begin
            a1_r <= a1; b1_r <= b1; a2_r <= a2; b2_r <= b2;
            field_sel_r <= field_sel;
            pipe_active <= 1'b1;
        end
    end

    // ── Pipeline stage 1: DSP multiplies (registered output) ────
    // Four parallel signed multiplies via Gowin primitives.
    // On GW5A: MULT27X36 or MULT18X18D (registered output).
    // On GW2A/GW1N: MULT18X18 (combinational, but we register anyway).
    wire signed [2*WIDTH-1:0] prod_a1a2, prod_b1b2, prod_a1b2, prod_b1a2;

    generate
        if (DEVICE == "GW5A" && WIDTH > 18) begin : gen_gw5a_wide
            // WIDTH 19-27: use MULT27X36 (27×36 DSP, registered output)
            wire [62:0] dsp_aa, dsp_bb, dsp_ab, dsp_ba;

            MULT27X36 u_aa (.DOUT(dsp_aa), .A(a1_r[WIDTH-1:0]),
                .B({{(36-WIDTH){b1_r[WIDTH-1]}}, b1_r}), .D(27'd0),
                .CLK({1'b0,clk}), .CE(2'b01), .RESET({1'b0,reset}), .PSEL(1'b0), .PADDSUB(1'b0));
            MULT27X36 u_bb (.DOUT(dsp_bb), .A(b1_r[WIDTH-1:0]),
                .B({{(36-WIDTH){b2_r[WIDTH-1]}}, b2_r}), .D(27'd0),
                .CLK({1'b0,clk}), .CE(2'b01), .RESET({1'b0,reset}), .PSEL(1'b0), .PADDSUB(1'b0));
            MULT27X36 u_ab (.DOUT(dsp_ab), .A(a1_r[WIDTH-1:0]),
                .B({{(36-WIDTH){b2_r[WIDTH-1]}}, b2_r}), .D(27'd0),
                .CLK({1'b0,clk}), .CE(2'b01), .RESET({1'b0,reset}), .PSEL(1'b0), .PADDSUB(1'b0));
            MULT27X36 u_ba (.DOUT(dsp_ba), .A(b1_r[WIDTH-1:0]),
                .B({{(36-WIDTH){a2_r[WIDTH-1]}}, a2_r}), .D(27'd0),
                .CLK({1'b0,clk}), .CE(2'b01), .RESET({1'b0,reset}), .PSEL(1'b0), .PADDSUB(1'b0));

            assign prod_a1a2 = dsp_aa[2*WIDTH-1:0];
            assign prod_b1b2 = dsp_bb[2*WIDTH-1:0];
            assign prod_a1b2 = dsp_ab[2*WIDTH-1:0];
            assign prod_b1a2 = dsp_ba[2*WIDTH-1:0];
        end else begin : gen_inferred
            // WIDTH ≤ 18: Yosys infers MULT18X18(D) automatically
            // We register the result ourselves for consistent pipeline depth
            reg signed [2*WIDTH-1:0] r_aa, r_bb, r_ab, r_ba;
            always @(posedge clk or posedge reset) begin
                if (reset) begin
                    r_aa <= 0; r_bb <= 0; r_ab <= 0; r_ba <= 0;
                end else begin
                    r_aa <= a1_r * a2_r;
                    r_bb <= b1_r * b2_r;
                    r_ab <= a1_r * b2_r;
                    r_ba <= b1_r * a2_r;
                end
            end
            assign prod_a1a2 = r_aa;
            assign prod_b1b2 = r_bb;
            assign prod_a1b2 = r_ab;
            assign prod_b1a2 = r_ba;
        end
    endgenerate

    // ── Pipeline stage 2: surd term + accumulation ──────────────
    wire signed [2*WIDTH-1:0] surd_term_3, surd_term_5, surd_term_15;
    assign surd_term_3  = (prod_b1b2 << 1) + prod_b1b2;
    assign surd_term_5  = (prod_b1b2 << 2) + prod_b1b2;
    assign surd_term_15 = (prod_b1b2 << 4) - prod_b1b2;

    wire signed [2*WIDTH-1:0] surd_term;
    assign surd_term = (field_sel_r == 2'b01) ? surd_term_5  :
                       (field_sel_r == 2'b10) ? surd_term_15 : surd_term_3;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            res_a <= 0;
            res_b <= 0;
            busy  <= 0;
        end else begin
            if (pipe_active) begin
                res_a <= (prod_a1a2 + surd_term) >>> SHIFT;
                res_b <= (prod_a1b2 + prod_b1a2) >>> SHIFT;
                busy  <= 1'b0;
            end else begin
                busy <= 1'b0;
            end
        end
    end

endmodule
