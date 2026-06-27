// spu13_janus_screw_lines.v -- tetrahedral edge topology permuter.
//
// This module operates on the six unoriented edge/line buses of a tetrahedron:
//   0 AB, 1 AC, 2 AD, 3 BC, 4 BD, 5 CD
//
// It is intentionally combinational.  JANUS.SCREW should be a topology/path
// operation first, not a new arithmetic unit.  If a later Thomson testbench
// requires directed edges, add orientation/sign handling outside this module so
// the pure permutation remains cheap and independently verifiable.

module spu13_janus_screw_lines #(
    parameter WIDTH = 64
) (
    input  wire [1:0]       mode,

    input  wire [WIDTH-1:0] line_ab_in,
    input  wire [WIDTH-1:0] line_ac_in,
    input  wire [WIDTH-1:0] line_ad_in,
    input  wire [WIDTH-1:0] line_bc_in,
    input  wire [WIDTH-1:0] line_bd_in,
    input  wire [WIDTH-1:0] line_cd_in,

    output reg  [WIDTH-1:0] line_ab_out,
    output reg  [WIDTH-1:0] line_ac_out,
    output reg  [WIDTH-1:0] line_ad_out,
    output reg  [WIDTH-1:0] line_bc_out,
    output reg  [WIDTH-1:0] line_bd_out,
    output reg  [WIDTH-1:0] line_cd_out
);

    localparam MODE_STRAIGHT = 2'd0;
    localparam MODE_SCREW_CW = 2'd1;
    localparam MODE_SCREW_CCW = 2'd2;
    localparam MODE_DUAL = 2'd3;

    always @(*) begin
        case (mode)
            MODE_SCREW_CW: begin
                // Input mapping:
                //   AB->BC, AC->CD, AD->BD, BC->AD, BD->AC, CD->AB
                line_ab_out = line_cd_in;
                line_ac_out = line_bd_in;
                line_ad_out = line_bc_in;
                line_bc_out = line_ab_in;
                line_bd_out = line_ad_in;
                line_cd_out = line_ac_in;
            end

            MODE_SCREW_CCW: begin
                // Inverse of MODE_SCREW_CW.
                line_ab_out = line_bc_in;
                line_ac_out = line_cd_in;
                line_ad_out = line_bd_in;
                line_bc_out = line_ad_in;
                line_bd_out = line_ac_in;
                line_cd_out = line_ab_in;
            end

            MODE_DUAL: begin
                // Opposite-edge dual / inverted tetra topology:
                //   AB↔CD, AC↔BD, AD↔BC  (each edge swaps with its opposite)
                line_ab_out = line_cd_in;
                line_ac_out = line_bd_in;
                line_ad_out = line_bc_in;
                line_bc_out = line_ad_in;
                line_bd_out = line_ac_in;
                line_cd_out = line_ab_in;
            end

            default: begin
                line_ab_out = line_ab_in;
                line_ac_out = line_ac_in;
                line_ad_out = line_ad_in;
                line_bc_out = line_bc_in;
                line_bd_out = line_bd_in;
                line_cd_out = line_cd_in;
            end
        endcase
    end

endmodule
