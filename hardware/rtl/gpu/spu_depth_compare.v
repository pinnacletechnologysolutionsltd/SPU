// spu_depth_compare.v — real depth-aware pixel selection between the two
// spu_dual_raster.v triangle units, using spu_attr_stepper.v's
// interpolated depth (depth-v2). Consumes spu_dual_raster.v's raw
// per-unit cov0/cov1/r0../r1.. ports (added 2026-08-25 alongside this),
// NOT its pixel_r/g/b outputs, which remain fixed-priority only.
//
// Depth convention (explicitly defined here -- nothing upstream of this
// module ever established a near/far semantic for the per-vertex z0..z2
// inputs depth-v2 takes): SMALLER value_out is NEARER, the standard
// depth-buffer convention. Ties go to unit 0.
//
// If a caller wants unit 0 to win regardless of depth for coincident
// surfaces, or wants any other tie policy, that's a scoping decision for
// whoever integrates this -- not addressed here, since there's no
// evidence yet of a real case needing it (AGENTS.md §2.2).
//
// No floating point, no division: pure signed comparison + mux.
// CC0 1.0 Universal.

module spu_depth_compare (
    input  wire        cov0,
    input  wire        cov1,
    input  wire signed [55:0] depth0,
    input  wire signed [55:0] depth1,
    input  wire [3:0]  r0, g0, b0,
    input  wire [3:0]  r1, g1, b1,
    output wire [3:0]  pixel_r,
    output wire [3:0]  pixel_g,
    output wire [3:0]  pixel_b
);

    wire unit0_wins = cov0 && (!cov1 || (depth0 <= depth1));
    wire unit1_wins = cov1 && !unit0_wins;

    assign pixel_r = unit0_wins ? r0 : (unit1_wins ? r1 : 4'h0);
    assign pixel_g = unit0_wins ? g0 : (unit1_wins ? g1 : 4'h0);
    assign pixel_b = unit0_wins ? b0 : (unit1_wins ? b1 : 4'h0);

endmodule
