// spu_ve_init.v — Vector Equilibrium Ground State Loader (v1.0)
// CC0 1.0 Universal.
//
// Emits the manifold's initial VE (cuboctahedral) state on the cycle
// that boot_done asserts, then holds it until rst_n deasserts.
//
// The Vector Equilibrium (Fuller 12-around-1 / cuboctahedron) maps onto
// the 13-axis SPU-13 manifold as:
//   Axis 12 (centre): A = +1 Q12, B = 0   — rational unity seed
//   Axes  0..5      : A = +1 Q12, B = 0   — 6 positive VE vertices
//   Axes  6..11     : A = -1 Q12, B = 0   — 6 negative VE vertices
//
// This gives:
//   - Σ(outer 12 axes A) = 6×(+1) + 6×(−1) = 0  → tensegrity equilibrium
//   - Every axis: K = A²−3B² = 1 > 0             → snap_laminar throughout
//   - No cubic leak at first Phi pulse (Davis Gate will not fire)
//
// Axis format: {A[31:0], B[31:0]}  — matches spu13_core manifold_reg layout.
// A and B are Q12 signed 32-bit (integer 1 → 0x00001000).
//
// Outputs:
//   ve_state[831:0] — the VE initial manifold; hold it into int_mem on boot_done.
//   ve_valid        — combinatorial, mirrors boot_done (registered at destination).
//
// Latency: 0 (combinatorial output).
// Depends on: nothing.

`timescale 1ns/1ps

module spu_ve_init (
    input  wire         boot_done,     // from spu_laminar_boot / spu_ghost_boot
    output wire [831:0] ve_state,      // 13 × 64-bit VE manifold
    output wire         ve_valid       // asserts when ve_state is valid
);

    // Q12 representations of +1 and -1 (signed 32-bit)
    localparam [31:0] POS_UNITY = 32'h0000_1000;   // +1.0 in Q12
    localparam [31:0] NEG_UNITY = 32'hFFFF_F000;   // -1.0 in Q12 (two's complement)
    localparam [31:0] ZERO      = 32'h0000_0000;

    // Each axis = {A[31:0], B[31:0]}
    // Axes 0-5:  positive VE vertices  {A=+1, B=0}
    // Axes 6-11: negative VE vertices  {A=-1, B=0}
    // Axis 12:   centre seed           {A=+1, B=0}
    function [63:0] ve_axis;
        input [3:0] idx;
        begin
            if (idx <= 4'd5)       ve_axis = {POS_UNITY, ZERO};  // +ve vertex
            else if (idx <= 4'd11) ve_axis = {NEG_UNITY, ZERO};  // -ve vertex
            else                   ve_axis = {POS_UNITY, ZERO};  // centre
        end
    endfunction

    assign ve_state[  63:  0] = ve_axis(4'd0);
    assign ve_state[ 127: 64] = ve_axis(4'd1);
    assign ve_state[ 191:128] = ve_axis(4'd2);
    assign ve_state[ 255:192] = ve_axis(4'd3);
    assign ve_state[ 319:256] = ve_axis(4'd4);
    assign ve_state[ 383:320] = ve_axis(4'd5);
    assign ve_state[ 447:384] = ve_axis(4'd6);
    assign ve_state[ 511:448] = ve_axis(4'd7);
    assign ve_state[ 575:512] = ve_axis(4'd8);
    assign ve_state[ 639:576] = ve_axis(4'd9);
    assign ve_state[ 703:640] = ve_axis(4'd10);
    assign ve_state[ 767:704] = ve_axis(4'd11);
    assign ve_state[ 831:768] = ve_axis(4'd12);

    assign ve_valid = boot_done;

endmodule
