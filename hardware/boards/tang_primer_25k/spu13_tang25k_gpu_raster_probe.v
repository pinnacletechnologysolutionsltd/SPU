// spu13_tang25k_gpu_raster_probe.v — GPU rasterizer coverage-path area probe
//
// Synthesis/place-route AREA MEASUREMENT ONLY. No UART, no functional
// PASS/FAIL self-test (the rasterizer's functional correctness is already
// testbench-verified, see hardware/tests/spu_raster_tb.v, 2026-08-24).
// This probe exists solely to answer "how many Tang 25K LUT4 does the
// coverage path (spu_edge_stepper + spu_raster_unit + spu_dual_raster,
// driven by real spu_video_timing scan) cost" -- see
// spu_strategy/contract_gpu_raster_synth_probe_2026-08-25.md.
//
// Deliberately excludes spu_gpu_top.v's HDMI/TMDS HAL and PLL -- unrelated
// cost center that would confound this measurement.
//
// Edge coefficients are derived from free-running counters (not literals)
// so Yosys cannot constant-fold the accumulators away and under-report
// LUT usage. Pixel output is folded into led[2:0] every cycle to keep the
// whole datapath live from setup input to a real output pin.

module spu13_tang25k_gpu_raster_probe (
    input  wire       sys_clk,
    output wire [2:0] led
);

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

    // ── Video timing drives the scan (real module, real usage shape) ──
    wire [9:0] vx, vy;
    wire hsync, vsync, active;
    spu_video_timing u_timing (.clk(sys_clk), .rst_n(rst_n),
        .x(vx), .y(vy), .hsync(hsync), .vsync(vsync), .active(active));

    wire step_x = active;
    reg [9:0] vx_d;
    always @(posedge sys_clk) vx_d <= vx;
    wire step_y = (vx == 10'd0) && (vx_d != 10'd0);

    reg vsync_d = 1'b1;
    always @(posedge sys_clk) vsync_d <= vsync;
    wire frame_tick = (vsync == 1'b0) && (vsync_d == 1'b1);

    // ── Non-constant coefficient source (two free-running counters) ───
    reg [31:0] ctr_a, ctr_b;
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            ctr_a <= 32'h0000_0001;
            ctr_b <= 32'h8000_0001;
        end else if (frame_tick) begin
            ctr_a <= ctr_a + 32'h9E37_79B1;
            ctr_b <= ctr_b + 32'h85EB_CA77;
        end
    end

    wire [31:0] mix1 = ctr_a ^ {ctr_b[7:0], ctr_b[31:8]};
    wire [31:0] mix2 = ctr_b ^ {ctr_a[3:0], ctr_a[31:4]};

    // Triangle unit 0
    wire signed [15:0] a0_0 = mix1[15:0];
    wire signed [15:0] b0_0 = mix1[31:16];
    wire signed [31:0] c0_0 = {ctr_a[15:0], ctr_b[15:0]};
    wire signed [15:0] a1_0 = ctr_b[15:0] ^ ctr_a[31:16];
    wire signed [15:0] b1_0 = ctr_a[15:0] ^ ctr_b[31:16];
    wire signed [31:0] c1_0 = {ctr_b[15:0], ctr_a[15:0]};
    wire signed [15:0] a2_0 = mix1[31:16] ^ mix1[15:0];
    wire signed [15:0] b2_0 = ctr_a[15:0] + ctr_b[15:0];
    wire signed [31:0] c2_0 = ctr_a ^ ctr_b;
    wire [3:0] tri_r0 = mix1[3:0], tri_g0 = mix1[7:4], tri_b0 = mix1[11:8];

    // Triangle unit 1 (different rotation/mix so it isn't a copy of unit 0)
    wire signed [15:0] a0_1 = mix2[15:0];
    wire signed [15:0] b0_1 = mix2[31:16];
    wire signed [31:0] c0_1 = {ctr_b[7:0], ctr_a[23:0]};
    wire signed [15:0] a1_1 = ctr_a[15:0] ^ ctr_b[15:0];
    wire signed [15:0] b1_1 = ctr_a[31:16] ^ ctr_b[31:16];
    wire signed [31:0] c1_1 = {ctr_a[15:0], ~ctr_b[15:0]};
    wire signed [15:0] a2_1 = mix2[15:0] ^ 16'hFFFF;
    wire signed [15:0] b2_1 = mix2[31:16] ^ 16'h00FF;
    wire signed [31:0] c2_1 = ctr_a + ctr_b;
    wire [3:0] tri_r1 = mix2[3:0], tri_g1 = mix2[7:4], tri_b1 = mix2[11:8];

    // ── Dual rasterizer (the coverage path under measurement) ──────────
    wire [3:0] pixel_r, pixel_g, pixel_b;

    spu_dual_raster u_rast (
        .clk(sys_clk), .rst_n(rst_n),
        .setup0(frame_tick),
        .a0_0(a0_0), .b0_0(b0_0), .c0_0(c0_0),
        .a1_0(a1_0), .b1_0(b1_0), .c1_0(c1_0),
        .a2_0(a2_0), .b2_0(b2_0), .c2_0(c2_0),
        .tri_r0(tri_r0), .tri_g0(tri_g0), .tri_b0(tri_b0),
        .setup1(frame_tick),
        .a0_1(a0_1), .b0_1(b0_1), .c0_1(c0_1),
        .a1_1(a1_1), .b1_1(b1_1), .c1_1(c1_1),
        .a2_1(a2_1), .b2_1(b2_1), .c2_1(c2_1),
        .tri_r1(tri_r1), .tri_g1(tri_g1), .tri_b1(tri_b1),
        .step_x(step_x), .step_y(step_y), .x_span(10'sd640),
        .pixel_r(pixel_r), .pixel_g(pixel_g), .pixel_b(pixel_b)
    );

    // ── Keep the datapath live: fold pixel output into led every cycle ─
    reg [2:0] led_reg = 3'b0;
    always @(posedge sys_clk) begin
        led_reg <= led_reg ^ {pixel_r[3] ^ pixel_r[0],
                               pixel_g[3] ^ pixel_g[0],
                               pixel_b[3] ^ pixel_b[0]};
    end
    assign led = led_reg;

endmodule
