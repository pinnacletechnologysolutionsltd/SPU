// SPU-13 Spread Multiplier (v1.0)
// Rational spread shading — no division, no floating point.
//
// Given two Quadray vectors (surface normal N and light direction L),
// computes the spread s = sin²θ as an exact rational pair (numer, denom).
//
// Formula (avoids the /2 in Quadray quadrance by working in 4× form):
//   SN       = Na²+Nb²+Nc²+Nd²   (unnormalized quadrance × 2)
//   SL       = La²+Lb²+Lc²+Ld²
//   dot      = Na·La+Nb·Lb+Nc·Lc+Nd·Ld
//   numer    = SN·SL − 4·dot²     (= 4·Q(N)·Q(L)·spread)
//   denom    = SN·SL               (= 4·Q(N)·Q(L))
//
// Caller multiplies numer/denom by intensity to get luminance (still rational).
// Pixel inside perpendicular beam:  numer == denom  (s=1)
// Pixel in shadow (parallel beam):  numer == 0      (s=0)
//
// Practical range: coordinates signed 16-bit, products 64-bit.
// At unit-normal scale (max coord ~362 for r^5 Pell step) numer/denom
// fit comfortably in 64-bit.  Document overflow: if raw coordinates ever
// reach 16-bit maximum (32767) the 4·dot² term hits ~1.84e19 which overflows
// int64 — keep Quadray coords normalised (Pell step ≤ 7).

module spu_spread_mul (
    input  wire signed [15:0] n_a, n_b, n_c, n_d,  // surface normal (Quadray)
    input  wire signed [15:0] l_a, l_b, l_c, l_d,  // light direction (Quadray)
    output wire        [63:0] spread_numer,          // rational numerator
    output wire        [63:0] spread_denom           // rational denominator (= SN·SL)
);

    // --- dot product (signed, fits 34-bit; use 64 for safety) ---
    wire signed [63:0] dot = $signed({{48{n_a[15]}}, n_a}) * $signed({{48{l_a[15]}}, l_a})
                           + $signed({{48{n_b[15]}}, n_b}) * $signed({{48{l_b[15]}}, l_b})
                           + $signed({{48{n_c[15]}}, n_c}) * $signed({{48{l_c[15]}}, l_c})
                           + $signed({{48{n_d[15]}}, n_d}) * $signed({{48{l_d[15]}}, l_d});

    // --- unnormalized quadrance sums (unsigned, 34-bit; use 64) ---
    wire [63:0] SN = ({{32{1'b0}}, n_a * n_a}
                    + {32'b0, n_b * n_b}
                    + {32'b0, n_c * n_c}
                    + {32'b0, n_d * n_d});

    wire [63:0] SL = ({32'b0, l_a * l_a}
                    + {32'b0, l_b * l_b}
                    + {32'b0, l_c * l_c}
                    + {32'b0, l_d * l_d});

    wire [63:0] SN_SL  = SN * SL;          // spread denominator (4·Q(N)·Q(L))
    wire [63:0] dot_sq = dot * dot;         // dot²

    assign spread_denom = SN_SL;
    // numer = SN·SL − 4·dot²   (clamped to zero — rounding can produce −1 ULP)
    assign spread_numer = (SN_SL >= (dot_sq << 2)) ? (SN_SL - (dot_sq << 2)) : 64'b0;

endmodule
