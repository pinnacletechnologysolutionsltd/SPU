// spu_gpu_top.v — GPU subsystem top for Tang Primer 25K
// Combines: video timing, dual rasterizer, depth-v2 (affine-interpolated
// depth + real depth-aware pixel selection), VGA + HDMI HAL.
// Pixel clock = 25 MHz (clk_pixel).  TMDS clock = 250 MHz (clk_tmds).
// No framebuffer: pixels stream out synchronously with display timing.
//
// Depth-v2 added 2026-08-25 (same day as its RTL implementation, first
// silicon proof, and spu_depth_compare.v): tri0_setup/tri1_setup now
// also trigger the depth-v2 setup sequence for that unit (one setup
// pulse per triangle covers both coverage and depth, matching how a
// host would naturally use this -- one triangle, one setup). Final
// pixel selection is now real depth comparison (spu_depth_compare.v),
// not spu_dual_raster.v's old fixed-priority pixel_r/g/b (which that
// module still provides, unused here, for any consumer that wants
// coverage-only fixed-priority instead).
//
// CC0 1.0 Universal.

module spu_gpu_top #(
    // DEVICE has NO usable default on purpose. It used to default to "GW5A",
    // which meant an Artix-7 top that forgot to set it synthesised the Gowin
    // branch and died on ELVDS_OBUF -- or worse, would have picked a silently
    // wrong serialiser contract. Every instantiation must name its board.
    // Valid: "GW5A" (Gowin), "A7" or "XILINX" (Artix-7).
    parameter DEVICE = "UNSET",
    // Video timing, forwarded to spu_video_timing. Defaults are 640x480@60
    // and every board top relies on them. They exist so a testbench can use a
    // small frame: at full size three frames is 1.26M cycles and ~28 s of
    // iverilog, nearly twice run_all_tests.py's 15 s per-bench limit, which
    // is what made the first version of the frame-anchor bench time out.
    parameter H_ACTIVE = 640,
    parameter H_FP     = 16,
    parameter H_SYNC   = 96,
    parameter H_BP     = 48,
    parameter V_ACTIVE = 480,
    parameter V_FP     = 10,
    parameter V_SYNC   = 2,
    parameter V_BP     = 33,
    // ENABLE_HDMI=0 omits hal_hdmi entirely and ties the TMDS outputs low.
    // Required on openXC7/nextpnr-xilinx, whose placer HANGS on differential
    // output (OBUFDS/TMDS_33) -- upstream issue #66, open and unimplemented,
    // so a toolchain rebuild will not fix it. Default 1 preserves the
    // pre-existing behaviour for the Gowin path and for any Vivado flow.
    parameter ENABLE_HDMI = 1,
    // T1c byte-level prepared-scene path. Default 0 preserves every existing
    // direct-triangle caller; no physical UART is instantiated here.
    parameter PREPARED_SCENE = 0,
    // T1f Family A profile. Default 0 preserves the frozen T1d/T1e
    // prepared-scene wire format and top-level behavior.
    parameter FOUR_PRIMITIVE_SCENE = 0,
    // T1h adds three unsigned 16-bit vertex samples per primitive. Default 0
    // preserves all earlier top-level profiles and scene packet layouts.
    parameter T1H_SCALAR_SCENE = 0,
    // Optional physical observability for T1h. The selected scalar's bits
    // [14:11] drive grayscale after depth winner selection; the Artix VGA
    // board exports bit 3 of each channel, giving a stable 16384 threshold.
    parameter T1H_SCALAR_DIAG = 0,
    // T1i carries independent raw U/V coordinates through the same winner.
    // Default 0 preserves all earlier packet profiles and behavior.
    parameter T1I_UV_SCENE = 0,
    // T1i hardware observability only. Selected U/V MSBs drive binary red and
    // green bands after depth winner selection; default 0 preserves RGB.
    parameter T1I_UV_DIAG = 0,
    // Experimental U/V path isolation. Registers winner-selected U/V, valid,
    // active, and sync together before applying the same binary visualization.
    parameter T1I_UV_REG_DIAG = 0,
    // Experimental T1i output isolation: 1 coverage, 2 combinational winner,
    // 3 registered winner output. Default 0 preserves the normal renderer.
    parameter T1I_DEPTH_DIAG = 0,
    // One aligned RGB/sync/active register after final pixel-color selection.
    // Default 0 preserves every existing profile's output cycle.
    parameter GPU_POST_WINNER_REG = 0
) (
    input  wire        clk_pixel,    // 25 MHz
    input  wire        clk_tmds,     // 250 MHz
    input  wire        rst_n,

    // Triangle 0 interface (from SPU-13 / CPU)
    input  wire        tri0_setup,
    input  wire signed [15:0] tri0_a0,
    input  wire signed [15:0] tri0_b0,
    input  wire signed [31:0] tri0_c0,
    input  wire signed [15:0] tri0_a1,
    input  wire signed [15:0] tri0_b1,
    input  wire signed [31:0] tri0_c1,
    input  wire signed [15:0] tri0_a2,
    input  wire signed [15:0] tri0_b2,
    input  wire signed [31:0] tri0_c2,
    input  wire [3:0]  tri0_r, tri0_g, tri0_b,
    input  wire [15:0] tri0_z0, tri0_z1, tri0_z2,   // per-vertex depth

    // Triangle 1 interface
    input  wire        tri1_setup,
    input  wire signed [15:0] tri1_a0,
    input  wire signed [15:0] tri1_b0,
    input  wire signed [31:0] tri1_c0,
    input  wire signed [15:0] tri1_a1,
    input  wire signed [15:0] tri1_b1,
    input  wire signed [31:0] tri1_c1,
    input  wire signed [15:0] tri1_a2,
    input  wire signed [15:0] tri1_b2,
    input  wire signed [31:0] tri1_c2,
    input  wire [3:0]  tri1_r, tri1_g, tri1_b,
    input  wire [15:0] tri1_z0, tri1_z1, tri1_z2,

    // Already-decoded byte stream used only when PREPARED_SCENE=1.
    input  wire [7:0]  scene_rx_byte,
    input  wire        scene_rx_valid,

    // VGA PMOD outputs
    output wire [3:0]  vga_r, vga_g, vga_b,
    output wire        vga_hsync, vga_vsync,

    // HDMI differential outputs
    output wire        tmds_clk_p, tmds_clk_n,
    output wire [2:0]  tmds_d_p, tmds_d_n
`ifdef GPU_T1D_DIAG
    , output wire      diag_start_accepted,
    output wire        diag_payload_accepted,
    output wire [6:0]  diag_payload_count,
    output wire        diag_receiving,
    output wire        diag_active_bank,
    output wire        diag_commit_pending,
    output wire        diag_activate_scene,
    output wire        diag_frame_start,
    output wire        diag_ready0,
    output wire        diag_ready1,
    output wire        diag_generation_matches
`endif
);

    // ── Video timing ─────────────────────────────────────────────────────
    wire [9:0] vx, vy;
    wire hsync, vsync, active;
    wire step_x;
    assign step_x = active;
    wire step_y;  // one cycle after hsync falling (end of line)

    spu_video_timing #(
        .H_ACTIVE(H_ACTIVE), .H_FP(H_FP), .H_SYNC(H_SYNC), .H_BP(H_BP),
        .V_ACTIVE(V_ACTIVE), .V_FP(V_FP), .V_SYNC(V_SYNC), .V_BP(V_BP)
    ) u_timing (.clk(clk_pixel), .rst_n(rst_n),
        .x(vx), .y(vy), .hsync(hsync), .vsync(vsync), .active(active));

    // step_y when x wraps (start of each new visible row)
    // vx_d is reset like every other pipeline register in this module; it
    // previously had none, so step_y was X on the first simulation cycle and
    // propagated X into all six edge accumulators. Benign on an FPGA, where
    // flops come up at 0, but it made any testbench of this module unusable.
    reg [9:0] vx_d;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) vx_d <= 10'd0;
        else        vx_d <= vx;
    end
    assign step_y = (vx == 10'd0) && (vx_d != 10'd0);

    // BUG FIX 2026-08-25 (pre-existing, found while building the first
    // real testbench this top-level has ever had -- unrelated to
    // depth-v2). spu_edge_stepper.v's accumulator `f` is a register whose
    // update this cycle is driven by step_x/active as they stood BEFORE
    // this edge -- so by the time vx reads a new value N, f has only just
    // become ready to represent N one cycle later. That's an ordinary,
    // unavoidable one-cycle group delay for any accumulator driven this
    // way, not a bug in the accumulator itself. The actual bug is that
    // hsync/vsync/active were fed to hal_vga/hal_hdmi WITHOUT that same
    // one-cycle delay, so the sync signals described position N while the
    // color pipeline was still delivering position N-1's color -- a
    // consistent one-pixel horizontal misalignment, confirmed by
    // exhaustive x-shift testing (RTL output at x matched the oracle's
    // expectation at x-1 with zero exceptions). Standard fix: delay the
    // sync/coordinate domain by one cycle to match the color pipeline's
    // depth, not try to make the color pipeline latency-free.
    reg hsync_d, vsync_d, active_d;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            hsync_d <= 1'b0; vsync_d <= 1'b0; active_d <= 1'b0;
        end else begin
            hsync_d <= hsync; vsync_d <= vsync; active_d <= active;
        end
    end

    // ── Frame-start re-anchor ────────────────────────────────────────────
    // BUG FIX 2026-09-05. step_y is derived from the horizontal wrap alone,
    // so it fires on all 525 lines of a frame while only 480 are displayed,
    // and nothing ever re-anchored the accumulators after `setup`. f_row
    // therefore reached C + 525*B at the start of the next frame instead of
    // returning to C, so a triangle set up once walked 525*B every frame --
    // the FULL frame's accumulation, since nothing re-anchored at all --
    // until it left the screen. Measured on the pre-fix RTL with B=170:
    // f_row at successive frame starts was -17520, 71730, 160980, a constant
    // step of 89250 = 525*170. Any consumer hit this; none existed to notice.
    //
    // Re-pulsing setup at (0,0) reloads f and f_row from the coefficient
    // inputs. spu_edge_stepper's `setup` branch precedes `step_y` in its
    // else-if chain, so on the cycle both are true the reload wins -- which
    // is what makes (0,0) the correct instant to do this rather than one
    // cycle either side of it.
    //
    // Gated by `armed`. A unit that has never been set up must not be
    // re-anchored: it would latch whatever sits on its coefficient inputs,
    // and with C=0 every edge reports inside (f >= 0) and the unit covers
    // the entire screen.
    //
    // Coefficients must be held stable by the caller for as long as the
    // triangle is to be drawn. That was already true -- `setup` latched them
    // and nothing re-read them -- but it is now a standing requirement rather
    // than a one-shot one.
    wire frame_start = (vx == 10'd0) && (vy == 10'd0);

    // ── T1c raw scene banking and canonical unpack ──────────────────────
    localparam integer FOUR_SCENE = PREPARED_SCENE && FOUR_PRIMITIVE_SCENE;
    localparam integer T1H_SCALAR = T1H_SCALAR_SCENE != 0;
    localparam integer T1I_UV = T1I_UV_SCENE != 0;
    localparam integer SCENE_BITS = T1I_UV ? 1392 :
        (T1H_SCALAR ? 1200 : (FOUR_SCENE ? 1008 : 504));
    wire [SCENE_BITS-1:0] active_scene, candidate_scene;
    wire scene_commit_pending;
    wire activate_scene;
    wire prepared_rx_valid = PREPARED_SCENE ? scene_rx_valid : 1'b0;

    spu_scene_loader #(
        .SCENE_BITS(SCENE_BITS),
        .PAYLOAD_BYTES(T1I_UV ? 174 : (T1H_SCALAR ? 150 : (FOUR_SCENE ? 126 : 63)))
    ) u_scene_loader (
        .clk(clk_pixel), .rst_n(rst_n), .rx_byte(scene_rx_byte),
        .rx_valid(prepared_rx_valid), .activate_raw_bank(activate_scene),
        .active_scene(active_scene), .candidate_scene(candidate_scene),
        .commit_pending(scene_commit_pending)
`ifdef GPU_T1D_DIAG
        , .diag_start_accepted(diag_start_accepted),
        .diag_payload_accepted(diag_payload_accepted),
        .diag_payload_count(diag_payload_count),
        .diag_receiving(diag_receiving),
        .diag_active_bank(diag_active_bank)
`endif
    );

    generate
        if (T1H_SCALAR && (!PREPARED_SCENE || !FOUR_PRIMITIVE_SCENE)) begin: bad_t1h_profile
            spu_gpu_top_T1H_requires_prepared_four_primitive_scene u_invalid_profile ();
        end
        if (T1H_SCALAR_DIAG && !T1H_SCALAR) begin: bad_t1h_diag_profile
            spu_gpu_top_T1H_scalar_diag_requires_scalar_scene u_invalid_profile ();
        end
        if (T1I_UV && (!PREPARED_SCENE || !FOUR_PRIMITIVE_SCENE)) begin: bad_t1i_profile
            spu_gpu_top_T1I_requires_prepared_four_primitive_scene u_invalid_profile ();
        end
        if (T1I_UV && T1H_SCALAR) begin: bad_t1i_t1h_profile
            spu_gpu_top_T1I_and_T1H_are_mutually_exclusive u_invalid_profile ();
        end
        if (T1I_UV_DIAG && (!T1I_UV || T1H_SCALAR || T1H_SCALAR_DIAG)) begin: bad_t1i_diag_profile
            spu_gpu_top_T1I_UV_diag_requires_uv_scene_without_t1h u_invalid_profile ();
        end
        if (T1I_UV_REG_DIAG && (!T1I_UV_DIAG || T1I_DEPTH_DIAG != 0)) begin: bad_t1i_uv_reg_diag_profile
            spu_gpu_top_T1I_UV_registered_diag_requires_uv_diag_only u_invalid_profile ();
        end
        if (GPU_POST_WINNER_REG && (!PREPARED_SCENE || !FOUR_PRIMITIVE_SCENE ||
            !T1I_UV || T1H_SCALAR || T1I_UV_REG_DIAG)) begin: bad_post_winner_register_profile
            spu_gpu_top_post_winner_register_requires_prepared_t1i_without_uv_register u_invalid_profile ();
        end
        if (T1I_DEPTH_DIAG < 0 || T1I_DEPTH_DIAG > 3) begin: bad_t1i_depth_diag_value
            spu_gpu_top_T1I_depth_diag_must_be_0_1_2_or_3 u_invalid_profile ();
        end
        if (T1I_DEPTH_DIAG != 0 &&
            (!T1I_UV || T1H_SCALAR || T1H_SCALAR_DIAG || T1I_UV_DIAG)) begin: bad_t1i_depth_diag_profile
            spu_gpu_top_T1I_depth_diag_requires_uv_scene_and_exclusive_diagnostic u_invalid_profile ();
        end
    endgenerate

`ifdef GPU_T1D_DIAG
    assign diag_commit_pending = scene_commit_pending;
    assign diag_activate_scene = activate_scene;
    assign diag_frame_start = frame_start;
`endif

    wire signed [15:0] ar_a0_0, ar_b0_0, ar_a1_0, ar_b1_0, ar_a2_0, ar_b2_0;
    wire signed [31:0] ar_c0_0, ar_c1_0, ar_c2_0;
    wire [3:0] ar_r0, ar_g0, ar_b_0;
    wire [15:0] ar_z0_0, ar_z1_0, ar_z2_0;
    wire signed [15:0] ar_a0_1, ar_b0_1, ar_a1_1, ar_b1_1, ar_a2_1, ar_b2_1;
    wire signed [31:0] ar_c0_1, ar_c1_1, ar_c2_1;
    wire [3:0] ar_r1, ar_g1, ar_b_1;
    wire [15:0] ar_z0_1, ar_z1_1, ar_z2_1;
    wire signed [15:0] ca_a0_0, ca_b0_0, ca_a1_0, ca_b1_0, ca_a2_0, ca_b2_0;
    wire signed [31:0] ca_c0_0, ca_c1_0, ca_c2_0;
    wire [3:0] ca_r0, ca_g0, ca_b_0;
    wire [15:0] ca_z0_0, ca_z1_0, ca_z2_0;
    wire signed [15:0] ca_a0_1, ca_b0_1, ca_a1_1, ca_b1_1, ca_a2_1, ca_b2_1;
    wire signed [31:0] ca_c0_1, ca_c1_1, ca_c2_1;
    wire [3:0] ca_r1, ca_g1, ca_b_1;
    wire [15:0] ca_z0_1, ca_z1_1, ca_z2_1;
    wire [1007:0] active_geometry_scene, candidate_geometry_scene;
    wire [63:0] candidate_attr0_bus, candidate_attr1_bus, candidate_attr2_bus;
    wire [63:0] candidate_u0_bus, candidate_v0_bus;
    wire [63:0] candidate_u1_bus, candidate_v1_bus;
    wire [63:0] candidate_u2_bus, candidate_v2_bus;
    spu_scene_profile_unpack #(.SCENE_BITS(SCENE_BITS), .FOUR_SCENE(FOUR_SCENE),
        .T1H_SCALAR_SCENE(T1H_SCALAR), .T1I_UV_SCENE(T1I_UV)) u_scene_profile_unpack (
        .active_scene(active_scene), .candidate_scene(candidate_scene),
        .active_geometry_scene(active_geometry_scene),
        .candidate_geometry_scene(candidate_geometry_scene),
        .active_attr0_bus(), .active_attr1_bus(), .active_attr2_bus(),
        .candidate_attr0_bus(candidate_attr0_bus),
        .candidate_attr1_bus(candidate_attr1_bus),
        .candidate_attr2_bus(candidate_attr2_bus),
        .candidate_u0_bus(candidate_u0_bus), .candidate_v0_bus(candidate_v0_bus),
        .candidate_u1_bus(candidate_u1_bus), .candidate_v1_bus(candidate_v1_bus),
        .candidate_u2_bus(candidate_u2_bus), .candidate_v2_bus(candidate_v2_bus));

    wire signed [15:0] ar_a0_2, ar_b0_2, ar_a1_2, ar_b1_2, ar_a2_2, ar_b2_2;
    wire signed [31:0] ar_c0_2, ar_c1_2, ar_c2_2;
    wire [3:0] ar_r2, ar_g2, ar_b_2;
    wire [15:0] ar_z0_2, ar_z1_2, ar_z2_2;
    wire signed [15:0] ar_a0_3, ar_b0_3, ar_a1_3, ar_b1_3, ar_a2_3, ar_b2_3;
    wire signed [31:0] ar_c0_3, ar_c1_3, ar_c2_3;
    wire [3:0] ar_r3, ar_g3, ar_b_3;
    wire [15:0] ar_z0_3, ar_z1_3, ar_z2_3;
    wire signed [15:0] ca_a0_2, ca_b0_2, ca_a1_2, ca_b1_2, ca_a2_2, ca_b2_2;
    wire signed [31:0] ca_c0_2, ca_c1_2, ca_c2_2;
    wire [3:0] ca_r2, ca_g2, ca_b_2;
    wire [15:0] ca_z0_2, ca_z1_2, ca_z2_2;
    wire signed [15:0] ca_a0_3, ca_b0_3, ca_a1_3, ca_b1_3, ca_a2_3, ca_b2_3;
    wire signed [31:0] ca_c0_3, ca_c1_3, ca_c2_3;
    wire [3:0] ca_r3, ca_g3, ca_b_3;
    wire [15:0] ca_z0_3, ca_z1_3, ca_z2_3;

    spu_scene_unpack u_active_tri0 (.scene(active_geometry_scene[251:0]),
        .a0(ar_a0_0), .b0(ar_b0_0), .c0(ar_c0_0), .a1(ar_a1_0), .b1(ar_b1_0), .c1(ar_c1_0),
        .a2(ar_a2_0), .b2(ar_b2_0), .c2(ar_c2_0), .r(ar_r0), .g(ar_g0), .b(ar_b_0),
        .z0(ar_z0_0), .z1(ar_z1_0), .z2(ar_z2_0));
    spu_scene_unpack u_active_tri1 (.scene(active_geometry_scene[503:252]),
        .a0(ar_a0_1), .b0(ar_b0_1), .c0(ar_c0_1), .a1(ar_a1_1), .b1(ar_b1_1), .c1(ar_c1_1),
        .a2(ar_a2_1), .b2(ar_b2_1), .c2(ar_c2_1), .r(ar_r1), .g(ar_g1), .b(ar_b_1),
        .z0(ar_z0_1), .z1(ar_z1_1), .z2(ar_z2_1));
    spu_scene_unpack u_candidate_tri0 (.scene(candidate_geometry_scene[251:0]),
        .a0(ca_a0_0), .b0(ca_b0_0), .c0(ca_c0_0), .a1(ca_a1_0), .b1(ca_b1_0), .c1(ca_c1_0),
        .a2(ca_a2_0), .b2(ca_b2_0), .c2(ca_c2_0), .r(ca_r0), .g(ca_g0), .b(ca_b_0),
        .z0(ca_z0_0), .z1(ca_z1_0), .z2(ca_z2_0));
    spu_scene_unpack u_candidate_tri1 (.scene(candidate_geometry_scene[503:252]),
        .a0(ca_a0_1), .b0(ca_b0_1), .c0(ca_c0_1), .a1(ca_a1_1), .b1(ca_b1_1), .c1(ca_c1_1),
        .a2(ca_a2_1), .b2(ca_b2_1), .c2(ca_c2_1), .r(ca_r1), .g(ca_g1), .b(ca_b_1),
        .z0(ca_z0_1), .z1(ca_z1_1), .z2(ca_z2_1));

    generate
        if (FOUR_SCENE) begin: prepared_tri34_unpack
            spu_scene_unpack u_active_tri2 (.scene(active_geometry_scene[755:504]),
                .a0(ar_a0_2), .b0(ar_b0_2), .c0(ar_c0_2), .a1(ar_a1_2), .b1(ar_b1_2), .c1(ar_c1_2),
                .a2(ar_a2_2), .b2(ar_b2_2), .c2(ar_c2_2), .r(ar_r2), .g(ar_g2), .b(ar_b_2),
                .z0(ar_z0_2), .z1(ar_z1_2), .z2(ar_z2_2));
            spu_scene_unpack u_active_tri3 (.scene(active_geometry_scene[1007:756]),
                .a0(ar_a0_3), .b0(ar_b0_3), .c0(ar_c0_3), .a1(ar_a1_3), .b1(ar_b1_3), .c1(ar_c1_3),
                .a2(ar_a2_3), .b2(ar_b2_3), .c2(ar_c2_3), .r(ar_r3), .g(ar_g3), .b(ar_b_3),
                .z0(ar_z0_3), .z1(ar_z1_3), .z2(ar_z2_3));
            spu_scene_unpack u_candidate_tri2 (.scene(candidate_geometry_scene[755:504]),
                .a0(ca_a0_2), .b0(ca_b0_2), .c0(ca_c0_2), .a1(ca_a1_2), .b1(ca_b1_2), .c1(ca_c1_2),
                .a2(ca_a2_2), .b2(ca_b2_2), .c2(ca_c2_2), .r(ca_r2), .g(ca_g2), .b(ca_b_2),
                .z0(ca_z0_2), .z1(ca_z1_2), .z2(ca_z2_2));
            spu_scene_unpack u_candidate_tri3 (.scene(candidate_geometry_scene[1007:756]),
                .a0(ca_a0_3), .b0(ca_b0_3), .c0(ca_c0_3), .a1(ca_a1_3), .b1(ca_b1_3), .c1(ca_c1_3),
                .a2(ca_a2_3), .b2(ca_b2_3), .c2(ca_c2_3), .r(ca_r3), .g(ca_g3), .b(ca_b_3),
                .z0(ca_z0_3), .z1(ca_z1_3), .z2(ca_z2_3));
        end else begin: direct_tri34_unpack
            assign ar_a0_2=0; assign ar_b0_2=0; assign ar_a1_2=0; assign ar_b1_2=0; assign ar_a2_2=0; assign ar_b2_2=0;
            assign ar_c0_2=0; assign ar_c1_2=0; assign ar_c2_2=0; assign ar_r2=0; assign ar_g2=0; assign ar_b_2=0;
            assign ar_z0_2=0; assign ar_z1_2=0; assign ar_z2_2=0;
            assign ar_a0_3=0; assign ar_b0_3=0; assign ar_a1_3=0; assign ar_b1_3=0; assign ar_a2_3=0; assign ar_b2_3=0;
            assign ar_c0_3=0; assign ar_c1_3=0; assign ar_c2_3=0; assign ar_r3=0; assign ar_g3=0; assign ar_b_3=0;
            assign ar_z0_3=0; assign ar_z1_3=0; assign ar_z2_3=0;
            assign ca_a0_2=0; assign ca_b0_2=0; assign ca_a1_2=0; assign ca_b1_2=0; assign ca_a2_2=0; assign ca_b2_2=0;
            assign ca_c0_2=0; assign ca_c1_2=0; assign ca_c2_2=0; assign ca_r2=0; assign ca_g2=0; assign ca_b_2=0;
            assign ca_z0_2=0; assign ca_z1_2=0; assign ca_z2_2=0;
            assign ca_a0_3=0; assign ca_b0_3=0; assign ca_a1_3=0; assign ca_b1_3=0; assign ca_a2_3=0; assign ca_b2_3=0;
            assign ca_c0_3=0; assign ca_c1_3=0; assign ca_c2_3=0; assign ca_r3=0; assign ca_g3=0; assign ca_b_3=0;
            assign ca_z0_3=0; assign ca_z1_3=0; assign ca_z2_3=0;
        end
    endgenerate

    // Coverage samples candidate coefficients on the activation edge; after
    // that edge T1a's active bank has advanced and supplies the same scene.
    wire use_candidate_now = PREPARED_SCENE && activate_scene;
    wire signed [15:0] cv_a0_0 = PREPARED_SCENE ? (use_candidate_now ? ca_a0_0 : ar_a0_0) : tri0_a0;
    wire signed [15:0] cv_b0_0 = PREPARED_SCENE ? (use_candidate_now ? ca_b0_0 : ar_b0_0) : tri0_b0;
    wire signed [31:0] cv_c0_0 = PREPARED_SCENE ? (use_candidate_now ? ca_c0_0 : ar_c0_0) : tri0_c0;
    wire signed [15:0] cv_a1_0 = PREPARED_SCENE ? (use_candidate_now ? ca_a1_0 : ar_a1_0) : tri0_a1;
    wire signed [15:0] cv_b1_0 = PREPARED_SCENE ? (use_candidate_now ? ca_b1_0 : ar_b1_0) : tri0_b1;
    wire signed [31:0] cv_c1_0 = PREPARED_SCENE ? (use_candidate_now ? ca_c1_0 : ar_c1_0) : tri0_c1;
    wire signed [15:0] cv_a2_0 = PREPARED_SCENE ? (use_candidate_now ? ca_a2_0 : ar_a2_0) : tri0_a2;
    wire signed [15:0] cv_b2_0 = PREPARED_SCENE ? (use_candidate_now ? ca_b2_0 : ar_b2_0) : tri0_b2;
    wire signed [31:0] cv_c2_0 = PREPARED_SCENE ? (use_candidate_now ? ca_c2_0 : ar_c2_0) : tri0_c2;
    wire signed [15:0] cv_a0_1 = PREPARED_SCENE ? (use_candidate_now ? ca_a0_1 : ar_a0_1) : tri1_a0;
    wire signed [15:0] cv_b0_1 = PREPARED_SCENE ? (use_candidate_now ? ca_b0_1 : ar_b0_1) : tri1_b0;
    wire signed [31:0] cv_c0_1 = PREPARED_SCENE ? (use_candidate_now ? ca_c0_1 : ar_c0_1) : tri1_c0;
    wire signed [15:0] cv_a1_1 = PREPARED_SCENE ? (use_candidate_now ? ca_a1_1 : ar_a1_1) : tri1_a1;
    wire signed [15:0] cv_b1_1 = PREPARED_SCENE ? (use_candidate_now ? ca_b1_1 : ar_b1_1) : tri1_b1;
    wire signed [31:0] cv_c1_1 = PREPARED_SCENE ? (use_candidate_now ? ca_c1_1 : ar_c1_1) : tri1_c1;
    wire signed [15:0] cv_a2_1 = PREPARED_SCENE ? (use_candidate_now ? ca_a2_1 : ar_a2_1) : tri1_a2;
    wire signed [15:0] cv_b2_1 = PREPARED_SCENE ? (use_candidate_now ? ca_b2_1 : ar_b2_1) : tri1_b2;
    wire signed [31:0] cv_c2_1 = PREPARED_SCENE ? (use_candidate_now ? ca_c2_1 : ar_c2_1) : tri1_c2;

    wire signed [15:0] cv_a0_2 = use_candidate_now ? ca_a0_2 : ar_a0_2;
    wire signed [15:0] cv_b0_2 = use_candidate_now ? ca_b0_2 : ar_b0_2;
    wire signed [31:0] cv_c0_2 = use_candidate_now ? ca_c0_2 : ar_c0_2;
    wire signed [15:0] cv_a1_2 = use_candidate_now ? ca_a1_2 : ar_a1_2;
    wire signed [15:0] cv_b1_2 = use_candidate_now ? ca_b1_2 : ar_b1_2;
    wire signed [31:0] cv_c1_2 = use_candidate_now ? ca_c1_2 : ar_c1_2;
    wire signed [15:0] cv_a2_2 = use_candidate_now ? ca_a2_2 : ar_a2_2;
    wire signed [15:0] cv_b2_2 = use_candidate_now ? ca_b2_2 : ar_b2_2;
    wire signed [31:0] cv_c2_2 = use_candidate_now ? ca_c2_2 : ar_c2_2;
    wire signed [15:0] cv_a0_3 = use_candidate_now ? ca_a0_3 : ar_a0_3;
    wire signed [15:0] cv_b0_3 = use_candidate_now ? ca_b0_3 : ar_b0_3;
    wire signed [31:0] cv_c0_3 = use_candidate_now ? ca_c0_3 : ar_c0_3;
    wire signed [15:0] cv_a1_3 = use_candidate_now ? ca_a1_3 : ar_a1_3;
    wire signed [15:0] cv_b1_3 = use_candidate_now ? ca_b1_3 : ar_b1_3;
    wire signed [31:0] cv_c1_3 = use_candidate_now ? ca_c1_3 : ar_c1_3;
    wire signed [15:0] cv_a2_3 = use_candidate_now ? ca_a2_3 : ar_a2_3;
    wire signed [15:0] cv_b2_3 = use_candidate_now ? ca_b2_3 : ar_b2_3;
    wire signed [31:0] cv_c2_3 = use_candidate_now ? ca_c2_3 : ar_c2_3;

    reg armed0, armed1, armed2, armed3;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            armed0 <= 1'b0;
            armed1 <= 1'b0;
            armed2 <= 1'b0;
            armed3 <= 1'b0;
        end else begin
            if (PREPARED_SCENE ? activate_scene : tri0_setup) armed0 <= 1'b1;
            if (PREPARED_SCENE ? activate_scene : tri1_setup) armed1 <= 1'b1;
            if (FOUR_SCENE && activate_scene) armed2 <= 1'b1;
            if (FOUR_SCENE && activate_scene) armed3 <= 1'b1;
        end
    end

    wire setup0 = (PREPARED_SCENE ? activate_scene : tri0_setup) | (frame_start & armed0);
    wire setup1 = (PREPARED_SCENE ? activate_scene : tri1_setup) | (frame_start & armed1);
    wire setup2 = FOUR_SCENE ? (activate_scene | (frame_start & armed2)) : 1'b0;
    wire setup3 = FOUR_SCENE ? (activate_scene | (frame_start & armed3)) : 1'b0;

    // ── Dual rasterizer (coverage) ──────────────────────────────────────
    wire [3:0] fixed_priority_r, fixed_priority_g, fixed_priority_b;  // unused
    wire cov0, cov1, cov2, cov3;
    wire [3:0] r0, g0, b0, r1, g1, b1, r2, g2, b2, r3, g3, b3;

    generate
        if (FOUR_SCENE) begin: prepared_quad_raster
            spu_quad_raster u_rast4 (.clk(clk_pixel), .rst_n(rst_n),
                .setup0(setup0),
                .a0_0(cv_a0_0), .b0_0(cv_b0_0), .a1_0(cv_a1_0), .b1_0(cv_b1_0),
                .a2_0(cv_a2_0), .b2_0(cv_b2_0), .c0_0(cv_c0_0), .c1_0(cv_c1_0), .c2_0(cv_c2_0),
                .tri_r0(ar_r0), .tri_g0(ar_g0), .tri_b0(ar_b_0),
                .setup1(setup1),
                .a0_1(cv_a0_1), .b0_1(cv_b0_1), .a1_1(cv_a1_1), .b1_1(cv_b1_1),
                .a2_1(cv_a2_1), .b2_1(cv_b2_1), .c0_1(cv_c0_1), .c1_1(cv_c1_1), .c2_1(cv_c2_1),
                .tri_r1(ar_r1), .tri_g1(ar_g1), .tri_b1(ar_b_1),
                .setup2(setup2),
                .a0_2(cv_a0_2), .b0_2(cv_b0_2), .a1_2(cv_a1_2), .b1_2(cv_b1_2),
                .a2_2(cv_a2_2), .b2_2(cv_b2_2), .c0_2(cv_c0_2), .c1_2(cv_c1_2), .c2_2(cv_c2_2),
                .tri_r2(ar_r2), .tri_g2(ar_g2), .tri_b2(ar_b_2),
                .setup3(setup3),
                .a0_3(cv_a0_3), .b0_3(cv_b0_3), .a1_3(cv_a1_3), .b1_3(cv_b1_3),
                .a2_3(cv_a2_3), .b2_3(cv_b2_3), .c0_3(cv_c0_3), .c1_3(cv_c1_3), .c2_3(cv_c2_3),
                .tri_r3(ar_r3), .tri_g3(ar_g3), .tri_b3(ar_b_3),
                .step_x(step_x), .step_y(step_y),
                .cov0(cov0), .cov1(cov1), .cov2(cov2), .cov3(cov3),
                .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
                .r2(r2), .g2(g2), .b2(b2), .r3(r3), .g3(g3), .b3(b3));
            assign fixed_priority_r = 0;
            assign fixed_priority_g = 0;
            assign fixed_priority_b = 0;
        end else begin: direct_dual_raster
            spu_dual_raster u_rast (.clk(clk_pixel), .rst_n(rst_n),
                .setup0(setup0),
                .a0_0(cv_a0_0), .b0_0(cv_b0_0), .c0_0(cv_c0_0),
                .a1_0(cv_a1_0), .b1_0(cv_b1_0), .c1_0(cv_c1_0),
                .a2_0(cv_a2_0), .b2_0(cv_b2_0), .c2_0(cv_c2_0),
                .tri_r0(PREPARED_SCENE ? ar_r0 : tri0_r),
                .tri_g0(PREPARED_SCENE ? ar_g0 : tri0_g),
                .tri_b0(PREPARED_SCENE ? ar_b_0 : tri0_b),
                .setup1(setup1),
                .a0_1(cv_a0_1), .b0_1(cv_b0_1), .c0_1(cv_c0_1),
                .a1_1(cv_a1_1), .b1_1(cv_b1_1), .c1_1(cv_c1_1),
                .a2_1(cv_a2_1), .b2_1(cv_b2_1), .c2_1(cv_c2_1),
                .tri_r1(PREPARED_SCENE ? ar_r1 : tri1_r),
                .tri_g1(PREPARED_SCENE ? ar_g1 : tri1_g),
                .tri_b1(PREPARED_SCENE ? ar_b_1 : tri1_b),
                .step_x(step_x), .step_y(step_y),
                .pixel_r(fixed_priority_r), .pixel_g(fixed_priority_g), .pixel_b(fixed_priority_b),
                .cov0_out(cov0), .cov1_out(cov1),
                .r0_out(r0), .g0_out(g0), .b0_out(b0),
                .r1_out(r1), .g1_out(g1), .b1_out(b1));
            assign cov2 = 1'b0; assign cov3 = 1'b0;
            assign r2 = 0; assign g2 = 0; assign b2 = 0;
            assign r3 = 0; assign g3 = 0; assign b3 = 0;
        end
    endgenerate

    // ── Depth-v2: setup dispatcher + per-pixel accumulators ─────────────
    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire signed [55:0] A_z2, B_z2, C_z2, A_z3, B_z3, C_z3;
    wire [6:0] frac_bits0, frac_bits1, frac_bits2, frac_bits3;
    wire ready0, ready1, ready2, ready3;
    wire candidate_prepare0, candidate_prepare1, candidate_prepare2, candidate_prepare3;
    wire [3:0] candidate_prepare = {candidate_prepare3, candidate_prepare2,
                                     candidate_prepare1, candidate_prepare0};
    wire [3:0] depth_setup = FOUR_SCENE ? candidate_prepare :
                              {2'b00, tri1_setup, tri0_setup};
    wire prepared_ready0, prepared_ready1, prepared_ready2, prepared_ready3;
    wire prepared_generation_matches;
    wire signed [55:0] active_A_z0, active_B_z0, active_C_z0;
    wire signed [55:0] active_A_z1, active_B_z1, active_C_z1;
    wire signed [55:0] active_A_z2, active_B_z2, active_C_z2;
    wire signed [55:0] active_A_z3, active_B_z3, active_C_z3;
    wire [6:0] active_frac_bits0, active_frac_bits1, active_frac_bits2, active_frac_bits3;

    wire signed [63:0] depth_a0_bus = {ca_a0_3, ca_a0_2, ca_a0_1, ca_a0_0};
    wire signed [63:0] depth_b0_bus = {ca_b0_3, ca_b0_2, ca_b0_1, ca_b0_0};
    wire signed [63:0] depth_a1_bus = {ca_a1_3, ca_a1_2, ca_a1_1, ca_a1_0};
    wire signed [63:0] depth_b1_bus = {ca_b1_3, ca_b1_2, ca_b1_1, ca_b1_0};
    wire signed [63:0] depth_a2_bus = {ca_a2_3, ca_a2_2, ca_a2_1, ca_a2_0};
    wire signed [63:0] depth_b2_bus = {ca_b2_3, ca_b2_2, ca_b2_1, ca_b2_0};
    wire signed [127:0] depth_c0_bus = {ca_c0_3, ca_c0_2, ca_c0_1, ca_c0_0};
    wire signed [127:0] depth_c1_bus = {ca_c1_3, ca_c1_2, ca_c1_1, ca_c1_0};
    wire signed [127:0] depth_c2_bus = {ca_c2_3, ca_c2_2, ca_c2_1, ca_c2_0};
    wire [63:0] depth_z0_bus = {ca_z0_3, ca_z0_2, ca_z0_1, ca_z0_0};
    wire [63:0] depth_z1_bus = {ca_z1_3, ca_z1_2, ca_z1_1, ca_z1_0};
    wire [63:0] depth_z2_bus = {ca_z2_3, ca_z2_2, ca_z2_1, ca_z2_0};

    wire [3:0] scalar_ready, scalar_ready_joined;
    wire signed [55:0] fragment_scalar;
    wire fragment_scalar_valid;
    wire [1:0] raster_primitive_id;
    wire raster_primitive_valid;
    wire ready_attr0=scalar_ready[0], ready_attr1=scalar_ready[1];
    wire ready_attr2=scalar_ready[2], ready_attr3=scalar_ready[3];
    spu_prepared_scalar_attribute4 u_t1h_scalar (
        .clk(clk_pixel), .rst_n(rst_n), .enable(T1H_SCALAR != 0), .prepare(candidate_prepare),
        .a0_bus(depth_a0_bus), .b0_bus(depth_b0_bus),
        .a1_bus(depth_a1_bus), .b1_bus(depth_b1_bus),
        .a2_bus(depth_a2_bus), .b2_bus(depth_b2_bus),
        .c0_bus(depth_c0_bus), .c1_bus(depth_c1_bus), .c2_bus(depth_c2_bus),
        .attr0_bus(candidate_attr0_bus), .attr1_bus(candidate_attr1_bus),
        .attr2_bus(candidate_attr2_bus), .depth_ready({ready3,ready2,ready1,ready0}),
        .activate_scene(activate_scene), .frame_start(frame_start),
        .step_x(step_x), .step_y(step_y), .pixel_id(raster_primitive_id),
        .pixel_valid(raster_primitive_valid), .attr_ready(scalar_ready),
        .joined_ready(scalar_ready_joined), .fragment_scalar(fragment_scalar),
        .fragment_scalar_valid(fragment_scalar_valid));

    wire [3:0] uv_u_ready, uv_v_ready;
    wire [3:0] uv_u_joined_ready, uv_v_joined_ready;
    wire [55:0] fragment_u, fragment_v;
    wire fragment_u_valid, fragment_v_valid;
    spu_prepared_scalar_attribute4 u_t1i_u (
        .clk(clk_pixel), .rst_n(rst_n), .enable(T1I_UV != 0), .prepare(candidate_prepare),
        .a0_bus(depth_a0_bus), .b0_bus(depth_b0_bus),
        .a1_bus(depth_a1_bus), .b1_bus(depth_b1_bus),
        .a2_bus(depth_a2_bus), .b2_bus(depth_b2_bus),
        .c0_bus(depth_c0_bus), .c1_bus(depth_c1_bus), .c2_bus(depth_c2_bus),
        .attr0_bus(candidate_u0_bus), .attr1_bus(candidate_u1_bus),
        .attr2_bus(candidate_u2_bus), .depth_ready({ready3,ready2,ready1,ready0}),
        .activate_scene(activate_scene), .frame_start(frame_start),
        .step_x(step_x), .step_y(step_y), .pixel_id(raster_primitive_id),
        .pixel_valid(raster_primitive_valid), .attr_ready(uv_u_ready),
        .joined_ready(uv_u_joined_ready), .fragment_scalar(fragment_u),
        .fragment_scalar_valid(fragment_u_valid));
    spu_prepared_scalar_attribute4 u_t1i_v (
        .clk(clk_pixel), .rst_n(rst_n), .enable(T1I_UV != 0), .prepare(candidate_prepare),
        .a0_bus(depth_a0_bus), .b0_bus(depth_b0_bus),
        .a1_bus(depth_a1_bus), .b1_bus(depth_b1_bus),
        .a2_bus(depth_a2_bus), .b2_bus(depth_b2_bus),
        .c0_bus(depth_c0_bus), .c1_bus(depth_c1_bus), .c2_bus(depth_c2_bus),
        .attr0_bus(candidate_v0_bus), .attr1_bus(candidate_v1_bus),
        .attr2_bus(candidate_v2_bus), .depth_ready({ready3,ready2,ready1,ready0}),
        .activate_scene(activate_scene), .frame_start(frame_start),
        .step_x(step_x), .step_y(step_y), .pixel_id(raster_primitive_id),
        .pixel_valid(raster_primitive_valid), .attr_ready(uv_v_ready),
        .joined_ready(uv_v_joined_ready), .fragment_scalar(fragment_v),
        .fragment_scalar_valid(fragment_v_valid));

    generate
        if (FOUR_SCENE) begin: prepared_depth_control
            spu_depth_dispatch4 u_depth_dispatch4 (.clk(clk_pixel), .rst_n(rst_n),
                .depth_setup(depth_setup), .a0_bus(depth_a0_bus), .b0_bus(depth_b0_bus),
                .a1_bus(depth_a1_bus), .b1_bus(depth_b1_bus), .a2_bus(depth_a2_bus), .b2_bus(depth_b2_bus),
                .c0_bus(depth_c0_bus), .c1_bus(depth_c1_bus), .c2_bus(depth_c2_bus),
                .z0_bus(depth_z0_bus), .z1_bus(depth_z1_bus), .z2_bus(depth_z2_bus),
                .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
                .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1),
                .A_z2(A_z2), .B_z2(B_z2), .C_z2(C_z2), .frac_bits2(frac_bits2), .ready2(ready2),
                .A_z3(A_z3), .B_z3(B_z3), .C_z3(C_z3), .frac_bits3(frac_bits3), .ready3(ready3));
            spu_prepared_scene_control4 u_prepared_control4 (.clk(clk_pixel), .rst_n(rst_n),
                .commit_pending(scene_commit_pending), .frame_start(frame_start),
                .ready(T1H_SCALAR ? scalar_ready_joined :
                    (T1I_UV ? (uv_u_joined_ready & uv_v_joined_ready) :
                              {ready3, ready2, ready1, ready0})),
                .candidate_A0(A_z0), .candidate_B0(B_z0), .candidate_C0(C_z0), .candidate_frac0(frac_bits0),
                .candidate_A1(A_z1), .candidate_B1(B_z1), .candidate_C1(C_z1), .candidate_frac1(frac_bits1),
                .candidate_A2(A_z2), .candidate_B2(B_z2), .candidate_C2(C_z2), .candidate_frac2(frac_bits2),
                .candidate_A3(A_z3), .candidate_B3(B_z3), .candidate_C3(C_z3), .candidate_frac3(frac_bits3),
                .prepare({candidate_prepare3, candidate_prepare2, candidate_prepare1, candidate_prepare0}),
                .activate_scene(activate_scene), .generation_matches(prepared_generation_matches),
                .ready_seen({prepared_ready3, prepared_ready2, prepared_ready1, prepared_ready0}),
                .active_A0(active_A_z0), .active_B0(active_B_z0), .active_C0(active_C_z0), .active_frac0(active_frac_bits0),
                .active_A1(active_A_z1), .active_B1(active_B_z1), .active_C1(active_C_z1), .active_frac1(active_frac_bits1),
                .active_A2(active_A_z2), .active_B2(active_B_z2), .active_C2(active_C_z2), .active_frac2(active_frac_bits2),
                .active_A3(active_A_z3), .active_B3(active_B_z3), .active_C3(active_C_z3), .active_frac3(active_frac_bits3));
        end else begin: direct_depth_control
            spu_depth_dispatch u_depth_dispatch (.clk(clk_pixel), .rst_n(rst_n),
                .depth_setup0(PREPARED_SCENE ? candidate_prepare0 : tri0_setup),
                .depth_setup1(PREPARED_SCENE ? candidate_prepare1 : tri1_setup),
                .a0_0(PREPARED_SCENE ? ca_a0_0 : tri0_a0), .b0_0(PREPARED_SCENE ? ca_b0_0 : tri0_b0),
                .a1_0(PREPARED_SCENE ? ca_a1_0 : tri0_a1), .b1_0(PREPARED_SCENE ? ca_b1_0 : tri0_b1),
                .a2_0(PREPARED_SCENE ? ca_a2_0 : tri0_a2), .b2_0(PREPARED_SCENE ? ca_b2_0 : tri0_b2),
                .c0_0(PREPARED_SCENE ? ca_c0_0 : tri0_c0), .c1_0(PREPARED_SCENE ? ca_c1_0 : tri0_c1), .c2_0(PREPARED_SCENE ? ca_c2_0 : tri0_c2),
                .z0_0(PREPARED_SCENE ? ca_z0_0 : tri0_z0), .z1_0(PREPARED_SCENE ? ca_z1_0 : tri0_z1), .z2_0(PREPARED_SCENE ? ca_z2_0 : tri0_z2),
                .a0_1(PREPARED_SCENE ? ca_a0_1 : tri1_a0), .b0_1(PREPARED_SCENE ? ca_b0_1 : tri1_b0),
                .a1_1(PREPARED_SCENE ? ca_a1_1 : tri1_a1), .b1_1(PREPARED_SCENE ? ca_b1_1 : tri1_b1),
                .a2_1(PREPARED_SCENE ? ca_a2_1 : tri1_a2), .b2_1(PREPARED_SCENE ? ca_b2_1 : tri1_b2),
                .c0_1(PREPARED_SCENE ? ca_c0_1 : tri1_c0), .c1_1(PREPARED_SCENE ? ca_c1_1 : tri1_c1), .c2_1(PREPARED_SCENE ? ca_c2_1 : tri1_c2),
                .z0_1(PREPARED_SCENE ? ca_z0_1 : tri1_z0), .z1_1(PREPARED_SCENE ? ca_z1_1 : tri1_z1), .z2_1(PREPARED_SCENE ? ca_z2_1 : tri1_z2),
                .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
                .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1));
            spu_prepared_scene_control u_prepared_control (.clk(clk_pixel), .rst_n(rst_n),
                .commit_pending(PREPARED_SCENE ? scene_commit_pending : 1'b0), .frame_start(frame_start), .ready0(ready0), .ready1(ready1),
                .candidate_A_z0(A_z0), .candidate_B_z0(B_z0), .candidate_C_z0(C_z0), .candidate_frac_bits0(frac_bits0),
                .candidate_A_z1(A_z1), .candidate_B_z1(B_z1), .candidate_C_z1(C_z1), .candidate_frac_bits1(frac_bits1),
                .prepare0(candidate_prepare0), .prepare1(candidate_prepare1), .activate_scene(activate_scene),
                .ready0_seen(prepared_ready0), .ready1_seen(prepared_ready1),
                .generation_matches(prepared_generation_matches),
                .active_A_z0(active_A_z0), .active_B_z0(active_B_z0), .active_C_z0(active_C_z0), .active_frac_bits0(active_frac_bits0),
                .active_A_z1(active_A_z1), .active_B_z1(active_B_z1), .active_C_z1(active_C_z1), .active_frac_bits1(active_frac_bits1));
            assign A_z2=0; assign B_z2=0; assign C_z2=0; assign frac_bits2=0; assign ready2=0;
            assign A_z3=0; assign B_z3=0; assign C_z3=0; assign frac_bits3=0; assign ready3=0;
            assign candidate_prepare2=0; assign candidate_prepare3=0;
            assign active_A_z2=0; assign active_B_z2=0; assign active_C_z2=0; assign active_frac_bits2=0;
            assign active_A_z3=0; assign active_B_z3=0; assign active_C_z3=0; assign active_frac_bits3=0;
        end
    endgenerate

`ifdef GPU_T1D_DIAG
    assign diag_ready0 = prepared_ready0;
    assign diag_ready1 = prepared_ready1;
    assign diag_generation_matches = prepared_generation_matches;
`endif

    // ── Depth-v2 re-anchor ───────────────────────────────────────────────
    // BUG FIX 2026-09-06. The coverage path above re-anchors at (0,0); the
    // depth path did not, and could not, by re-pulsing the same setup.
    //
    // spu_attr_stepper.v accumulates exactly like spu_edge_stepper.v, so it
    // needs the same per-frame re-anchor. Feeding it `setup0` was impossible
    // -- its coefficients do not exist until spu_depth_dispatch has run the
    // reciprocal -- so it was anchored on `ready0` instead. `setup0` pulsing
    // at (0,0) therefore made `ready0` land WHEREVER the setup latency
    // happened to end: MEASURED at vx=25, vy=0 for unit 0 and vx=48, vy=0
    // for unit 1, the two units 23 pixels apart because spu_depth_dispatch
    // dispatches them sequentially. spu_attr_stepper's `setup` loads
    // acc <= c_coef, the depth AT (0,0), so it declared "I am at x=0" a
    // quarter of a scanline into the frame.
    //
    // The damage is bounded, and the bound was measured, not reasoned:
    // acc_row is re-seeded from the row wrap, so the field self-corrects
    // from row 1 and ONLY row 0 is wrong -- 80/4800 active pixels on the
    // 80x60 bench frame, one full scanline, every frame. The row has TWO
    // error regimes, not one: x=0..23 are the pixels the scan had already
    // passed before the anchor landed, and carry the previous frame's
    // over-accumulated value (measured error +2000, ~10 pixels of A_z);
    // x=24..79 are stepped correctly but from an origin 24 pixels late
    // (measured +4363, ~23 pixels of A_z).
    //
    // Latent, not observed: section 3.9 draws ONE triangle, and with only
    // unit 0 armed spu_depth_compare's unit0_wins reduces to cov0 and never
    // reads a depth. It would have appeared on the first two-triangle scene.
    //
    // The fix is to give the depth path the coverage path's shape rather
    // than a compensating offset. The depth coefficients are a pure function
    // of the triangle, so the math need only run ONCE per triangle -- hence
    // `tri0_setup` below, not `setup0`, which also stops re-running a
    // reciprocal every frame for a result that cannot change. The attribute
    // accumulator is then re-anchored at (0,0) from the latched
    // coefficients, gated by `depth_armed` for the same reason `armed0`
    // gates the coverage re-anchor: a unit whose coefficients have never
    // been computed must not load them.
    //
    // The frame in which a triangle is first set up still anchors mid-row --
    // unavoidable, the coefficients do not exist before then -- so that one
    // frame has one wrong scanline. Every frame after it is exact.
    reg depth_armed0, depth_armed1, depth_armed2, depth_armed3;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            depth_armed0 <= 1'b0;
            depth_armed1 <= 1'b0;
            depth_armed2 <= 1'b0;
            depth_armed3 <= 1'b0;
        end else begin
            if (PREPARED_SCENE ? activate_scene : ready0) depth_armed0 <= 1'b1;
            if (PREPARED_SCENE ? activate_scene : ready1) depth_armed1 <= 1'b1;
            if (FOUR_SCENE && activate_scene) depth_armed2 <= 1'b1;
            if (FOUR_SCENE && activate_scene) depth_armed3 <= 1'b1;
        end
    end

    // The `ready` term is the INITIAL load only, and must stop there. A board
    // top may hold `tri0_setup` asserted or re-pulse it every frame --
    // spu_a7_gpu_vga_top.v wires .tri0_setup(frame_start) and does exactly
    // that -- in which case the dispatcher re-runs and `ready0` pulses again
    // mid-scanline every frame, re-anchoring after the correct frame_start
    // anchor and reinstating the very bug this block removes. MEASURED under
    // that drive pattern with an unguarded `ready0` term: 55 pixels wrong for
    // unit 0 and 32 for unit 1.
    //
    // depth_armed0 is still low on the cycle its own `ready0` is high, so the
    // first pulse arms and anchors; every later one is suppressed and the
    // frame_start term owns the anchor from then on. A triangle whose
    // coefficients change therefore takes effect at the next frame boundary
    // rather than part-way down the screen, which is also what you want.
    wire attr_setup0 = PREPARED_SCENE ?
        (activate_scene | (frame_start & depth_armed0)) :
        ((ready0 & ~depth_armed0) | (frame_start & depth_armed0));
    wire attr_setup1 = PREPARED_SCENE ?
        (activate_scene | (frame_start & depth_armed1)) :
        ((ready1 & ~depth_armed1) | (frame_start & depth_armed1));
    wire attr_setup2 = FOUR_SCENE ?
        (activate_scene | (frame_start & depth_armed2)) : 1'b0;
    wire attr_setup3 = FOUR_SCENE ?
        (activate_scene | (frame_start & depth_armed3)) : 1'b0;

    wire signed [55:0] attr_A_z0 = PREPARED_SCENE ?
        (activate_scene ? A_z0 : active_A_z0) : A_z0;
    wire signed [55:0] attr_B_z0 = PREPARED_SCENE ?
        (activate_scene ? B_z0 : active_B_z0) : B_z0;
    wire signed [55:0] attr_C_z0 = PREPARED_SCENE ?
        (activate_scene ? C_z0 : active_C_z0) : C_z0;
    wire [6:0] attr_frac_bits0 = PREPARED_SCENE ?
        (activate_scene ? frac_bits0 : active_frac_bits0) : frac_bits0;
    wire signed [55:0] attr_A_z1 = PREPARED_SCENE ?
        (activate_scene ? A_z1 : active_A_z1) : A_z1;
    wire signed [55:0] attr_B_z1 = PREPARED_SCENE ?
        (activate_scene ? B_z1 : active_B_z1) : B_z1;
    wire signed [55:0] attr_C_z1 = PREPARED_SCENE ?
        (activate_scene ? C_z1 : active_C_z1) : C_z1;
    wire [6:0] attr_frac_bits1 = PREPARED_SCENE ?
        (activate_scene ? frac_bits1 : active_frac_bits1) : frac_bits1;
    wire signed [55:0] attr_A_z2 = activate_scene ? A_z2 : active_A_z2;
    wire signed [55:0] attr_B_z2 = activate_scene ? B_z2 : active_B_z2;
    wire signed [55:0] attr_C_z2 = activate_scene ? C_z2 : active_C_z2;
    wire [6:0] attr_frac_bits2 = activate_scene ? frac_bits2 : active_frac_bits2;
    wire signed [55:0] attr_A_z3 = activate_scene ? A_z3 : active_A_z3;
    wire signed [55:0] attr_B_z3 = activate_scene ? B_z3 : active_B_z3;
    wire signed [55:0] attr_C_z3 = activate_scene ? C_z3 : active_C_z3;
    wire [6:0] attr_frac_bits3 = activate_scene ? frac_bits3 : active_frac_bits3;

    wire signed [55:0] depth0, depth1, depth2, depth3;
    spu_attr_stepper u_attr0 (.clk(clk_pixel), .rst_n(rst_n), .setup(attr_setup0),
        .a_coef(attr_A_z0), .b_coef(attr_B_z0), .c_coef(attr_C_z0),
        .step_x(step_x), .step_y(step_y), .frac_bits(attr_frac_bits0),
        .value_out(depth0));
    spu_attr_stepper u_attr1 (.clk(clk_pixel), .rst_n(rst_n), .setup(attr_setup1),
        .a_coef(attr_A_z1), .b_coef(attr_B_z1), .c_coef(attr_C_z1),
        .step_x(step_x), .step_y(step_y), .frac_bits(attr_frac_bits1),
        .value_out(depth1));

    generate
        if (FOUR_SCENE) begin: prepared_depth_steppers
            spu_attr_stepper u_attr2 (.clk(clk_pixel), .rst_n(rst_n), .setup(attr_setup2),
                .a_coef(attr_A_z2), .b_coef(attr_B_z2), .c_coef(attr_C_z2),
                .step_x(step_x), .step_y(step_y), .frac_bits(attr_frac_bits2),
                .value_out(depth2));
            spu_attr_stepper u_attr3 (.clk(clk_pixel), .rst_n(rst_n), .setup(attr_setup3),
                .a_coef(attr_A_z3), .b_coef(attr_B_z3), .c_coef(attr_C_z3),
                .step_x(step_x), .step_y(step_y), .frac_bits(attr_frac_bits3),
                .value_out(depth3));
        end else begin: direct_depth_steppers
            assign depth2 = 0;
            assign depth3 = 0;
        end
    endgenerate

    // ── Real depth-aware pixel selection (replaces spu_dual_raster's
    // fixed-priority pixel_r/g/b, which remains available above,
    // unused, for any consumer that wants coverage-only priority) ──────
    wire [3:0] rast_r, rast_g, rast_b;
    wire [3:0] display_r, display_g, display_b;
    wire display_hsync, display_vsync, display_active;
    // A unit that has never been set up must not cover anything. Its edge
    // accumulators reset to 0 and `inside` is (f >= 0), so all three edges
    // report inside and the unit claims EVERY pixel. Until now that was
    // masked by unit 0 winning wherever it was covered, and by unit 1's
    // colour happening to be zero -- a non-zero tri1_r with no tri1_setup
    // would have filled the screen.
    wire cov0_armed = cov0 & armed0;
    wire cov1_armed = cov1 & armed1;
    wire cov2_armed = cov2 & armed2;
    wire cov3_armed = cov3 & armed3;

    generate
        if (FOUR_SCENE) begin: prepared_depth_reduction
            spu_depth_compare4 u_depth_compare4 (
                .cov0(cov0_armed), .cov1(cov1_armed), .cov2(cov2_armed), .cov3(cov3_armed),
                .depth0(depth0), .depth1(depth1), .depth2(depth2), .depth3(depth3),
                .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
                .r2(r2), .g2(g2), .b2(b2), .r3(r3), .g3(g3), .b3(b3),
                .pixel_r(rast_r), .pixel_g(rast_g), .pixel_b(rast_b),
                .pixel_id(raster_primitive_id), .pixel_valid(raster_primitive_valid));
        end else begin: direct_depth_reduction
            spu_depth_compare u_depth_compare (
                .cov0(cov0_armed), .cov1(cov1_armed), .depth0(depth0), .depth1(depth1),
                .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
                .pixel_r(rast_r), .pixel_g(rast_g), .pixel_b(rast_b));
            assign raster_primitive_id=0;
            assign raster_primitive_valid=0;
        end
    endgenerate

    wire any_armed_coverage = cov0_armed | cov1_armed | cov2_armed | cov3_armed;
    wire [3:0] winner_diag_r = {4{raster_primitive_valid && (~^raster_primitive_id)}};
    wire [3:0] winner_diag_g = {4{raster_primitive_valid && raster_primitive_id[0]}};
    wire [3:0] winner_diag_b = {4{raster_primitive_valid && raster_primitive_id[1] &&
                                      !raster_primitive_id[0]}};
    reg t1i_depth_valid_q;
    reg [1:0] t1i_depth_id_q;
    reg [3:0] t1i_depth_r_q, t1i_depth_g_q, t1i_depth_b_q;
    reg t1i_depth_hsync_q, t1i_depth_vsync_q, t1i_depth_active_q;
    reg signed [55:0] t1i_uv_u_q, t1i_uv_v_q;
    reg t1i_uv_valid_q, t1i_uv_hsync_q, t1i_uv_vsync_q, t1i_uv_active_q;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            t1i_depth_valid_q <= 1'b0;
            t1i_depth_id_q <= 2'd0;
            t1i_depth_r_q <= 4'd0; t1i_depth_g_q <= 4'd0; t1i_depth_b_q <= 4'd0;
            t1i_depth_hsync_q <= 1'b0; t1i_depth_vsync_q <= 1'b0; t1i_depth_active_q <= 1'b0;
            t1i_uv_u_q <= 56'sd0; t1i_uv_v_q <= 56'sd0;
            t1i_uv_valid_q <= 1'b0;
            t1i_uv_hsync_q <= 1'b0; t1i_uv_vsync_q <= 1'b0; t1i_uv_active_q <= 1'b0;
        end else begin
            t1i_depth_valid_q <= raster_primitive_valid;
            t1i_depth_id_q <= raster_primitive_id;
            t1i_depth_r_q <= winner_diag_r;
            t1i_depth_g_q <= winner_diag_g;
            t1i_depth_b_q <= winner_diag_b;
            t1i_depth_hsync_q <= hsync_d;
            t1i_depth_vsync_q <= vsync_d;
            t1i_depth_active_q <= active_d;
            t1i_uv_u_q <= fragment_u;
            t1i_uv_v_q <= fragment_v;
            t1i_uv_valid_q <= fragment_u_valid && fragment_v_valid;
            t1i_uv_hsync_q <= hsync_d;
            t1i_uv_vsync_q <= vsync_d;
            t1i_uv_active_q <= active_d;
        end
    end

    generate
        if (T1I_UV_REG_DIAG) begin: t1i_uv_registered_visualization
            wire [3:0] registered_uv_red = {4{t1i_uv_valid_q && t1i_uv_u_q[14]}};
            wire [3:0] registered_uv_green = {4{t1i_uv_valid_q && t1i_uv_v_q[14]}};
            assign display_r = registered_uv_red;
            assign display_g = registered_uv_green;
            assign display_b = 4'b0000;
            assign display_hsync = t1i_uv_hsync_q;
            assign display_vsync = t1i_uv_vsync_q;
            assign display_active = t1i_uv_active_q;
        end else if (T1I_DEPTH_DIAG == 3) begin: t1i_depth_registered_visualization
            assign display_r = t1i_depth_valid_q ? t1i_depth_r_q : 4'd0;
            assign display_g = t1i_depth_valid_q ? t1i_depth_g_q : 4'd0;
            assign display_b = t1i_depth_valid_q ? t1i_depth_b_q : 4'd0;
            assign display_hsync = t1i_depth_hsync_q;
            assign display_vsync = t1i_depth_vsync_q;
            assign display_active = t1i_depth_active_q;
        end else begin: t1i_unregistered_visualization
            assign display_hsync = hsync_d;
            assign display_vsync = vsync_d;
            assign display_active = active_d;
            if (T1I_DEPTH_DIAG == 1) begin: coverage_only
                wire [3:0] coverage_white = {4{any_armed_coverage}};
                assign display_r = coverage_white;
                assign display_g = coverage_white;
                assign display_b = coverage_white;
            end else if (T1I_DEPTH_DIAG == 2) begin: winner_id_colour
                assign display_r = winner_diag_r;
                assign display_g = winner_diag_g;
                assign display_b = winner_diag_b;
            end else if (T1H_SCALAR_DIAG) begin: t1h_scalar_visualization
            wire [3:0] scalar_gray = fragment_scalar_valid ? fragment_scalar[14:11] : 4'h0;
            assign display_r = scalar_gray;
            assign display_g = scalar_gray;
            assign display_b = scalar_gray;
            end else if (T1I_UV_DIAG) begin: t1i_uv_visualization
                wire selected_uv_valid = fragment_u_valid && fragment_v_valid;
                wire [3:0] uv_red = {4{selected_uv_valid && fragment_u[14]}};
                wire [3:0] uv_green = {4{selected_uv_valid && fragment_v[14]}};
                assign display_r = uv_red;
                assign display_g = uv_green;
                assign display_b = 4'b0000;
            end else begin: normal_scene_visualization
                assign display_r = rast_r;
                assign display_g = rast_g;
                assign display_b = rast_b;
            end
        end
    endgenerate

    wire [3:0] video_r, video_g, video_b;
    wire video_hsync, video_vsync, video_active;
    generate
        if (GPU_POST_WINNER_REG) begin: post_winner_output_register
            spu_pixel_output_register u_pixel_output_register (
                .clk_pixel(clk_pixel), .rst_n(rst_n),
                .rgb_r_in(display_r), .rgb_g_in(display_g), .rgb_b_in(display_b),
                .hsync_in(display_hsync), .vsync_in(display_vsync),
                .active_in(display_active),
                .rgb_r_out(video_r), .rgb_g_out(video_g), .rgb_b_out(video_b),
                .hsync_out(video_hsync), .vsync_out(video_vsync),
                .active_out(video_active));
        end else begin: direct_pixel_output
            assign video_r=display_r; assign video_g=display_g; assign video_b=display_b;
            assign video_hsync=display_hsync; assign video_vsync=display_vsync;
            assign video_active=display_active;
        end
    endgenerate

    // ── hal_vga ── (base sync delay plus optional post-winner stage) ──
    hal_vga u_vga (.r(video_r), .g(video_g), .b(video_b),
        .hsync(video_hsync), .vsync(video_vsync), .active(video_active),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync));

    // Elaboration-time guard: an unset or misspelled DEVICE fails here with a
    // readable module name rather than deep inside a vendor primitive.
    generate
        if (DEVICE != "GW5A" && DEVICE != "A7" && DEVICE != "XILINX") begin: bad_device
            spu_gpu_top_DEVICE_must_be_GW5A_or_A7_or_XILINX u_unset_device ();
        end
    endgenerate

    // ── hal_hdmi ─────────────────────────────────────────────────────────
    generate
        if (ENABLE_HDMI) begin: hdmi_out
            hal_hdmi #(.DEVICE(DEVICE)) u_hdmi (.clk_pixel(clk_pixel), .clk_tmds(clk_tmds), .rst_n(rst_n),
                .r({video_r, 4'h0}), .g({video_g, 4'h0}), .b({video_b, 4'h0}),
                .hsync(video_hsync), .vsync(video_vsync), .active(video_active),
                .tmds_clk_p(tmds_clk_p), .tmds_clk_n(tmds_clk_n),
                .tmds_d_p(tmds_d_p), .tmds_d_n(tmds_d_n));
        end else begin: no_hdmi
            // VGA-only build: no differential primitive is instantiated at
            // all, so nothing for the openXC7 placer to trip over. clk_tmds
            // is unused in this configuration.
            assign tmds_clk_p = 1'b0;
            assign tmds_clk_n = 1'b0;
            assign tmds_d_p   = 3'b000;
            assign tmds_d_n   = 3'b000;
        end
    endgenerate

endmodule
