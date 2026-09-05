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
    // ENABLE_HDMI=0 omits hal_hdmi entirely and ties the TMDS outputs low.
    // Required on openXC7/nextpnr-xilinx, whose placer HANGS on differential
    // output (OBUFDS/TMDS_33) -- upstream issue #66, open and unimplemented,
    // so a toolchain rebuild will not fix it. Default 1 preserves the
    // pre-existing behaviour for the Gowin path and for any Vivado flow.
    parameter ENABLE_HDMI = 1
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

    // VGA PMOD outputs
    output wire [3:0]  vga_r, vga_g, vga_b,
    output wire        vga_hsync, vga_vsync,

    // HDMI differential outputs
    output wire        tmds_clk_p, tmds_clk_n,
    output wire [2:0]  tmds_d_p, tmds_d_n
);

    // ── Video timing ─────────────────────────────────────────────────────
    wire [9:0] vx, vy;
    wire hsync, vsync, active;
    wire step_x;
    assign step_x = active;
    wire step_y;  // one cycle after hsync falling (end of line)

    spu_video_timing u_timing (.clk(clk_pixel), .rst_n(rst_n),
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

    reg armed0, armed1;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            armed0 <= 1'b0;
            armed1 <= 1'b0;
        end else begin
            if (tri0_setup) armed0 <= 1'b1;
            if (tri1_setup) armed1 <= 1'b1;
        end
    end

    wire setup0 = tri0_setup | (frame_start & armed0);
    wire setup1 = tri1_setup | (frame_start & armed1);

    // ── Dual rasterizer (coverage) ──────────────────────────────────────
    wire [3:0] fixed_priority_r, fixed_priority_g, fixed_priority_b;  // unused
    wire cov0, cov1;
    wire [3:0] r0, g0, b0, r1, g1, b1;

    spu_dual_raster u_rast (.clk(clk_pixel), .rst_n(rst_n),
        .setup0(setup0),
        .a0_0(tri0_a0), .b0_0(tri0_b0), .c0_0(tri0_c0),
        .a1_0(tri0_a1), .b1_0(tri0_b1), .c1_0(tri0_c1),
        .a2_0(tri0_a2), .b2_0(tri0_b2), .c2_0(tri0_c2),
        .tri_r0(tri0_r), .tri_g0(tri0_g), .tri_b0(tri0_b),
        .setup1(setup1),
        .a0_1(tri1_a0), .b0_1(tri1_b0), .c0_1(tri1_c0),
        .a1_1(tri1_a1), .b1_1(tri1_b1), .c1_1(tri1_c1),
        .a2_1(tri1_a2), .b2_1(tri1_b2), .c2_1(tri1_c2),
        .tri_r1(tri1_r), .tri_g1(tri1_g), .tri_b1(tri1_b),
        .step_x(step_x), .step_y(step_y), .x_span(10'd640),
        .pixel_r(fixed_priority_r), .pixel_g(fixed_priority_g), .pixel_b(fixed_priority_b),
        .cov0_out(cov0), .cov1_out(cov1),
        .r0_out(r0), .g0_out(g0), .b0_out(b0),
        .r1_out(r1), .g1_out(g1), .b1_out(b1));

    // ── Depth-v2: setup dispatcher + two per-pixel accumulators ─────────
    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire [6:0] frac_bits0, frac_bits1;
    wire ready0, ready1;

    spu_depth_dispatch u_depth_dispatch (.clk(clk_pixel), .rst_n(rst_n),
        .depth_setup0(setup0), .depth_setup1(setup1),
        .a0_0(tri0_a0), .b0_0(tri0_b0), .a1_0(tri0_a1), .b1_0(tri0_b1),
        .a2_0(tri0_a2), .b2_0(tri0_b2),
        .c0_0(tri0_c0), .c1_0(tri0_c1), .c2_0(tri0_c2),
        .z0_0(tri0_z0), .z1_0(tri0_z1), .z2_0(tri0_z2),
        .a0_1(tri1_a0), .b0_1(tri1_b0), .a1_1(tri1_a1), .b1_1(tri1_b1),
        .a2_1(tri1_a2), .b2_1(tri1_b2),
        .c0_1(tri1_c0), .c1_1(tri1_c1), .c2_1(tri1_c2),
        .z0_1(tri1_z0), .z1_1(tri1_z1), .z2_1(tri1_z2),
        .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
        .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1));

    wire signed [55:0] depth0, depth1;
    spu_attr_stepper u_attr0 (.clk(clk_pixel), .rst_n(rst_n), .setup(ready0),
        .a_coef(A_z0), .b_coef(B_z0), .c_coef(C_z0),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits0),
        .value_out(depth0));
    spu_attr_stepper u_attr1 (.clk(clk_pixel), .rst_n(rst_n), .setup(ready1),
        .a_coef(A_z1), .b_coef(B_z1), .c_coef(C_z1),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits1),
        .value_out(depth1));

    // ── Real depth-aware pixel selection (replaces spu_dual_raster's
    // fixed-priority pixel_r/g/b, which remains available above,
    // unused, for any consumer that wants coverage-only priority) ──────
    wire [3:0] rast_r, rast_g, rast_b;
    // A unit that has never been set up must not cover anything. Its edge
    // accumulators reset to 0 and `inside` is (f >= 0), so all three edges
    // report inside and the unit claims EVERY pixel. Until now that was
    // masked by unit 0 winning wherever it was covered, and by unit 1's
    // colour happening to be zero -- a non-zero tri1_r with no tri1_setup
    // would have filled the screen.
    wire cov0_armed = cov0 & armed0;
    wire cov1_armed = cov1 & armed1;

    spu_depth_compare u_depth_compare (
        .cov0(cov0_armed), .cov1(cov1_armed), .depth0(depth0), .depth1(depth1),
        .r0(r0), .g0(g0), .b0(b0), .r1(r1), .g1(g1), .b1(b1),
        .pixel_r(rast_r), .pixel_g(rast_g), .pixel_b(rast_b));

    // ── hal_vga ── (hsync_d/vsync_d/active_d: see the delay note above) ──
    hal_vga u_vga (.r(rast_r), .g(rast_g), .b(rast_b),
        .hsync(hsync_d), .vsync(vsync_d), .active(active_d),
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
                .r({rast_r, 4'h0}), .g({rast_g, 4'h0}), .b({rast_b, 4'h0}),
                .hsync(hsync_d), .vsync(vsync_d), .active(active_d),
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
