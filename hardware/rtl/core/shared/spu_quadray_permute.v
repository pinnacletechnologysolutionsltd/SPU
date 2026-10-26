// spu_quadray_permute.v — Quadray Coordinate Permuter (v1.0)
// Rewires the 4 components (A,B,C,D) of a Quadray vector to change
// the invariant axis for the ROTC circulant.
//
// The ROTC circulant always keeps A invariant and rotates B,C,D.
// To rotate around B: permute so B→A, apply ROTC, permute back.
// To rotate around C: permute so C→A, apply ROTC, permute back.
// To rotate around D: no permute needed (D is already the invariant
//   when A is the circulant's invariant axis — D-up convention).
//
// Permutation select (perm_sel):
//   2'b00: identity   (A,B,C,D)
//   2'b01: B→A       (B,C,D,A)
//   2'b10: C→A       (C,D,A,B)
//   2'b11: D→A       (D,A,B,C)
//
// Combinational — zero latency, ~16 LUTs (4×64-bit muxes).
// CC0 1.0 Universal.

module spu_quadray_permute (
    input  wire [1:0]   perm_sel,       // 0=id, 1=B→A, 2=C→A, 3=D→A
    input  wire [63:0]  A_in, B_in, C_in, D_in,
    output wire [63:0]  A_out, B_out, C_out, D_out
);

    // Forward permutation: move selected axis to A position
    assign A_out = (perm_sel == 2'b00) ? A_in :
                   (perm_sel == 2'b01) ? B_in :
                   (perm_sel == 2'b10) ? C_in : D_in;

    assign B_out = (perm_sel == 2'b00) ? B_in :
                   (perm_sel == 2'b01) ? C_in :
                   (perm_sel == 2'b10) ? D_in : A_in;

    assign C_out = (perm_sel == 2'b00) ? C_in :
                   (perm_sel == 2'b01) ? D_in :
                   (perm_sel == 2'b10) ? A_in : B_in;

    assign D_out = (perm_sel == 2'b00) ? D_in :
                   (perm_sel == 2'b01) ? A_in :
                   (perm_sel == 2'b10) ? B_in : C_in;

endmodule
