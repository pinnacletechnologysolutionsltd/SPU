// spu_gpu_top_frame_anchor_tb.v — the first testbench to instantiate
// spu_gpu_top. Covers the frame-start re-anchor fixed 2026-09-05.
//
// THE BUG. step_y is derived from the horizontal wrap alone, so it fires on
// all 525 lines of a frame while only 480 are displayed, and nothing
// re-anchored the edge accumulators after `setup`. f_row reached C + 525*B
// at the start of the next frame instead of returning to C, so a triangle set
// up once walked 525*B every frame -- measured as a constant 89250 = 525*170
// step in f_row on the pre-fix RTL.
//
// FALSIFICATION. This bench renders the SAME static triangle across three
// consecutive frames and requires the coverage bitmap to be IDENTICAL each
// time. That is exactly what drift breaks and nothing else plausibly does.
// It was run against the pre-fix RTL and FAILS there -- see the recorded
// counts in the commit message. A bench that only passes proves nothing.
//
// CC0 1.0 Universal.

`timescale 1ns/1ps

module spu_gpu_top_frame_anchor_tb;

    localparam H_TOTAL = 800;
    localparam V_TOTAL = 525;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    always #1 clk = ~clk;

    // Triangle V0(320,100) V1(150,380) V2(490,380); +95200 at each opposite
    // vertex, so the winding is consistent and the interior is well defined.
    localparam signed [15:0] E0_A = 16'sd280,  E0_B = 16'sd170;
    localparam signed [31:0] E0_C = -32'sd106600;
    localparam signed [15:0] E1_A = 16'sd0,    E1_B = -16'sd340;
    localparam signed [31:0] E1_C = 32'sd129200;
    localparam signed [15:0] E2_A = -16'sd280, E2_B = 16'sd170;
    localparam signed [31:0] E2_C = 32'sd72600;

    reg tri0_setup = 1'b0;
    wire [3:0] vga_r, vga_g, vga_b;
    wire vga_hsync, vga_vsync;

    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0)) dut (
        .clk_pixel(clk), .clk_tmds(clk), .rst_n(rst_n),
        .tri0_setup(tri0_setup),
        .tri0_a0(E0_A), .tri0_b0(E0_B), .tri0_c0(E0_C),
        .tri0_a1(E1_A), .tri0_b1(E1_B), .tri0_c1(E1_C),
        .tri0_a2(E2_A), .tri0_b2(E2_B), .tri0_c2(E2_C),
        .tri0_r(4'hF), .tri0_g(4'h0), .tri0_b(4'h0),
        .tri0_z0(16'd1000), .tri0_z1(16'd1000), .tri0_z2(16'd1000),
        .tri1_setup(1'b0),
        .tri1_a0(16'sd0), .tri1_b0(16'sd0), .tri1_c0(32'sd0),
        .tri1_a1(16'sd0), .tri1_b1(16'sd0), .tri1_c1(32'sd0),
        .tri1_a2(16'sd0), .tri1_b2(16'sd0), .tri1_c2(32'sd0),
        .tri1_r(4'h0), .tri1_g(4'h0), .tri1_b(4'h0),
        .tri1_z0(16'd0), .tri1_z1(16'd0), .tri1_z2(16'd0),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync),
        .tmds_clk_p(), .tmds_clk_n(), .tmds_d_p(), .tmds_d_n());

    // Per-frame signature of the rendered image: how many pixels were lit,
    // and a position-weighted checksum so that a shape of equal area at a
    // different place is still caught.
    integer lit [0:2];
    integer csum [0:2];
    integer frame, i;
    integer errors = 0;

    // Mirror of the display counters, purely for observation.
    integer px = 0, py = 0;

    task run_one_frame(input integer slot);
        integer p;
        begin
            lit[slot]  = 0;
            csum[slot] = 0;
            for (p = 0; p < H_TOTAL * V_TOTAL; p = p + 1) begin
                @(posedge clk);
                if (vga_r != 4'h0) begin
                    lit[slot]  = lit[slot] + 1;
                    csum[slot] = csum[slot] + px + (py * 7);
                end
                if (px == H_TOTAL - 1) begin
                    px = 0;
                    py = (py == V_TOTAL - 1) ? 0 : py + 1;
                end else
                    px = px + 1;
            end
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (4) @(posedge clk);

        // Align to a frame boundary, then set the triangle up once -- the
        // whole point is that ONE setup must survive many frames.
        while (!(dut.vx == 10'd0 && dut.vy == 10'd0)) @(posedge clk);
        @(negedge clk); tri0_setup = 1'b1;
        @(negedge clk); tri0_setup = 1'b0;

        // Discard the remainder of the setup frame, then measure three.
        while (!(dut.vx == 10'd0 && dut.vy == 10'd0)) @(posedge clk);
        px = 0; py = 0;

        for (frame = 0; frame < 3; frame = frame + 1)
            run_one_frame(frame);

        $display("frame 0: lit=%0d csum=%0d", lit[0], csum[0]);
        $display("frame 1: lit=%0d csum=%0d", lit[1], csum[1]);
        $display("frame 2: lit=%0d csum=%0d", lit[2], csum[2]);

        // A triangle must actually be drawn, or "identical" is vacuous.
        if (lit[0] < 1000) begin
            $display("FAIL: frame 0 lit %0d pixels, expected a triangle of thousands", lit[0]);
            errors = errors + 1;
        end

        for (i = 1; i < 3; i = i + 1) begin
            if (lit[i] != lit[0]) begin
                $display("FAIL: frame %0d lit %0d, frame 0 lit %0d -- area drifted",
                         i, lit[i], lit[0]);
                errors = errors + 1;
            end
            if (csum[i] != csum[0]) begin
                $display("FAIL: frame %0d csum %0d, frame 0 csum %0d -- position drifted",
                         i, csum[i], csum[0]);
                errors = errors + 1;
            end
        end

        if (errors == 0)
            $display("PASS: 3 frames identical from a single setup (lit=%0d)", lit[0]);
        else
            $display("FAILED with %0d error(s)", errors);
        $finish;
    end

endmodule
