// SPU-13 Rotary Logic Primitive (v3.0.29)
// Basis: Isotropic Vector Matrix (IVM)
// Function: Coordinate-Invariant Geometric Switching (Vortex Valve)

module spu13_rotary_gate (
    input  wire [63:0] a, b, c, d,    // Quadray Vector Inputs (SF32.16)
    input  wire [1:0]  spin_dir,     // Phase Shift / Scale Command
    output reg  [63:0] out_a, out_b, out_c, out_d
);

    // 1. The 'Jitterbug' Transformation Logic
    // Logic states are determined by Vector Permutation rather than Boolean gating.
    // This eliminates the 'Hysteresis Tax' of standard switching.

    always @(*) begin
        case (spin_dir)
            2'b00: begin // State 0: Identity (Static Rest)
                {out_a, out_b, out_c, out_d} = {a, b, c, d};
            end
            
            2'b01: begin // State 1: 60-Degree CW Rotation (Flow)
                // Permute coordinates following Tetrahedral Symmetry
                {out_a, out_b, out_c, out_d} = {b, c, a, d}; 
            end
            
            2'b10: begin // State 2: Dielectric Pulse (Growth)
                // Scaling via the Golden Ratio (Phi-Rotor)
                // Implemented as Rational Surd multiplication in the full ALU
                out_a = (a * 106039) >>> 16; // 1.618033 fixed-point approx
                out_b = (b * 106039) >>> 16;
                out_c = (c * 106039) >>> 16;
                out_d = (d * 106039) >>> 16;
            end
            
            2'b11: begin // State 3: Reciprocal Flip (Reciprocity)
                {out_a, out_b, out_c, out_d} = {d, c, b, a};
            end
        endcase
    end

endmodule
