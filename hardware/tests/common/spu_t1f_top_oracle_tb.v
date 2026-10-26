`timescale 1ns/1ps

// T1f-I2 exploratory top-level oracle. One common geometric triangle is
// assigned four affine depth planes whose lower envelope selects each record
// at a different representative pixel. This exercises all four lanes,
// four-way reduction, unequal-depth selection, and the lower-record tie rule.
module spu_t1f_top_oracle_tb;
    localparam [251:0] P0 = {16'd60,16'd0,16'd110,4'h0,4'h0,4'hf,
        -32'sd500, -16'sd30, 16'sd80, 32'sd5900, -16'sd30, -16'sd80,
        -32'sd600, 16'sd60, 16'sd0};
    localparam [251:0] P1 = {16'd0,16'd60,16'd110,4'h0,4'hf,4'h0,
        -32'sd500, -16'sd30, 16'sd80, 32'sd5900, -16'sd30, -16'sd80,
        -32'sd600, 16'sd60, 16'sd0};
    localparam [251:0] P2 = {16'd120,16'd60,16'd10,4'hf,4'h0,4'h0,
        -32'sd500, -16'sd30, 16'sd80, 32'sd5900, -16'sd30, -16'sd80,
        -32'sd600, 16'sd60, 16'sd0};
    localparam [251:0] P3 = {16'd60,16'd120,16'd10,4'h0,4'hf,4'hf,
        -32'sd500, -16'sd30, 16'sd80, 32'sd5900, -16'sd30, -16'sd80,
        -32'sd600, 16'sd60, 16'sd0};
    localparam [1007:0] SCENE = {P3,P2,P1,P0};
    localparam [1007:0] SCENE_PERM = {P2,P0,P3,P1};

    localparam [251:0] C0 = {16'd10,16'd10,16'd10,4'h0,4'h0,4'hf,
        -32'sd200, 16'sd0, 16'sd20, 32'sd800, -16'sd20, -16'sd20,
        -32'sd200, 16'sd20, 16'sd0};
    localparam [251:0] C1 = {16'd20,16'd20,16'd20,4'h0,4'hf,4'h0,
        -32'sd1000, 16'sd0, 16'sd20, 32'sd1600, -16'sd20, -16'sd20,
        -32'sd200, 16'sd20, 16'sd0};
    localparam [251:0] C2 = {16'd30,16'd30,16'd30,4'hf,4'h0,4'h0,
        -32'sd200, 16'sd0, 16'sd20, 32'sd1600, -16'sd20, -16'sd20,
        -32'sd1000, 16'sd20, 16'sd0};
    localparam [251:0] C3 = {16'd40,16'd40,16'd40,4'h0,4'hf,4'hf,
        -32'sd1000, 16'sd0, 16'sd20, 32'sd2400, -16'sd20, -16'sd20,
        -32'sd1000, 16'sd20, 16'sd0};
    localparam [1007:0] COVERAGE_SCENE = {C3,C2,C1,C0};

    reg clk = 1'b0, rst_n = 1'b0;
    reg [7:0] scene_rx_byte = 8'h00;
    reg scene_rx_valid = 1'b0;
    wire [3:0] vga_r, vga_g, vga_b;
    integer failures = 0, seen_mask = 0, i, x_ref, y_ref, guard = 0;

    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1),
        .H_ACTIVE(80), .H_FP(2), .H_SYNC(2), .H_BP(2),
        .V_ACTIVE(100), .V_FP(1), .V_SYNC(1), .V_BP(1)) dut (
        .clk_pixel(clk), .clk_tmds(clk), .rst_n(rst_n),
        .tri0_setup(1'b0), .tri0_a0(16'sd0), .tri0_b0(16'sd0), .tri0_c0(32'sd0),
        .tri0_a1(16'sd0), .tri0_b1(16'sd0), .tri0_c1(32'sd0),
        .tri0_a2(16'sd0), .tri0_b2(16'sd0), .tri0_c2(32'sd0),
        .tri0_r(4'd0), .tri0_g(4'd0), .tri0_b(4'd0),
        .tri0_z0(16'd0), .tri0_z1(16'd0), .tri0_z2(16'd0),
        .tri1_setup(1'b0), .tri1_a0(16'sd0), .tri1_b0(16'sd0), .tri1_c0(32'sd0),
        .tri1_a1(16'sd0), .tri1_b1(16'sd0), .tri1_c1(32'sd0),
        .tri1_a2(16'sd0), .tri1_b2(16'sd0), .tri1_c2(32'sd0),
        .tri1_r(4'd0), .tri1_g(4'd0), .tri1_b(4'd0),
        .tri1_z0(16'd0), .tri1_z1(16'd0), .tri1_z2(16'd0),
        .scene_rx_byte(scene_rx_byte), .scene_rx_valid(scene_rx_valid),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(), .vga_vsync(), .tmds_clk_p(), .tmds_clk_n(),
        .tmds_d_p(), .tmds_d_n());

    always #1 clk = ~clk;

    task send_byte(input [7:0] value); begin
        @(negedge clk); scene_rx_byte = value; scene_rx_valid = 1'b1;
        @(negedge clk); scene_rx_valid = 1'b0; scene_rx_byte = 8'h00;
    end endtask

    task send_scene(input [1007:0] value); begin
        send_byte(8'hA5);
        for (i = 0; i < 126; i = i + 1) send_byte(value[i*8 +: 8]);
    end endtask

    task check_pixel(input integer bit_no, input [3:0] er, eg, eb,
                     input [8*32-1:0] label); begin
        seen_mask = seen_mask | (1 << bit_no);
        if ({vga_r,vga_g,vga_b} !== {er,eg,eb}) begin
            failures = failures + 1;
            $display("FAIL: (%0d,%0d) %0s expected=%h got=%h depths=%0d,%0d,%0d,%0d cov=%b%b%b%b",
                x_ref, y_ref, label, {er,eg,eb}, {vga_r,vga_g,vga_b},
                dut.depth0, dut.depth1, dut.depth2, dut.depth3,
                dut.cov3_armed, dut.cov2_armed, dut.cov1_armed, dut.cov0_armed);
        end else begin
            $display("ORACLE: (%0d,%0d) %0s RGB=%h", x_ref, y_ref, label,
                {vga_r,vga_g,vga_b});
        end
    end endtask

    task sample_target; begin
        if (dut.active_d) begin
            if (x_ref == 5  && y_ref == 5  && !(seen_mask & (1 << 0))) check_pixel(0,0,0,0,"background");
            if (x_ref == 20 && y_ref == 20 && !(seen_mask & (1 << 1))) check_pixel(1,15,0,0,"primitive0_nearer");
            if (x_ref == 60 && y_ref == 20 && !(seen_mask & (1 << 2))) check_pixel(2,0,15,0,"primitive1_nearer");
            if (x_ref == 30 && y_ref == 60 && !(seen_mask & (1 << 3))) check_pixel(3,0,0,15,"primitive2_nearer");
            if (x_ref == 50 && y_ref == 60 && !(seen_mask & (1 << 4))) check_pixel(4,15,15,0,"primitive3_nearer");
            if (x_ref == 40 && y_ref == 40 && !(seen_mask & (1 << 5))) check_pixel(5,15,0,0,"equal_depth_record0_tie");
        end
    end endtask

    task sample_permuted_target; begin
        if (dut.active_d) begin
            if (x_ref == 20 && y_ref == 20 && !(seen_mask & (1 << 1))) check_pixel(1,15,0,0,"permuted_primitive0_nearer");
            if (x_ref == 60 && y_ref == 20 && !(seen_mask & (1 << 2))) check_pixel(2,0,15,0,"permuted_primitive1_nearer");
            if (x_ref == 30 && y_ref == 60 && !(seen_mask & (1 << 3))) check_pixel(3,0,0,15,"permuted_primitive2_nearer");
            if (x_ref == 50 && y_ref == 60 && !(seen_mask & (1 << 4))) check_pixel(4,15,15,0,"permuted_primitive3_nearer");
        end
    end endtask

    task sample_coverage_target; begin
        if (dut.active_d) begin
            if (x_ref == 40 && y_ref == 40 && !(seen_mask & (1 << 0))) check_pixel(0,0,0,0,"coverage_background");
            if (x_ref == 20 && y_ref == 20 && !(seen_mask & (1 << 1))) check_pixel(1,15,0,0,"primitive0_only");
            if (x_ref == 60 && y_ref == 20 && !(seen_mask & (1 << 2))) check_pixel(2,0,15,0,"primitive1_only");
            if (x_ref == 20 && y_ref == 60 && !(seen_mask & (1 << 3))) check_pixel(3,0,0,15,"primitive2_only");
            if (x_ref == 60 && y_ref == 60 && !(seen_mask & (1 << 4))) check_pixel(4,15,15,0,"primitive3_only");
        end
    end endtask

    initial begin
        repeat (5) @(negedge clk);
        rst_n = 1'b1;
        send_scene(SCENE);
        wait (dut.active_scene === SCENE);
        wait (dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0);
        @(posedge clk);
        while (!(dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0)) @(posedge clk);

        while (seen_mask != 63 && guard < 20000) begin
            x_ref = dut.u_timing.x; y_ref = dut.u_timing.y;
            @(posedge clk); #1; sample_target(); guard = guard + 1;
        end
        if (seen_mask != 63) begin
            failures = failures + 1;
            $display("FAIL: top-level oracle incomplete mask=%0d", seen_mask);
        end

        // Unequal-depth order must be invariant when the same geometric
        // primitive/depth/colour tuples are permuted among record slots.
        send_scene(SCENE_PERM);
        wait (dut.active_scene === SCENE_PERM);
        wait (dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0);
        @(posedge clk);
        while (!(dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0)) @(posedge clk);
        seen_mask = 0; guard = 0;
        while ((seen_mask & 5'b11110) != 5'b11110 && guard < 20000) begin
            x_ref = dut.u_timing.x; y_ref = dut.u_timing.y;
            @(posedge clk); #1; sample_permuted_target(); guard = guard + 1;
        end
        if ((seen_mask & 5'b11110) != 5'b11110) begin
            failures = failures + 1;
            $display("FAIL: permutation oracle incomplete mask=%0d", seen_mask);
        end

        send_scene(COVERAGE_SCENE);
        wait (dut.active_scene === COVERAGE_SCENE);
        wait (dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0);
        @(posedge clk);
        while (!(dut.u_timing.x == 10'd0 && dut.u_timing.y == 10'd0)) @(posedge clk);
        seen_mask = 0; guard = 0;
        while ((seen_mask & 5'b11111) != 5'b11111 && guard < 20000) begin
            x_ref = dut.u_timing.x; y_ref = dut.u_timing.y;
            @(posedge clk); #1; sample_coverage_target(); guard = guard + 1;
        end
        if ((seen_mask & 5'b11111) != 5'b11111) begin
            failures = failures + 1;
            $display("FAIL: coverage oracle incomplete mask=%0d", seen_mask);
        end
        if (failures == 0) $display("PASS: T1f-I2 top-level four-way oracle");
        else $display("FAIL: T1f-I2 top-level oracle failures=%0d", failures);
        $finish;
    end
endmodule
