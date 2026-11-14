// psurd_sign.v — STST sign of a + b*sqrt(3) (frozen contract §6), d > 0 so d is ignored.
// Combinational, dedicated squarers (RTL-0A decision D1). Same-sign fast path; otherwise compare
// |a|^2 with 3|b|^2 as unsigned 130-bit values (both < 2^128; -2^63 handled via 64-bit magnitudes).
module psurd_sign (
    input  wire [191:0] t,
    output wire zero, neg, pos
);
    wire [63:0] a = t[63:0], b = t[127:64];
    wire an = a[63], bn = b[63];
    wire az = a == 64'd0, bz = b == 64'd0;
    wire [63:0] am = an ? (~a + 64'd1) : a;          // |a|; -2^63 -> 2^63 (fits unsigned 64)
    wire [63:0] bm = bn ? (~b + 64'd1) : b;
    wire [127:0] aa = am * am;
    wire [127:0] bb = bm * bm;
    wire [129:0] bb3 = {2'b00, bb} + {1'b0, bb, 1'b0};  // 3*b^2 < 2^128
    wire a_wins = {2'b00, aa} > bb3;                  // never equal for nonzero integers (sqrt3 irrational)
    wire same = az || bz || (an == bn);
    wire neg_same = az ? bn : an;                     // same-sign / one-zero case
    assign zero = az && bz;
    assign neg = !zero && (same ? neg_same : (a_wins ? an : bn));
    assign pos = !zero && !neg;
endmodule
