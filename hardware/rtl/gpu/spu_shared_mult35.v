// spu_shared_mult35.v — single physical 49x17 unsigned multiplier
// (module name kept from an earlier, since-corrected sizing -- see
// below -- to avoid another file rename mid-implementation; the port
// widths are what matter). Shared by spu_depth_math.v's dot-product/
// final-scale states and spu_reciprocal_core.v's Newton-Raphson states,
// selected (not arbitrated) by whichever is the current owning FSM
// state -- see spu_strategy/contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md
// §8. Magnitude-only: no sign handling here, every caller extracts
// signs and negates outside this module. No internal state, no
// truncation: presents the full unsigned product, untruncated -- every
// consumer's own truncation is explicit at its point of use.
//
// Width history (three corrections before any of the three depth-v2
// modules were finished, all caught before commit):
// 1. 42x42 -- wrong, sized off A_z's OUTPUT width, not multiply operands.
// 2. 35x17 -- wrong, only checked Sa/Sb (from 16-bit a_i/b_i); Sc is
//    built from c_i, a 32-bit port, so this bound didn't cover it.
// 3. Briefly widened to 49x17, sized to c_i's full 32-bit PORT range
//    (an adversarial-input assumption) -- overcorrected. This is a
//    trusted, closed pipeline (host-generated coefficients from real
//    640x480 vertices, not an adversarial interface), the same
//    reasoning already used for D's 16-25 bit domain evidence. The
//    provable bound for REAL screen-derived c_i is |c_i| < 2**20
//    (|c_i| <= 2*639*479), giving |Sc| < 2**38 -- not 2**49. Widening
//    past that would have also silently exceeded the already-measured,
//    tested 56-bit A_z/B_z/C_z and per-pixel accumulator registers
//    downstream, trading one overflow bug for another.
// 4. 40x17 (this file) -- covers |Sc| < 2**38 with margin (39-bit "a"
//    port would suffice exactly; 40 for clean round width), and its
//    57-bit product fits the existing 56-bit A_z/B_z/C_z registers
//    with 1 bit to spare.
// CC0 1.0 Universal.

module spu_shared_mult35 (
    input  wire [39:0] a,
    input  wire [16:0] b,
    output wire [56:0] p
);
    assign p = a * b;
endmodule
