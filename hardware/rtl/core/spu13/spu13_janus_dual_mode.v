// spu13_janus_dual_mode.v -- dual tetrahedron Janus topology controller.
//
// This wrapper keeps the Janus trigger explicit.  It does not try to infer
// "zero volume" from signed arithmetic; upstream PHSLK/RPLU logic supplies
// boundary strobes when the algebraic predicate is true.
//
// dual_mode:
//   0 PISTON      -- positive tetrahedron passes through, negative screws
//   1 SEESAW      -- both boundaries must arrive together; outputs cross-couple
//   2 INDEPENDENT -- each side screws on its own boundary; phase offset checked
//   3 HOLD        -- no topology change

module spu13_janus_dual_mode #(
    parameter WIDTH = 64,
    parameter OFFSET_WIDTH = 11
) (
    input  wire                    clk,
    input  wire                    rst_n,

    input  wire [1:0]              dual_mode,
    input  wire [1:0]              screw_mode,
    input  wire [OFFSET_WIDTH-1:0] phase_offset,
    input  wire                    pos_boundary,
    input  wire                    neg_boundary,

    input  wire [WIDTH-1:0] pos_ab_in,
    input  wire [WIDTH-1:0] pos_ac_in,
    input  wire [WIDTH-1:0] pos_ad_in,
    input  wire [WIDTH-1:0] pos_bc_in,
    input  wire [WIDTH-1:0] pos_bd_in,
    input  wire [WIDTH-1:0] pos_cd_in,

    input  wire [WIDTH-1:0] neg_ab_in,
    input  wire [WIDTH-1:0] neg_ac_in,
    input  wire [WIDTH-1:0] neg_ad_in,
    input  wire [WIDTH-1:0] neg_bc_in,
    input  wire [WIDTH-1:0] neg_bd_in,
    input  wire [WIDTH-1:0] neg_cd_in,

    output wire [WIDTH-1:0] pos_ab_out,
    output wire [WIDTH-1:0] pos_ac_out,
    output wire [WIDTH-1:0] pos_ad_out,
    output wire [WIDTH-1:0] pos_bc_out,
    output wire [WIDTH-1:0] pos_bd_out,
    output wire [WIDTH-1:0] pos_cd_out,

    output wire [WIDTH-1:0] neg_ab_out,
    output wire [WIDTH-1:0] neg_ac_out,
    output wire [WIDTH-1:0] neg_ad_out,
    output wire [WIDTH-1:0] neg_bc_out,
    output wire [WIDTH-1:0] neg_bd_out,
    output wire [WIDTH-1:0] neg_cd_out,

    output wire                    fire_pos,
    output wire                    fire_neg,
    output reg                     phase_match,
    output reg                     phase_mismatch
);

    localparam MODE_PISTON      = 2'd0;
    localparam MODE_SEESAW      = 2'd1;
    localparam MODE_INDEPENDENT = 2'd2;
    localparam MODE_HOLD        = 2'd3;

    wire [WIDTH-1:0] pos_perm_ab, pos_perm_ac, pos_perm_ad;
    wire [WIDTH-1:0] pos_perm_bc, pos_perm_bd, pos_perm_cd;
    wire [WIDTH-1:0] neg_perm_ab, neg_perm_ac, neg_perm_ad;
    wire [WIDTH-1:0] neg_perm_bc, neg_perm_bd, neg_perm_cd;

    spu13_janus_screw_lines #(.WIDTH(WIDTH)) u_pos_screw (
        .mode(screw_mode),
        .line_ab_in(pos_ab_in),
        .line_ac_in(pos_ac_in),
        .line_ad_in(pos_ad_in),
        .line_bc_in(pos_bc_in),
        .line_bd_in(pos_bd_in),
        .line_cd_in(pos_cd_in),
        .line_ab_out(pos_perm_ab),
        .line_ac_out(pos_perm_ac),
        .line_ad_out(pos_perm_ad),
        .line_bc_out(pos_perm_bc),
        .line_bd_out(pos_perm_bd),
        .line_cd_out(pos_perm_cd)
    );

    spu13_janus_screw_lines #(.WIDTH(WIDTH)) u_neg_screw (
        .mode(screw_mode),
        .line_ab_in(neg_ab_in),
        .line_ac_in(neg_ac_in),
        .line_ad_in(neg_ad_in),
        .line_bc_in(neg_bc_in),
        .line_bd_in(neg_bd_in),
        .line_cd_in(neg_cd_in),
        .line_ab_out(neg_perm_ab),
        .line_ac_out(neg_perm_ac),
        .line_ad_out(neg_perm_ad),
        .line_bc_out(neg_perm_bc),
        .line_bd_out(neg_perm_bd),
        .line_cd_out(neg_perm_cd)
    );

    wire seesaw_fire = (dual_mode == MODE_SEESAW) && pos_boundary && neg_boundary;

    assign fire_pos =
        (dual_mode == MODE_SEESAW)      ? seesaw_fire :
        (dual_mode == MODE_INDEPENDENT) ? pos_boundary :
                                           1'b0;

    assign fire_neg =
        (dual_mode == MODE_PISTON)      ? neg_boundary :
        (dual_mode == MODE_SEESAW)      ? seesaw_fire :
        (dual_mode == MODE_INDEPENDENT) ? neg_boundary :
                                           1'b0;

    wire cross_couple = (dual_mode == MODE_SEESAW) && seesaw_fire;

    assign pos_ab_out = cross_couple ? neg_perm_ab : (fire_pos ? pos_perm_ab : pos_ab_in);
    assign pos_ac_out = cross_couple ? neg_perm_ac : (fire_pos ? pos_perm_ac : pos_ac_in);
    assign pos_ad_out = cross_couple ? neg_perm_ad : (fire_pos ? pos_perm_ad : pos_ad_in);
    assign pos_bc_out = cross_couple ? neg_perm_bc : (fire_pos ? pos_perm_bc : pos_bc_in);
    assign pos_bd_out = cross_couple ? neg_perm_bd : (fire_pos ? pos_perm_bd : pos_bd_in);
    assign pos_cd_out = cross_couple ? neg_perm_cd : (fire_pos ? pos_perm_cd : pos_cd_in);

    assign neg_ab_out = cross_couple ? pos_perm_ab : (fire_neg ? neg_perm_ab : neg_ab_in);
    assign neg_ac_out = cross_couple ? pos_perm_ac : (fire_neg ? neg_perm_ac : neg_ac_in);
    assign neg_ad_out = cross_couple ? pos_perm_ad : (fire_neg ? neg_perm_ad : neg_ad_in);
    assign neg_bc_out = cross_couple ? pos_perm_bc : (fire_neg ? neg_perm_bc : neg_bc_in);
    assign neg_bd_out = cross_couple ? pos_perm_bd : (fire_neg ? neg_perm_bd : neg_bd_in);
    assign neg_cd_out = cross_couple ? pos_perm_cd : (fire_neg ? neg_perm_cd : neg_cd_in);

    reg waiting_for_neg;
    reg waiting_for_pos;
    reg [OFFSET_WIDTH-1:0] phase_count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            waiting_for_neg <= 1'b0;
            waiting_for_pos <= 1'b0;
            phase_count <= {OFFSET_WIDTH{1'b0}};
            phase_match <= 1'b0;
            phase_mismatch <= 1'b0;
        end else begin
            phase_match <= 1'b0;
            phase_mismatch <= 1'b0;

            if (dual_mode != MODE_INDEPENDENT) begin
                waiting_for_neg <= 1'b0;
                waiting_for_pos <= 1'b0;
                phase_count <= {OFFSET_WIDTH{1'b0}};
                if (dual_mode == MODE_SEESAW && (pos_boundary ^ neg_boundary))
                    phase_mismatch <= 1'b1;
                if (dual_mode == MODE_SEESAW && pos_boundary && neg_boundary)
                    phase_match <= 1'b1;
            end else if (pos_boundary && neg_boundary) begin
                waiting_for_neg <= 1'b0;
                waiting_for_pos <= 1'b0;
                phase_count <= {OFFSET_WIDTH{1'b0}};
                if (phase_offset == {OFFSET_WIDTH{1'b0}})
                    phase_match <= 1'b1;
                else
                    phase_mismatch <= 1'b1;
            end else if (waiting_for_neg) begin
                if (neg_boundary) begin
                    waiting_for_neg <= 1'b0;
                    phase_match <= (phase_count == phase_offset);
                    phase_mismatch <= (phase_count != phase_offset);
                    phase_count <= {OFFSET_WIDTH{1'b0}};
                end else begin
                    phase_count <= phase_count + 1'b1;
                end
            end else if (waiting_for_pos) begin
                if (pos_boundary) begin
                    waiting_for_pos <= 1'b0;
                    phase_match <= (phase_count == phase_offset);
                    phase_mismatch <= (phase_count != phase_offset);
                    phase_count <= {OFFSET_WIDTH{1'b0}};
                end else begin
                    phase_count <= phase_count + 1'b1;
                end
            end else if (pos_boundary) begin
                waiting_for_neg <= 1'b1;
                phase_count <= {{(OFFSET_WIDTH-1){1'b0}}, 1'b1};
            end else if (neg_boundary) begin
                waiting_for_pos <= 1'b1;
                phase_count <= {{(OFFSET_WIDTH-1){1'b0}}, 1'b1};
            end
        end
    end

endmodule
