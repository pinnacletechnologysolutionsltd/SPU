`timescale 1ns/1ps

// T1f-I1 profile boundary smoke test. This is deliberately not a T1f scene
// oracle; it only proves that the compile-time profile split keeps the legacy
// 63-byte transaction out of the four-primitive 126-byte commit path.
module spu_t1f_profile_tb;
    reg clk = 0, rst_n = 0, rx_valid = 0;
    reg [7:0] rx_byte = 0;
    wire [3:0] vr, vg, vb;
    integer checks = 0, failures = 0, i;

    localparam [251:0] P0 = {16'd400,16'd3600,16'd700,4'h0,4'h0,4'hf,
        32'sd276000,-16'sd480,-16'sd460,-32'sd18400,-16'sd80,16'sd460,
        32'sd0,16'sd560,16'sd0};
    localparam [251:0] P1 = {16'd3600,16'd400,16'd700,4'h0,4'hf,4'h0,
        32'sd276000,-16'sd80,-16'sd460,-32'sd18400,-16'sd480,16'sd460,
        32'sd0,16'sd560,16'sd0};
    localparam [251:0] P2 = {16'd900,16'd3200,16'd500,4'hf,4'h0,4'h0,
        32'sd34500,-16'sd60,-16'sd58,-32'sd2300,-16'sd10,16'sd58,
        32'sd0,16'sd70,16'sd0};
    localparam [251:0] P3 = {16'd3100,16'd600,16'd800,4'h0,4'hf,4'hf,
        32'sd34500,-16'sd10,-16'sd58,-32'sd2300,-16'sd60,16'sd58,
        32'sd0,16'sd70,16'sd0};
    localparam [1007:0] SCENE4 = {P3,P2,P1,P0};

    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1),
        .H_ACTIVE(24),.H_FP(2),.H_SYNC(2),.H_BP(2),
        .V_ACTIVE(12),.V_FP(1),.V_SYNC(1),.V_BP(1)) dut (
        .clk_pixel(clk),.clk_tmds(clk),.rst_n(rst_n),
        .tri0_setup(1'b0),.tri0_a0(16'sd0),.tri0_b0(16'sd0),.tri0_c0(32'sd0),.tri0_a1(16'sd0),.tri0_b1(16'sd0),.tri0_c1(32'sd0),
        .tri0_a2(16'sd0),.tri0_b2(16'sd0),.tri0_c2(32'sd0),.tri0_r(4'd0),.tri0_g(4'd0),.tri0_b(4'd0),.tri0_z0(16'd0),.tri0_z1(16'd0),.tri0_z2(16'd0),
        .tri1_setup(1'b0),.tri1_a0(16'sd0),.tri1_b0(16'sd0),.tri1_c0(32'sd0),.tri1_a1(16'sd0),.tri1_b1(16'sd0),.tri1_c1(32'sd0),
        .tri1_a2(16'sd0),.tri1_b2(16'sd0),.tri1_c2(32'sd0),.tri1_r(4'd0),.tri1_g(4'd0),.tri1_b(4'd0),.tri1_z0(16'd0),.tri1_z1(16'd0),.tri1_z2(16'd0),
        .scene_rx_byte(rx_byte),.scene_rx_valid(rx_valid),
        .vga_r(vr),.vga_g(vg),.vga_b(vb),.vga_hsync(),.vga_vsync(),
        .tmds_clk_p(),.tmds_clk_n(),.tmds_d_p(),.tmds_d_n());

    always #5 clk = ~clk;

    task check(input condition, input [8*96-1:0] label); begin
        checks = checks + 1;
        if (condition !== 1'b1) begin failures = failures + 1; $display("FAIL: %0s", label); end
    end endtask

    task send_byte(input [7:0] value); begin
        @(negedge clk); rx_byte = value; rx_valid = 1'b1;
        @(negedge clk); rx_valid = 1'b0; rx_byte = 0;
    end endtask

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        send_byte(8'hA5);
        for (i = 0; i < 63; i = i + 1) send_byte(SCENE4[i*8 +: 8]);
        check(!dut.scene_commit_pending, "63 bytes do not commit four-scene candidate");
        check(!dut.activate_scene, "63 bytes do not activate four-scene profile");
        check(dut.active_scene === 1008'b0, "incomplete four-scene candidate leaves active scene unchanged");

        for (i = 63; i < 126; i = i + 1) send_byte(SCENE4[i*8 +: 8]);
        check(dut.scene_commit_pending, "126 bytes commit four-scene candidate");
        check(dut.candidate_scene === SCENE4, "126-byte candidate reconstructs exactly");
        check(dut.active_scene === 1008'b0, "prepared candidate remains separate from active scene");

        while (!dut.prepared_generation_matches) begin
            @(negedge clk);
            check(dut.active_scene === 1008'b0, "active scene remains stable during four-result preparation");
            check(!dut.activate_scene, "four-scene preparation does not activate early");
        end
        force dut.frame_start = 1'b1;
        #1;
        check(dut.prepared_depth_control.u_prepared_control4.ready_seen === 4'b1111,
              "activation waits for all four derived results");
        check(dut.activate_scene, "four-scene activation waits for all four results");
        @(posedge clk); #1;
        check(dut.active_scene === SCENE4, "qualified activation selects the four-scene bank");
        release dut.frame_start;

        if (!failures) $display("PASS: T1f profile split (%0d checks)", checks);
        else $display("FAIL: T1f profile split %0d/%0d checks failed", failures, checks);
        $finish;
    end
endmodule
