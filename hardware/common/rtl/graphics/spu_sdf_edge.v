// SPU-13 SDF Edge Renderer (v1.0)
// Implements Metal drawEdge() as fixed-point pipelined RTL.
//
// This module is the critical anti-sinusoidal-winding fix for rendering
// IVM wireframe geometry on 90-degree Cartesian displays.
//
// WHY THIS IS NEEDED:
//   When projecting 4D Quadray vectors onto a 2D Cartesian screen, each axis
//   component has a different projected frequency.  Stepping per-axis (as a
//   naive DDA would do) creates Lissajous-like interference — a winding
//   sinusoidal pattern in place of a straight edge.
//
//   The fix is the parametric closest-point projection from Metal drawEdge():
//
//     pa = pixel - a                       // vector from edge start to pixel
//     ba = b - a                           // edge direction vector
//     h  = clamp(dot(pa,ba)/dot(ba,ba), 0, 1)  // parametric t on segment
//     d  = length(pa - ba*h)               // perpendicular distance
//     intensity = smoothstep(threshold, 0, d)
//
//   This collapses all 4 Quadray frequency components into a single scalar t,
//   rendering the line as one continuous parametric curve regardless of the
//   per-component step rates.  No winding, no knots.
//
// PIPELINE (3 stages, fully registered):
//   Stage 1 (cycle 0): Compute dot(pa,ba) and dot(ba,ba)
//   Stage 2 (cycle 1): Normalise h via reciprocal LUT; compute closest point
//   Stage 3 (cycle 2): Distance squared; smoothstep intensity output
//
// Fixed-point format: Q8 (1.0 = 256 counts; screen coords in Q8)
// Tension: adds 'vibration' per Metal drawEdge — positive values add organic
//          manifold shimmer proportional to edge stress.  Use 0 for clean lines.
//
// Coordinate convention matches spu_hal_cartesian.v and DQFA.metal toIVM():
//   x = (b - c) * scale
//   y = a - (b + c)/2 * scale
//   where a,b,c are Quadray components projected to Q8 screen space.

`include "spu_rational_lut.v"

module spu_sdf_edge #(
    parameter Q      = 8,           // fixed-point fractional bits
    parameter THRESH = 8'd20        // default line half-width (Q8 units, ~0.08)
)(
    input  wire        clk,
    input  wire        reset,
    input  wire        enable,      // accept new pixel on this cycle

    // Edge endpoints in Q8 screen coordinates
    input  wire signed [15:0] ax, ay,   // edge start
    input  wire signed [15:0] bx, by,   // edge end

    // Current pixel to test
    input  wire signed [15:0] px, py,

    // Tension: manifold stress factor (0 = clean, higher = shimmer)
    // Matches Metal: float2 vibration = float2(sin(uv.y*50 + tension)*0.002, 0)
    // Hardware: integer vibration_x = (tension * sin_lut[py[5:0]]) >> 8
    input  wire        [7:0]  tension,

    // Output
    output reg         [7:0]  intensity,  // 0=miss, 255=centre of edge
    output reg                valid       // intensity is ready (2 cycles after enable)
);

    // -----------------------------------------------------------------------
    // Stage 1 — dot products (registered)
    // -----------------------------------------------------------------------
    // pa = pixel - a
    wire signed [15:0] pa_x = px - ax;
    wire signed [15:0] pa_y = py - ay;
    // ba = b - a
    wire signed [15:0] ba_x = bx - ax;
    wire signed [15:0] ba_y = by - ay;

    // dot(pa, ba) — signed, can be negative (pixel behind start point)
    wire signed [31:0] dot_pa_ba = $signed(pa_x) * $signed(ba_x) +
                                   $signed(pa_y) * $signed(ba_y);

    // dot(ba, ba) — always non-negative (squared edge length)
    wire [31:0] len_sq    = $signed(ba_x) * $signed(ba_x) +
                            $signed(ba_y) * $signed(ba_y);

    // Vibration offset (tension shimmer, Q8)
    // Uses top 6 bits of py as LUT phase, matches Metal sin(uv.y * 50 + tension)
    // Approximated as: vib = tension * (py[6:1] - 32) >> 6  (triangle wave)
    wire signed [7:0]  py_phase   = $signed(py[6:1]) - 8'sd32; // −32..+31
    wire signed [15:0] vibration  = ($signed({8'd0, tension}) * $signed(py_phase)) >>> 6;

    // Registered stage 1 outputs
    reg signed [31:0] s1_dot_pa_ba;
    reg        [31:0] s1_len_sq;
    reg signed [15:0] s1_pa_x, s1_pa_y;
    reg signed [15:0] s1_ba_x, s1_ba_y;
    reg signed [15:0] s1_vib;
    reg               s1_valid;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            s1_valid <= 0;
        end else begin
            s1_valid     <= enable;
            s1_dot_pa_ba <= dot_pa_ba;
            s1_len_sq    <= len_sq;
            s1_pa_x      <= pa_x;
            s1_pa_y      <= pa_y;
            s1_ba_x      <= ba_x;
            s1_ba_y      <= ba_y;
            s1_vib       <= vibration;
        end
    end

    // -----------------------------------------------------------------------
    // Stage 2 — normalise h, compute closest point (registered)
    // -----------------------------------------------------------------------
    // h = clamp(dot_pa_ba / len_sq, 0, 1)  in Q8
    // Strategy: use leading-zero normalisation + reciprocal LUT (same as
    // spu_rasterizer.v's barycentric normalisation).
    //
    // 1. Extract 8-bit mantissa of len_sq for LUT lookup
    // 2. Shift dot_pa_ba by the same amount to match scale
    // 3. h_q8 = (dot_pa_ba_shifted * reciprocal) >> 23  (LUT is 1.23 format)
    // 4. Clamp h_q8 to [0, 256] (Q8 representation of [0.0, 1.0])

    wire [7:0]  s1_mantissa = s1_len_sq[31:24]; // MSB-aligned 8-bit mantissa
    wire [23:0] s1_recip;
    spu_rational_lut edge_recip_lut (
        .addr(s1_mantissa),
        .reciprocal(s1_recip)
    );

    // Shift dot_pa_ba to match the mantissa normalisation (top 8 bits of len_sq)
    // We need: h_raw = dot_pa_ba * (2^24 / len_sq)  → use recip as 1/mantissa
    // Scale dot by matching shift: shift = count leading zeros of len_sq to bit 31
    // Simplified: use top byte of len_sq as divisor proxy
    wire signed [47:0] h_raw = $signed(s1_dot_pa_ba) * $signed({1'b0, s1_recip});
    // h_raw is in Q(8+23) = Q31; to get Q8: take bits [38:31] (Q31 >> 23)
    wire signed [15:0] h_q8_raw = h_raw[38:23];  // Q8 parametric t

    // Clamp to [0, 256] — endpoints of segment
    wire [8:0] h_q8_clamped = (h_q8_raw < 0)      ? 9'd0   :
                               (h_q8_raw > 9'd256)  ? 9'd256 :
                               h_q8_raw[8:0];

    // Closest point on segment: cp = a + ba * h / 256  (Q8 divide by scale)
    wire signed [23:0] cp_x_full = $signed({s1_ba_x, 8'd0}) *
                                   $signed({1'b0, h_q8_clamped});
    wire signed [23:0] cp_y_full = $signed({s1_ba_y, 8'd0}) *
                                   $signed({1'b0, h_q8_clamped});
    // cp_x = ax + (ba_x * h) >> Q  — but ax is in stage-1 latch; use pa offset:
    // distance vector: dv = pa - ba * h/256
    wire signed [15:0] dv_x = s1_pa_x - cp_x_full[23:8] + s1_vib;
    wire signed [15:0] dv_y = s1_pa_y - cp_y_full[23:8];

    // Distance squared (Q16 — dv is Q8, so dv*dv is Q16)
    wire [31:0] dist_sq = dv_x * dv_x + dv_y * dv_y;

    // Registered stage 2 outputs
    reg [31:0] s2_dist_sq;
    reg        s2_valid;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            s2_valid <= 0;
        end else begin
            s2_valid   <= s1_valid;
            s2_dist_sq <= dist_sq;
        end
    end

    // -----------------------------------------------------------------------
    // Stage 3 — smoothstep intensity (registered output)
    // -----------------------------------------------------------------------
    // Metal: smoothstep(0.01 + tension*0.01, 0.005, d)
    //   → edge at d=0.005, fade to zero at d=0.01
    //   → In Q8: threshold ≈ THRESH (default 20 = 0.078 in Q8)
    //   → inner edge: THRESH/2
    //
    // Quadratic smoothstep: intensity = 255 * clamp(1 - (d/T)^2, 0, 1)
    //   where d = sqrt(dist_sq) and T = THRESH
    //   Avoid sqrt: compare dist_sq to THRESH^2
    //
    // thresh_sq = THRESH * THRESH (in Q16 since dist_sq is Q16)
    localparam [15:0] THRESH_SQ = THRESH * THRESH;

    // Scale dist_sq down: dist_sq is Q16, THRESH is Q8 → THRESH_SQ is Q16
    wire [15:0] ds_q16 = s2_dist_sq[15:0]; // lower 16 bits capture Q8*Q8

    wire        inside = (ds_q16 < THRESH_SQ);

    // Quadratic falloff:  255 * (THRESH_SQ - ds) / THRESH_SQ
    // = (255 * (THRESH_SQ - ds)) >> log2(THRESH_SQ)
    // Use 8-bit approximation: ratio = (THRESH_SQ - ds)[15:8]
    wire [15:0] remain  = inside ? (THRESH_SQ - ds_q16) : 16'd0;
    // Divide by THRESH_SQ via reciprocal: result in 0..255
    wire [7:0]  smooth  = (remain * 8'd255) >> $clog2(THRESH_SQ > 0 ? THRESH_SQ : 1);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            intensity <= 0;
            valid     <= 0;
        end else begin
            valid     <= s2_valid;
            intensity <= inside ? smooth : 8'd0;
        end
    end

endmodule
