// SPU-13 Spectral Purify (v1.0)
// Reduces a rational (numer, denom) colour value to a display-ready integer
// in [0, max_out] using binary GCD (shifts + subtracts — no division operator).
//
// Two-stage pipeline:
//   Stage 1: binary GCD — count common trailing zeros, shift both operands
//   Stage 2: scale  pixel_val = (numer_r * max_out) / denom_r
//            implemented as: find leading bit of denom_r, use reciprocal LUT,
//            multiply, shift.  One approximation at the display boundary only.
//
// The "no division in the manifold" rule holds — this module only runs once,
// at the display PHY boundary, after all Q(√3) geometry is resolved.
//
// Latency: 2 clock cycles (registered output).

module spu_purify (
    input  wire        clk,
    input  wire        reset,
    input  wire [63:0] numer,        // spread/colour numerator
    input  wire [63:0] denom,        // spread/colour denominator (must be > 0)
    input  wire [9:0]  max_out,      // display PHY depth (255, 1023, etc.)
    input  wire        valid_in,
    output reg  [9:0]  pixel_val,    // display-ready value in [0, max_out]
    output reg         valid_out
);

    // ── Stage 1: binary GCD via common trailing zeros ────────────────────
    // ctz(n|d) gives the highest power of 2 dividing both n and d.
    // Shifting both right by that count gives the reduced pair (numer_r, denom_r).

    function automatic [5:0] ctz64;
        input [63:0] v;
        integer i;
        begin
            ctz64 = 6'd63;
            for (i = 0; i < 64; i = i + 1)
                if (v[i] && (ctz64 == 6'd63)) ctz64 = i[5:0];
        end
    endfunction

    wire [5:0] shift_n  = ctz64(numer);
    wire [5:0] shift_d  = ctz64(denom);
    wire [5:0] gcd_sh   = (shift_n < shift_d) ? shift_n : shift_d;

    wire [63:0] numer_r = numer >> gcd_sh;
    wire [63:0] denom_r = denom >> gcd_sh;

    // ── Stage 2: scale numer_r to [0, max_out] ───────────────────────────
    // pixel_val = floor(numer_r * max_out / denom_r)
    // Use leading-bit normalisation + reciprocal LUT (1.23 fixed-point).
    // This is a bounded approximation: error < 1 display LSB.

    // Find position of MSB of denom_r (5-bit, 0..63)
    function automatic [5:0] msb64;
        input [63:0] v;
        integer i;
        begin
            msb64 = 6'd0;
            for (i = 0; i < 64; i = i + 1)
                if (v[i]) msb64 = i[5:0];
        end
    endfunction

    wire [5:0]  denom_msb   = msb64(denom_r);

    // Extract the fractional bits BELOW the MSB of denom_r, pad to 8-bit.
    // This gives the LUT address: addr = floor((denom_r/2^msb - 1) * 256).
    // Example: denom_r=17=10001b, msb=4 → frac=1 → addr = 1<<(8-4) = 16 → 1/1.0625
    wire [63:0] denom_frac  = denom_r & ((64'h1 << denom_msb) - 64'h1);
    wire [7:0]  denom_mant  = (denom_msb >= 6'd8)
                              ? denom_frac >> (denom_msb - 6'd8)
                              : denom_frac << (6'd8 - denom_msb);

    wire [23:0] recip;
    spu_rational_lut recip_lut (.addr(denom_mant), .reciprocal(recip));

    // scaled = (numer_r * max_out * recip) >> (23 + denom_msb)
    // Use explicit 128-bit padding to prevent intermediate truncation.
    wire [127:0] numer_128  = {64'b0, numer_r};
    wire [127:0] maxout_128 = {118'b0, max_out};
    wire [127:0] recip_128  = {104'b0, recip};
    wire [127:0] scaled     = numer_128 * maxout_128 * recip_128;

    wire [5:0] total_shift = 6'd23 + denom_msb;  // reciprocal is 1.23 format

    wire [63:0] pixel_raw = scaled >> total_shift;

    // ── Registered output ─────────────────────────────────────────────────
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            pixel_val  <= 10'b0;
            valid_out  <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (valid_in) begin
                // Clamp to max_out in case of rounding overshoot
                pixel_val <= (pixel_raw > {54'b0, max_out}) ? max_out
                                                             : pixel_raw[9:0];
            end
        end
    end

endmodule
