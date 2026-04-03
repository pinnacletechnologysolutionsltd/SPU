// SPU-13 SQR Rotor (v1.1 Chiral Edition)
// Target: Unified SPU-13 Fleet
// Objective: Algebraic Isotropic Rotation in 4D Quadray Space.
// Logic: 60-degree chiral permutation around the D-axis.
// Result: Bit-perfect return to identity after 6 cycles.

module spu_sqr_rotor (
    input  wire         clk,
    input  wire         reset,
    input  wire [63:0]  q_in_a, q_in_b, q_in_c, q_in_d,
    input  wire [15:0]  t_param,   // Rational spread (Unused in pure permutation mode)
    output reg  [63:0]  q_out_a, q_out_b, q_out_c, q_out_d
);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            q_out_a <= 64'h0; q_out_b <= 64'h0;
            q_out_c <= 64'h0; q_out_d <= 64'h0;
        end else begin
            // 60-degree Chiral Shift (Around D-axis Apex)
            // This is the fundamental 'Jitterbug' step of the IVM.
            q_out_a <= q_in_c;
            q_out_b <= q_in_a;
            q_out_c <= q_in_b;
            q_out_d <= q_in_d; // Axial Anchor
        end
    end

endmodule
