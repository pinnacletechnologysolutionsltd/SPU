// Profile-aware scene splitter: legacy geometry plus T1h scalar or T1i UV data.
// T1h appends three and T1i appends six 16-bit attributes per canonical record.
// CC0 1.0 Universal.

module spu_scene_profile_unpack #(
    parameter integer SCENE_BITS = 1008,
    parameter integer FOUR_SCENE = 1,
    parameter integer T1H_SCALAR_SCENE = 0,
    parameter integer T1I_UV_SCENE = 0
) (
    input wire [SCENE_BITS-1:0] active_scene,
    input wire [SCENE_BITS-1:0] candidate_scene,
    output wire [1007:0] active_geometry_scene,
    output wire [1007:0] candidate_geometry_scene,
    output wire [63:0] active_attr0_bus,
    output wire [63:0] active_attr1_bus,
    output wire [63:0] active_attr2_bus,
    output wire [63:0] candidate_attr0_bus,
    output wire [63:0] candidate_attr1_bus,
    output wire [63:0] candidate_attr2_bus,
    output wire [63:0] candidate_u0_bus,
    output wire [63:0] candidate_v0_bus,
    output wire [63:0] candidate_u1_bus,
    output wire [63:0] candidate_v1_bus,
    output wire [63:0] candidate_u2_bus,
    output wire [63:0] candidate_v2_bus
);
    generate
        if (T1I_UV_SCENE) begin: t1i_profile
            genvar lane;
            for (lane=0; lane<4; lane=lane+1) begin: records
                assign active_geometry_scene[lane*252 +: 252] =
                    active_scene[lane*348 +: 252];
                assign candidate_geometry_scene[lane*252 +: 252] =
                    candidate_scene[lane*348 +: 252];
                assign candidate_u0_bus[lane*16 +: 16] = candidate_scene[lane*348+252 +: 16];
                assign candidate_v0_bus[lane*16 +: 16] = candidate_scene[lane*348+268 +: 16];
                assign candidate_u1_bus[lane*16 +: 16] = candidate_scene[lane*348+284 +: 16];
                assign candidate_v1_bus[lane*16 +: 16] = candidate_scene[lane*348+300 +: 16];
                assign candidate_u2_bus[lane*16 +: 16] = candidate_scene[lane*348+316 +: 16];
                assign candidate_v2_bus[lane*16 +: 16] = candidate_scene[lane*348+332 +: 16];
            end
            assign active_attr0_bus=0; assign active_attr1_bus=0; assign active_attr2_bus=0;
            assign candidate_attr0_bus=0; assign candidate_attr1_bus=0; assign candidate_attr2_bus=0;
        end else if (T1H_SCALAR_SCENE) begin: t1h_profile
            genvar lane;
            for (lane=0; lane<4; lane=lane+1) begin: records
                assign active_geometry_scene[lane*252 +: 252] =
                    active_scene[lane*300 +: 252];
                assign candidate_geometry_scene[lane*252 +: 252] =
                    candidate_scene[lane*300 +: 252];
                assign active_attr0_bus[lane*16 +: 16] =
                    active_scene[lane*300+252 +: 16];
                assign active_attr1_bus[lane*16 +: 16] =
                    active_scene[lane*300+268 +: 16];
                assign active_attr2_bus[lane*16 +: 16] =
                    active_scene[lane*300+284 +: 16];
                assign candidate_attr0_bus[lane*16 +: 16] =
                    candidate_scene[lane*300+252 +: 16];
                assign candidate_attr1_bus[lane*16 +: 16] =
                    candidate_scene[lane*300+268 +: 16];
                assign candidate_attr2_bus[lane*16 +: 16] =
                    candidate_scene[lane*300+284 +: 16];
            end
        end else begin: legacy_profile
            if (FOUR_SCENE) begin: four_records
                assign active_geometry_scene=active_scene[1007:0];
                assign candidate_geometry_scene=candidate_scene[1007:0];
            end else begin: two_records
                assign active_geometry_scene={504'd0,active_scene[503:0]};
                assign candidate_geometry_scene={504'd0,candidate_scene[503:0]};
            end
            assign active_attr0_bus=0; assign active_attr1_bus=0; assign active_attr2_bus=0;
            assign candidate_attr0_bus=0; assign candidate_attr1_bus=0; assign candidate_attr2_bus=0;
        end
        if (!T1I_UV_SCENE) begin: no_t1i_profile
            assign candidate_u0_bus=0; assign candidate_v0_bus=0;
            assign candidate_u1_bus=0; assign candidate_v1_bus=0;
            assign candidate_u2_bus=0; assign candidate_v2_bus=0;
        end
    endgenerate
endmodule
