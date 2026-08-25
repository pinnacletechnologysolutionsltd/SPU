// spu13_tang25k_gpu_depth_v2_probe.v — integrated coverage + depth-v2
// area probe: spu_dual_raster (existing, tested coverage path) +
// spu_depth_dispatch (shared dispatcher, both triangle units) + two
// spu_attr_stepper instances (per-pixel depth output, one per unit).
//
// Synthesis/place-route AREA MEASUREMENT ONLY -- no video PMOD needed
// (neither this board nor the A7 has a working TMDS/HDMI driver in this
// repo yet; every existing top-level just ties those pins to zero). No
// functional PASS/FAIL self-test: coverage and depth-v2 are already
// testbench-verified independently (spu_raster_tb.v; the four
// test_gpu_*_rtl_parity.py suites). This exists solely to answer "what
// does the FULL integrated design cost," catching any interaction
// effects (congestion, resource contention) a sum of the separately-
// measured raster (1,317 LUT4) and multiplier (3,532 LUT4) probes
// wouldn't show. See
// spu_strategy/contract_gpu_depth_v2_integrated_probe_2026-08-25.md.
//
// Same anti-optimization pattern as the earlier probes: free-running
// counters drive every input so Yosys can't constant-fold anything
// away; every output (raster pixels + both units' interpolated depth)
// is folded into led[2:0] every cycle to keep the whole datapath live.

module spu13_tang25k_gpu_depth_v2_probe (
    input  wire       sys_clk,
    output wire [2:0] led
);

    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

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
    wire [31:0] mix3 = ctr_a ^ {ctr_a[11:0], ctr_a[31:12]} ^ ctr_b;

    // Triangle unit 0 -- edge coefficients + per-vertex depths
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
    wire [15:0] z0_0 = mix3[15:0];
    wire [15:0] z1_0 = mix3[31:16];
    wire [15:0] z2_0 = ctr_a[15:0] ^ mix3[15:0];

    // Triangle unit 1
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
    wire [15:0] z0_1 = mix3[31:16] ^ ctr_b[15:0];
    wire [15:0] z1_1 = ctr_b[31:16];
    wire [15:0] z2_1 = mix3[15:0] ^ ctr_b[31:16];

    // ── Coverage path (existing, tested) ────────────────────────────
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

    // ── Depth-v2 path (new: dispatcher + one attr_stepper per unit) ─
    wire signed [55:0] A_z0, B_z0, C_z0, A_z1, B_z1, C_z1;
    wire [6:0] frac_bits0, frac_bits1;
    wire ready0, ready1;

    spu_depth_dispatch u_dispatch (
        .clk(sys_clk), .rst_n(rst_n),
        .depth_setup0(frame_tick), .depth_setup1(frame_tick),
        .a0_0(a0_0), .b0_0(b0_0), .a1_0(a1_0), .b1_0(b1_0), .a2_0(a2_0), .b2_0(b2_0),
        .c0_0(c0_0), .c1_0(c1_0), .c2_0(c2_0), .z0_0(z0_0), .z1_0(z1_0), .z2_0(z2_0),
        .a0_1(a0_1), .b0_1(b0_1), .a1_1(a1_1), .b1_1(b1_1), .a2_1(a2_1), .b2_1(b2_1),
        .c0_1(c0_1), .c1_1(c1_1), .c2_1(c2_1), .z0_1(z0_1), .z1_1(z1_1), .z2_1(z2_1),
        .A_z0(A_z0), .B_z0(B_z0), .C_z0(C_z0), .frac_bits0(frac_bits0), .ready0(ready0),
        .A_z1(A_z1), .B_z1(B_z1), .C_z1(C_z1), .frac_bits1(frac_bits1), .ready1(ready1)
    );

    wire signed [55:0] depth0, depth1;
    spu_attr_stepper u_attr0 (
        .clk(sys_clk), .rst_n(rst_n), .setup(ready0),
        .a_coef(A_z0), .b_coef(B_z0), .c_coef(C_z0),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits0),
        .value_out(depth0)
    );
    spu_attr_stepper u_attr1 (
        .clk(sys_clk), .rst_n(rst_n), .setup(ready1),
        .a_coef(A_z1), .b_coef(B_z1), .c_coef(C_z1),
        .step_x(step_x), .step_y(step_y), .frac_bits(frac_bits1),
        .value_out(depth1)
    );

    // ── Keep everything live: fold all outputs into led every cycle ─
    reg [2:0] led_reg = 3'b0;
    always @(posedge sys_clk) begin
        led_reg <= led_reg
            ^ {pixel_r[3] ^ pixel_r[0], pixel_g[3] ^ pixel_g[0], pixel_b[3] ^ pixel_b[0]}
            ^ {depth0[55] ^ depth0[0], depth0[27], depth0[10]}
            ^ {depth1[55] ^ depth1[0], depth1[27], depth1[10]};
    end
    assign led = led_reg;

endmodule
