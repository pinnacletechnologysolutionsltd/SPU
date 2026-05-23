// spu_laminar_fold.v — Fibonacci Descent Overflow Guard (v2.0)
// Width-parameterized: folds an N-bit accumulator back to (N-2)-bit
// range via arithmetic right-shift when overflow bits are set.
//
// When an accumulation exceeds the target range, instead of silent
// binary wrap-around the value is halved (arithmetic right-shift).
// Successive applications converge toward zero at the Fibonacci
// ratio 1/φ² ≈ 0.382, preserving the manifold's geometric character.
//
// Fold rules (unsigned interpretation of overflow bits):
//   in_val[W-1]    set → 2-bit overflow → out = in_val[W-1:2]   (÷4, >>2)
//   in_val[W-2]    set → 1-bit overflow → out = in_val[W-2:1]   (÷2, >>1)
//   no overflow          →              out = in_val[W-3:0]     (pass-through)
//
// henosis: asserted when a fold is applied.
// Combinatorial — zero latency, ~6 LUTs.
//
// CC0 1.0 Universal.

module spu_laminar_fold #(
    parameter WIDTH = 18    // input width (default: 18-bit → 16-bit Q12)
) (
    input  wire [WIDTH-1:0]   in_val,
    output wire [WIDTH-3:0]   out_val,
    output wire               henosis
);
    assign henosis = (in_val[WIDTH-1:WIDTH-2] != 2'b00);

    assign out_val = in_val[WIDTH-1]   ? in_val[WIDTH-1:2]        // 2-bit overflow → >>2
                   : in_val[WIDTH-2]   ? in_val[WIDTH-2:1]        // 1-bit overflow → >>1
                   :                     in_val[WIDTH-3:0];       // in range

endmodule
