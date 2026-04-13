// spu_janus_mirror.v — Q(√3) Conjugate + Janus Snap (v2.0)
// CC0 1.0 Universal.
`timescale 1ns/1ps
//
// For a surd s = (P + Q·√3) in Q(√3):
//   Object    : s  = P + Q·√3
//   Shadow    : s* = P - Q·√3   (algebraic conjugate — negates the surd part)
//   Quadrance : K  = P² - 3·Q²  (the rational "norm" of the surd)
//
// Janus Snap: K > 0 means the surd is "laminar" — living in the positive
// rational cone.  K == 0 is a zero-vector (null / cubic leak).
// K < 0 is a "shadow-dominant" / inverted polarity state.
//
// Inputs are Q8.8 fixed-point (8-bit integer, 8-bit fraction) packed as
// {P[15:0], Q[15:0]}.  Quadrance K = P²−3Q² is computed in full 32-bit
// precision before the sign check, keeping the module bit-exact.
//
// Latency: 2 clock cycles (mul stage 1 → accumulate stage 2 → outputs).
//
// Depends on: nothing (standalone primitive)
// CC0 1.0 Universal.

module spu_janus_mirror #(
    parameter WIDTH = 16   // P/Q component width (matches spu_surd_mul_gowin)
)(
    input  wire                    clk,
    input  wire                    rst_n,

    // Packed surd input: {P[WIDTH-1:0], Q[WIDTH-1:0]}
    input  wire [WIDTH*2-1:0]      surd_in,

    // Shadow: algebraic conjugate packed as {P, -Q}
    output reg  [WIDTH*2-1:0]      shadow_out,

    // Quadrance K = P² − 3Q² (signed, full 2×WIDTH bits)
    output reg  signed [WIDTH*2-1:0] quadrance_out,

    // Snap flags (valid 2 cycles after surd_in changes)
    output reg                     snap_laminar,  // K > 0  — positive rational cone
    output reg                     snap_null,     // K == 0 — zero / cubic leak
    output reg                     snap_shadow    // K < 0  — inverted / shadow polarity
);

    wire signed [WIDTH-1:0] P_in;
    assign P_in = $signed(surd_in[WIDTH-1:0]);
    wire signed [WIDTH-1:0] Q_in;
    assign Q_in = $signed(surd_in[WIDTH*2-1:WIDTH]);

    // ── Stage 1: multiply ─────────────────────────────────────────────────
    reg signed [WIDTH*2-1:0] P_sq;    // P²
    reg signed [WIDTH*2-1:0] Q_sq3;   // 3·Q²
    reg signed [WIDTH-1:0]   P_s1;    // latch P for stage-2 shadow
    reg signed [WIDTH-1:0]   Q_s1;    // latch Q for stage-2 shadow

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            P_sq  <= 0;
            Q_sq3 <= 0;
            P_s1  <= 0;
            Q_s1  <= 0;
        end else begin
            P_sq  <= P_in * P_in;
            Q_sq3 <= (Q_in * Q_in) + (Q_in * Q_in) + (Q_in * Q_in); // 3·Q² via add
            P_s1  <= P_in;
            Q_s1  <= Q_in;
        end
    end

    // ── Stage 2: subtract + classify ──────────────────────────────────────
    wire signed [WIDTH*2-1:0] K_wire;
    assign K_wire = P_sq - Q_sq3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            quadrance_out <= 0;
            shadow_out    <= 0;
            snap_laminar  <= 1'b0;
            snap_null     <= 1'b0;
            snap_shadow   <= 1'b0;
        end else begin
            quadrance_out <= K_wire;

            // Shadow = algebraic conjugate: negate the surd (√3) component
            shadow_out <= {-Q_s1, P_s1};

            snap_laminar <= (K_wire  > 0);
            snap_null    <= (K_wire == 0);
            snap_shadow  <= (K_wire  < 0);
        end
    end

endmodule
