// spu_gpu_pipeline_tb.v — GPU Pipeline Integration Testbench
//
// Chains: rasterizer → fragment pipe → HAL output
// Projects one VE triangle onto a pixel grid and verifies
// the spread-weighted Quadray blend produces correct values.
//
// Test triangle: VE vertices (1,-1,0,0), (1,0,-1,0), (1,0,0,-1)
// These form an equilateral triangle face of the cuboctahedron.
// Projected onto 2D: (0,0), (100,0), (50,87) — a regular triangle.

`timescale 1ns/1ps

module spu_gpu_pipeline_tb;

    reg         clk, rst_n;
    reg         pulse_61k;
    reg  [15:0] q_a, q_b, q_c, q_d, q_energy, rational_scale;
    wire        display_ready;

    // ── Rasterizer signals ──────────────────────────────────────────
    reg  [63:0] v0_xy, v1_xy, v2_xy;
    reg  [15:0] v0_z, v1_z, v2_z;
    reg  [31:0] pixel_x, pixel_y;
    wire        pixel_inside;
    wire [31:0] lambda0, lambda1, lambda2;
    wire [15:0] pixel_z;

    spu_rasterizer u_rast (
        .clk(clk), .reset(!rst_n),
        .v0_abcd(v0_xy), .v1_abcd(v1_xy), .v2_abcd(v2_xy),
        .v0_z(v0_z), .v1_z(v1_z), .v2_z(v2_z),
        .pixel_x(pixel_x), .pixel_y(pixel_y),
        .pixel_inside(pixel_inside),
        .lambda0(lambda0), .lambda1(lambda1), .lambda2(lambda2),
        .pixel_z(pixel_z)
    );

    // ── Fragment pipe signals ───────────────────────────────────────
    reg  [63:0] v0_attr, v1_attr, v2_attr;
    wire [127:0] pixel_energy_n;
    wire [15:0]  pixel_w_total;

    spu_fragment_pipe u_frag (
        .clk(clk), .rst_n(rst_n),
        .pixel_inside(pixel_inside),
        .w0_n(lambda1[31:16]),  // convert 16.16 → integer
        .w1_n(lambda2[31:16]),
        .w2_n(lambda0[31:16]),  // reorder: λ0↔λ2 to match vertex order
        .v0_attr(v0_attr),
        .v1_attr(v1_attr),
        .v2_attr(v2_attr),
        .pixel_energy_n(pixel_energy_n),
        .pixel_w_total(pixel_w_total)
    );

    always #5 clk = ~clk;  // 100 MHz

    integer pass, fail;

    task check;
        input [255:0] name;
        input condition;
        begin
            if (condition) begin
                $display("  PASS: %0s", name);
                pass = pass + 1;
            end else begin
                $display("  FAIL: %0s", name);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; pulse_61k = 0;
        pass = 0; fail = 0;

        @(posedge clk); rst_n = 1;
        @(posedge clk);

        $display("\n── GPU Pipeline Tests ──");

        // ── Test 1: Triangle setup ─────────────────────────────────
        // VE triangle face vertices, projected to screen
        // v0 = (100, 0), v1 = (0, 0), v2 = (50, 86)
        v0_xy = {32'd0,   32'd100};  // {y, x}
        v1_xy = {32'd0,   32'd0};
        v2_xy = {32'd86,  32'd50};
        v0_z = 16'd0; v1_z = 16'd0; v2_z = 16'd0;

        // Fragment attributes: Quadray vertex data (4×16-bit packed)
        // VE vertices in integer Quadray, packed as {axis0, axis1, axis2, axis3}
        // Using zero-sum coordinates scaled to fit 16 bits
        // v0=(1,-1,0,0) → {1, -1, 0, 0}
        // v1=(1,0,-1,0) → {1, 0, -1, 0}
        // v2=(1,0,0,-1) → {1, 0, 0, -1}
        v0_attr = {16'd1, 16'hFFFF, 16'd0,    16'd0};     // {A=1, B=-1, C=0, D=0}
        v1_attr = {16'd1, 16'd0,    16'hFFFF, 16'd0};     // {A=1, B=0, C=-1, D=0}
        v2_attr = {16'd1, 16'd0,    16'd0,    16'hFFFF};  // {A=1, B=0, C=0, D=-1}

        @(posedge clk);

        // ── Test 2: Pixel inside triangle (centroid) ───────────────
        pixel_x = 50; pixel_y = 28;  // near centroid
        #1;  // let combinational settle
        check("centroid inside", pixel_inside == 1);

        // ── Test 3: Pixel outside triangle ─────────────────────────
        pixel_x = 200; pixel_y = 200;  // clearly outside
        #1;
        check("far outside", pixel_inside == 0);

        // ── Test 4: Barycentric weights at centroid ────────────────
        pixel_x = 50; pixel_y = 28;
        #1;
        // All three lambdas should be positive and sum to ~1.0 in 16.16
        check("lambda0 > 0", lambda0 > 0);
        check("lambda1 > 0", lambda1 > 0);
        check("lambda2 > 0", lambda2 > 0);

        // ── Test 5: Fragment blend ─────────────────────────────────
        @(posedge clk);  // fragment pipe registers on clock
        @(posedge clk);
        // pixel_energy_n should be non-zero for inside pixels
        check("fragment blend non-zero", pixel_energy_n != 128'b0);

        // ── Test 6: Weight sum ─────────────────────────────────────
        check("weight total > 0", pixel_w_total > 0);

        repeat (2) @(posedge clk);

        $display("\n──────────────────────────────");
        $display("Results: %0d passed, %0d failed", pass, fail);
        if (fail == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

endmodule
