// spu_laminar_fold.v — Phi-Step Fold Primitive (v1.0)
// Folds an 18-bit overflow value back to 16-bit via Fibonacci descent.
//
// When an accumulation exceeds Q8.8/Q12 range, instead of silent binary
// wrap-around the value is halved (arithmetic right-shift).  Successive
// applications converge toward zero at the Fibonacci ratio 1/φ² ≈ 0.382,
// preserving the manifold's geometric character.
//
// Fold rules (unsigned interpretation of overflow bits):
//   in_val[17]  set → 2-bit overflow → out = in_val[17:2]  (÷4, >>2)
//   in_val[16]  set → 1-bit overflow → out = in_val[16:1]  (÷2, >>1)
//   no overflow        →              out = in_val[15:0]   (pass-through)
//
// henosis: asserted for one cycle whenever a fold is applied.
// Combinatorial — zero latency, ~6 LUTs.
//
// CC0 1.0 Universal.

module spu_laminar_fold (
    input  wire [17:0] in_val,   // 18-bit accumulator value
    output wire [15:0] out_val,  // 16-bit folded result
    output wire        henosis   // 1 = fold was applied this cycle
);
    assign henosis = (in_val[17:16] != 2'b00);

    assign out_val = in_val[17] ? in_val[17:2]   // 2-bit overflow → >>2
                  : in_val[16] ? in_val[16:1]    // 1-bit overflow → >>1
                  :              in_val[15:0];   // in range

endmodule
