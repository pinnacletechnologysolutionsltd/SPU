// spu13_topology6_state.v -- six-line positive/negative tetra topology state.
//
// This is the architectural state layer for JANUS.SCREW/JSCR-style inverse
// pathways.  It stores topology as six tetrahedral edge buses instead of
// projecting immediately back into Quadray A,B,C,D coordinates.

module spu13_topology6_state #(
    parameter WIDTH = 64,
    parameter LANES = 13,
    parameter LANE_WIDTH = 4,
    parameter OFFSET_WIDTH = 11
) (
    input  wire                    clk,
    input  wire                    rst_n,

    input  wire [LANE_WIDTH-1:0]   rd_lane,
    output wire [WIDTH-1:0]        rd_pos_ab,
    output wire [WIDTH-1:0]        rd_pos_ac,
    output wire [WIDTH-1:0]        rd_pos_ad,
    output wire [WIDTH-1:0]        rd_pos_bc,
    output wire [WIDTH-1:0]        rd_pos_bd,
    output wire [WIDTH-1:0]        rd_pos_cd,
    output wire [WIDTH-1:0]        rd_neg_ab,
    output wire [WIDTH-1:0]        rd_neg_ac,
    output wire [WIDTH-1:0]        rd_neg_ad,
    output wire [WIDTH-1:0]        rd_neg_bc,
    output wire [WIDTH-1:0]        rd_neg_bd,
    output wire [WIDTH-1:0]        rd_neg_cd,

    input  wire                    load_en,
    input  wire [LANE_WIDTH-1:0]   load_lane,
    input  wire [WIDTH-1:0]        load_pos_ab,
    input  wire [WIDTH-1:0]        load_pos_ac,
    input  wire [WIDTH-1:0]        load_pos_ad,
    input  wire [WIDTH-1:0]        load_pos_bc,
    input  wire [WIDTH-1:0]        load_pos_bd,
    input  wire [WIDTH-1:0]        load_pos_cd,
    input  wire [WIDTH-1:0]        load_neg_ab,
    input  wire [WIDTH-1:0]        load_neg_ac,
    input  wire [WIDTH-1:0]        load_neg_ad,
    input  wire [WIDTH-1:0]        load_neg_bc,
    input  wire [WIDTH-1:0]        load_neg_bd,
    input  wire [WIDTH-1:0]        load_neg_cd,

    input  wire                    janus_en,
    input  wire [LANE_WIDTH-1:0]   janus_src_lane,
    input  wire [LANE_WIDTH-1:0]   janus_dst_lane,
    input  wire [1:0]              dual_mode,
    input  wire [1:0]              screw_mode,
    input  wire [OFFSET_WIDTH-1:0] phase_offset,
    input  wire                    pos_boundary,
    input  wire                    neg_boundary,

    output reg                     janus_done,
    output wire                    fire_pos,
    output wire                    fire_neg,
    output wire                    phase_match,
    output wire                    phase_mismatch
);

    reg [WIDTH-1:0] pos_ab [0:LANES-1];
    reg [WIDTH-1:0] pos_ac [0:LANES-1];
    reg [WIDTH-1:0] pos_ad [0:LANES-1];
    reg [WIDTH-1:0] pos_bc [0:LANES-1];
    reg [WIDTH-1:0] pos_bd [0:LANES-1];
    reg [WIDTH-1:0] pos_cd [0:LANES-1];
    reg [WIDTH-1:0] neg_ab [0:LANES-1];
    reg [WIDTH-1:0] neg_ac [0:LANES-1];
    reg [WIDTH-1:0] neg_ad [0:LANES-1];
    reg [WIDTH-1:0] neg_bc [0:LANES-1];
    reg [WIDTH-1:0] neg_bd [0:LANES-1];
    reg [WIDTH-1:0] neg_cd [0:LANES-1];

    wire rd_lane_ok = (rd_lane < LANES);
    wire src_lane_ok = (janus_src_lane < LANES);

    assign rd_pos_ab = rd_lane_ok ? pos_ab[rd_lane] : {WIDTH{1'b0}};
    assign rd_pos_ac = rd_lane_ok ? pos_ac[rd_lane] : {WIDTH{1'b0}};
    assign rd_pos_ad = rd_lane_ok ? pos_ad[rd_lane] : {WIDTH{1'b0}};
    assign rd_pos_bc = rd_lane_ok ? pos_bc[rd_lane] : {WIDTH{1'b0}};
    assign rd_pos_bd = rd_lane_ok ? pos_bd[rd_lane] : {WIDTH{1'b0}};
    assign rd_pos_cd = rd_lane_ok ? pos_cd[rd_lane] : {WIDTH{1'b0}};
    assign rd_neg_ab = rd_lane_ok ? neg_ab[rd_lane] : {WIDTH{1'b0}};
    assign rd_neg_ac = rd_lane_ok ? neg_ac[rd_lane] : {WIDTH{1'b0}};
    assign rd_neg_ad = rd_lane_ok ? neg_ad[rd_lane] : {WIDTH{1'b0}};
    assign rd_neg_bc = rd_lane_ok ? neg_bc[rd_lane] : {WIDTH{1'b0}};
    assign rd_neg_bd = rd_lane_ok ? neg_bd[rd_lane] : {WIDTH{1'b0}};
    assign rd_neg_cd = rd_lane_ok ? neg_cd[rd_lane] : {WIDTH{1'b0}};

    wire [WIDTH-1:0] src_pos_ab = src_lane_ok ? pos_ab[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_pos_ac = src_lane_ok ? pos_ac[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_pos_ad = src_lane_ok ? pos_ad[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_pos_bc = src_lane_ok ? pos_bc[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_pos_bd = src_lane_ok ? pos_bd[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_pos_cd = src_lane_ok ? pos_cd[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_neg_ab = src_lane_ok ? neg_ab[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_neg_ac = src_lane_ok ? neg_ac[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_neg_ad = src_lane_ok ? neg_ad[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_neg_bc = src_lane_ok ? neg_bc[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_neg_bd = src_lane_ok ? neg_bd[janus_src_lane] : {WIDTH{1'b0}};
    wire [WIDTH-1:0] src_neg_cd = src_lane_ok ? neg_cd[janus_src_lane] : {WIDTH{1'b0}};

    wire [WIDTH-1:0] next_pos_ab, next_pos_ac, next_pos_ad;
    wire [WIDTH-1:0] next_pos_bc, next_pos_bd, next_pos_cd;
    wire [WIDTH-1:0] next_neg_ab, next_neg_ac, next_neg_ad;
    wire [WIDTH-1:0] next_neg_bc, next_neg_bd, next_neg_cd;

    spu13_janus_dual_mode #(
        .WIDTH(WIDTH),
        .OFFSET_WIDTH(OFFSET_WIDTH)
    ) u_janus_dual (
        .clk(clk),
        .rst_n(rst_n),
        .dual_mode(dual_mode),
        .screw_mode(screw_mode),
        .phase_offset(phase_offset),
        .pos_boundary(janus_en && pos_boundary),
        .neg_boundary(janus_en && neg_boundary),
        .pos_ab_in(src_pos_ab),
        .pos_ac_in(src_pos_ac),
        .pos_ad_in(src_pos_ad),
        .pos_bc_in(src_pos_bc),
        .pos_bd_in(src_pos_bd),
        .pos_cd_in(src_pos_cd),
        .neg_ab_in(src_neg_ab),
        .neg_ac_in(src_neg_ac),
        .neg_ad_in(src_neg_ad),
        .neg_bc_in(src_neg_bc),
        .neg_bd_in(src_neg_bd),
        .neg_cd_in(src_neg_cd),
        .pos_ab_out(next_pos_ab),
        .pos_ac_out(next_pos_ac),
        .pos_ad_out(next_pos_ad),
        .pos_bc_out(next_pos_bc),
        .pos_bd_out(next_pos_bd),
        .pos_cd_out(next_pos_cd),
        .neg_ab_out(next_neg_ab),
        .neg_ac_out(next_neg_ac),
        .neg_ad_out(next_neg_ad),
        .neg_bc_out(next_neg_bc),
        .neg_bd_out(next_neg_bd),
        .neg_cd_out(next_neg_cd),
        .fire_pos(fire_pos),
        .fire_neg(fire_neg),
        .phase_match(phase_match),
        .phase_mismatch(phase_mismatch)
    );

    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            janus_done <= 1'b0;
            for (i = 0; i < LANES; i = i + 1) begin
                pos_ab[i] <= {WIDTH{1'b0}};
                pos_ac[i] <= {WIDTH{1'b0}};
                pos_ad[i] <= {WIDTH{1'b0}};
                pos_bc[i] <= {WIDTH{1'b0}};
                pos_bd[i] <= {WIDTH{1'b0}};
                pos_cd[i] <= {WIDTH{1'b0}};
                neg_ab[i] <= {WIDTH{1'b0}};
                neg_ac[i] <= {WIDTH{1'b0}};
                neg_ad[i] <= {WIDTH{1'b0}};
                neg_bc[i] <= {WIDTH{1'b0}};
                neg_bd[i] <= {WIDTH{1'b0}};
                neg_cd[i] <= {WIDTH{1'b0}};
            end
        end else begin
            janus_done <= 1'b0;

            if (load_en && (load_lane < LANES)) begin
                pos_ab[load_lane] <= load_pos_ab;
                pos_ac[load_lane] <= load_pos_ac;
                pos_ad[load_lane] <= load_pos_ad;
                pos_bc[load_lane] <= load_pos_bc;
                pos_bd[load_lane] <= load_pos_bd;
                pos_cd[load_lane] <= load_pos_cd;
                neg_ab[load_lane] <= load_neg_ab;
                neg_ac[load_lane] <= load_neg_ac;
                neg_ad[load_lane] <= load_neg_ad;
                neg_bc[load_lane] <= load_neg_bc;
                neg_bd[load_lane] <= load_neg_bd;
                neg_cd[load_lane] <= load_neg_cd;
            end else if (janus_en && (janus_dst_lane < LANES)) begin
                pos_ab[janus_dst_lane] <= next_pos_ab;
                pos_ac[janus_dst_lane] <= next_pos_ac;
                pos_ad[janus_dst_lane] <= next_pos_ad;
                pos_bc[janus_dst_lane] <= next_pos_bc;
                pos_bd[janus_dst_lane] <= next_pos_bd;
                pos_cd[janus_dst_lane] <= next_pos_cd;
                neg_ab[janus_dst_lane] <= next_neg_ab;
                neg_ac[janus_dst_lane] <= next_neg_ac;
                neg_ad[janus_dst_lane] <= next_neg_ad;
                neg_bc[janus_dst_lane] <= next_neg_bc;
                neg_bd[janus_dst_lane] <= next_neg_bd;
                neg_cd[janus_dst_lane] <= next_neg_cd;
                janus_done <= 1'b1;
            end
        end
    end

endmodule
