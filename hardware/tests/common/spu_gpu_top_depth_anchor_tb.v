// spu_gpu_top_depth_anchor_tb.v — the first testbench to read a depth value
// out of spu_gpu_top. Covers the depth-v2 frame re-anchor fixed 2026-09-06.
//
// THE BUG. spu_attr_stepper.v accumulates exactly like spu_edge_stepper.v, so
// it needs the same per-frame re-anchor the coverage path got on 2026-09-05.
// It could not be given the same `setup0` pulse -- its coefficients do not
// exist until spu_depth_dispatch.v has run a reciprocal -- so it was anchored
// on `ready0` instead. `setup0` pulsing at (0,0) therefore made `ready0` land
// wherever the setup latency happened to end: MEASURED at vx=25, vy=0 for
// unit 0 and vx=48, vy=0 for unit 1, the two 23 pixels apart because
// spu_depth_dispatch dispatches them sequentially. spu_attr_stepper's `setup`
// loads acc <= c_coef, the depth AT (0,0), so it declared "I am at x=0" a
// quarter of a scanline in.
//
// acc_row is re-seeded from the row wrap, so the field self-corrects from
// row 1: exactly row 0 was wrong, all of it, every frame.
//
// WHY NOTHING CAUGHT IT. spu_gpu_top_frame_anchor_tb.v arms ONE triangle, and
// spu_depth_compare's unit0_wins reduces to cov0 when cov1 is low -- it never
// reads a depth. Section 3.9's silicon result is the same single-triangle
// scene. The defect was latent, not observed, and would have appeared on the
// first two-triangle scene.
//
// FALSIFICATION. Both units armed, both with depth sloped in x AND y, and
// every active pixel of a steady-state frame checked against the affine
// oracle z(x,y) = (C_z + x*A_z + y*B_z) >>> frac_bits. Run against the
// pre-fix RTL this reports 80/4800 wrong for unit 0 and 80/4800 for unit 1 --
// one full scanline each -- and FAILS. A bench that only passes proves
// nothing.
//
// SCOPE, stated so it is not overread. The oracle is built from the DUT's own
// A_z/B_z/C_z/frac_bits, so this checks that the per-pixel accumulator is
// anchored and stepped consistently with the coefficients the setup stage
// produced. It does NOT check that those coefficients are the right ones --
// spu_depth_math.v's arithmetic has no bench of its own and this is not it.
//
// CC0 1.0 Universal.

`timescale 1ns/1ps

module spu_gpu_top_depth_anchor_tb;

    // Small frame, same reasoning as spu_gpu_top_frame_anchor_tb.v: the
    // anchoring behaviour is a property of the update rule, not of the frame
    // size, and 640x480 does not fit the harness's 15 s limit.
    localparam H_ACTIVE = 80, H_FP = 4, H_SYNC = 8, H_BP = 8;   // H_TOTAL 100
    localparam V_ACTIVE = 60, V_FP = 2, V_SYNC = 2, V_BP = 6;   // V_TOTAL  70

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    always #1 clk = ~clk;

    // Same triangle as the frame-anchor bench: V0(40,12) V1(18,47) V2(62,47).
    localparam signed [15:0] E0_A = 16'sd35,  E0_B = 16'sd22;
    localparam signed [31:0] E0_C = -32'sd1664;
    localparam signed [15:0] E1_A = 16'sd0,   E1_B = -16'sd44;
    localparam signed [31:0] E1_C = 32'sd2068;
    localparam signed [15:0] E2_A = -16'sd35, E2_B = 16'sd22;
    localparam signed [31:0] E2_C = 32'sd1136;

    reg tri0_setup = 1'b0, tri1_setup = 1'b0;
    wire [3:0] vga_r, vga_g, vga_b;
    wire vga_hsync, vga_vsync;

    // Both units get the SAME triangle so both cover the same pixels and the
    // depth comparison is what decides every interior pixel -- the situation
    // the single-triangle benches cannot create. Distinct per-vertex z, so
    // both A_z and B_z are non-zero for both units (asserted below).
    spu_gpu_top #(
        .DEVICE("A7"), .ENABLE_HDMI(0),
        .H_ACTIVE(H_ACTIVE), .H_FP(H_FP), .H_SYNC(H_SYNC), .H_BP(H_BP),
        .V_ACTIVE(V_ACTIVE), .V_FP(V_FP), .V_SYNC(V_SYNC), .V_BP(V_BP)
    ) dut (
        .clk_pixel(clk), .clk_tmds(clk), .rst_n(rst_n),
        .tri0_setup(tri0_setup),
        .tri0_a0(E0_A), .tri0_b0(E0_B), .tri0_c0(E0_C),
        .tri0_a1(E1_A), .tri0_b1(E1_B), .tri0_c1(E1_C),
        .tri0_a2(E2_A), .tri0_b2(E2_B), .tri0_c2(E2_C),
        .tri0_r(4'hF), .tri0_g(4'h0), .tri0_b(4'h0),
        .tri0_z0(16'd1000), .tri0_z1(16'd4000), .tri0_z2(16'd9000),
        .tri1_setup(tri1_setup),
        .tri1_a0(E0_A), .tri1_b0(E0_B), .tri1_c0(E0_C),
        .tri1_a1(E1_A), .tri1_b1(E1_B), .tri1_c1(E1_C),
        .tri1_a2(E2_A), .tri1_b2(E2_B), .tri1_c2(E2_C),
        .tri1_r(4'h0), .tri1_g(4'hF), .tri1_b(4'h0),
        .tri1_z0(16'd9000), .tri1_z1(16'd4000), .tri1_z2(16'd1000),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync),
        .tmds_clk_p(), .tmds_clk_n(), .tmds_d_p(), .tmds_d_n());

    integer x, y;
    integer bad0 = 0, bad1 = 0, checked = 0;
    integer errors = 0;
    integer shown = 0;
    integer exp0, exp1;

    task align_to_frame_start;
        begin
            while (!(dut.vx == 10'd0 && dut.vy == 10'd0)) @(posedge clk);
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (4) @(posedge clk);

        // One setup for both units, then let two whole frames pass so the
        // measured frame is steady state and not the setup transient (the
        // frame a triangle is first set up in still anchors mid-row -- the
        // coefficients do not exist before then -- and that is by design).
        align_to_frame_start;
        @(negedge clk); tri0_setup = 1'b1; tri1_setup = 1'b1;
        @(negedge clk); tri0_setup = 1'b0; tri1_setup = 1'b0;
        repeat (2) begin align_to_frame_start; @(posedge clk); end
        align_to_frame_start;

        // ── Vacuous-pass guards ──────────────────────────────────────────
        // A constant depth field matches any anchor, so it would pass this
        // bench on the broken RTL. Both gradients must be real, and both
        // units must actually be armed.
        if (dut.A_z0 === 56'sd0 || dut.B_z0 === 56'sd0 ||
            dut.A_z1 === 56'sd0 || dut.B_z1 === 56'sd0) begin
            $display("FAIL: a depth gradient is zero (A_z0=%0d B_z0=%0d A_z1=%0d B_z1=%0d)",
                     dut.A_z0, dut.B_z0, dut.A_z1, dut.B_z1);
            $display("      the field would not vary with position and this bench");
            $display("      could not distinguish a correct anchor from any other");
            errors = errors + 1;
        end
        if (!dut.depth_armed0 || !dut.depth_armed1) begin
            $display("FAIL: depth_armed0=%b depth_armed1=%b -- a unit never completed setup",
                     dut.depth_armed0, dut.depth_armed1);
            errors = errors + 1;
        end

        // ── The measurement ──────────────────────────────────────────────
        for (y = 0; y < V_ACTIVE; y = y + 1) begin
            for (x = 0; x < H_ACTIVE; x = x + 1) begin
                @(posedge clk);
                exp0 = ($signed(dut.C_z0) + x * $signed(dut.A_z0)
                                          + y * $signed(dut.B_z0)) >>> dut.frac_bits0;
                exp1 = ($signed(dut.C_z1) + x * $signed(dut.A_z1)
                                          + y * $signed(dut.B_z1)) >>> dut.frac_bits1;
                checked = checked + 1;
                if ($signed(dut.depth0) !== exp0) begin
                    bad0 = bad0 + 1;
                    if (shown < 4) begin
                        $display("  unit0 (%0d,%0d): depth %0d, expected %0d",
                                 x, y, $signed(dut.depth0), exp0);
                        shown = shown + 1;
                    end
                end
                if ($signed(dut.depth1) !== exp1) begin
                    bad1 = bad1 + 1;
                    if (shown < 8) begin
                        $display("  unit1 (%0d,%0d): depth %0d, expected %0d",
                                 x, y, $signed(dut.depth1), exp1);
                        shown = shown + 1;
                    end
                end
            end
            while (dut.vx != 10'd0) @(posedge clk);   // skip blanking
        end

        $display("checked %0d active pixels: unit0 %0d wrong, unit1 %0d wrong",
                 checked, bad0, bad1);

        if (checked != H_ACTIVE * V_ACTIVE) begin
            $display("FAIL: checked %0d pixels, expected %0d", checked, H_ACTIVE * V_ACTIVE);
            errors = errors + 1;
        end
        if (bad0 != 0) begin
            $display("FAIL: unit 0 depth field is not anchored at (0,0) -- %0d pixels wrong", bad0);
            errors = errors + 1;
        end
        if (bad1 != 0) begin
            $display("FAIL: unit 1 depth field is not anchored at (0,0) -- %0d pixels wrong", bad1);
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: both depth fields anchored at (0,0) across %0d active pixels", checked);
        else
            $display("FAILED with %0d error(s)", errors);
        $finish;
    end

endmodule
