`timescale 1ns/1ps
module spu_prepared_scene_banking_tb;
    reg clk = 0, rst_n = 0, rx_valid = 0;
    reg [7:0] rx_byte = 0;
    wire [3:0] vr, vg, vb;
    integer checks = 0, failures = 0, activations = 0, early_frames = 0;
    integer i;
    reg signed [15:0] bypass_cov_expected;
    reg signed [55:0] bypass_depth_expected;

    localparam [251:0] A0 = {16'd400,16'd3600,16'd700,4'h0,4'h0,4'hf,
        32'sd276000,-16'sd480,-16'sd460,-32'sd18400,-16'sd80,16'sd460,
        32'sd0,16'sd560,16'sd0};
    localparam [251:0] A1 = {16'd3600,16'd400,16'd700,4'h0,4'hf,4'h0,
        32'sd276000,-16'sd80,-16'sd460,-32'sd18400,-16'sd480,16'sd460,
        32'sd0,16'sd560,16'sd0};
    localparam [251:0] B0 = {16'd900,16'd3200,16'd500,4'hf,4'h0,4'h0,
        32'sd34500,-16'sd60,-16'sd58,-32'sd2300,-16'sd10,16'sd58,
        32'sd0,16'sd70,16'sd0};
    localparam [251:0] B1 = {16'd3100,16'd600,16'd800,4'h0,4'hf,4'hf,
        32'sd34500,-16'sd10,-16'sd58,-32'sd2300,-16'sd60,16'sd58,
        32'sd0,16'sd70,16'sd0};
    localparam [251:0] C0 = {16'd1200,16'd2800,16'd300,4'hf,4'h0,4'hf,
        32'sd69000,-16'sd120,-16'sd115,-32'sd4600,-16'sd20,16'sd115,
        32'sd0,16'sd140,16'sd0};
    localparam [251:0] C1 = {16'd2600,16'd800,16'd1100,4'hf,4'hf,4'h0,
        32'sd69000,-16'sd20,-16'sd115,-32'sd4600,-16'sd120,16'sd115,
        32'sd0,16'sd140,16'sd0};
    localparam [503:0] SCENE_A = {A1,A0};
    localparam [503:0] SCENE_B = {B1,B0};
    localparam [503:0] SCENE_C = {C1,C0};

    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1),
        .H_ACTIVE(24),.H_FP(2),.H_SYNC(2),.H_BP(2),
        .V_ACTIVE(12),.V_FP(1),.V_SYNC(1),.V_BP(1)) dut (
        .clk_pixel(clk),.clk_tmds(clk),.rst_n(rst_n),
        .tri0_setup(1'b0),.tri0_a0(16'sd0),.tri0_b0(16'sd0),.tri0_c0(32'sd0),
        .tri0_a1(16'sd0),.tri0_b1(16'sd0),.tri0_c1(32'sd0),
        .tri0_a2(16'sd0),.tri0_b2(16'sd0),.tri0_c2(32'sd0),
        .tri0_r(4'd0),.tri0_g(4'd0),.tri0_b(4'd0),
        .tri0_z0(16'd0),.tri0_z1(16'd0),.tri0_z2(16'd0),
        .tri1_setup(1'b0),.tri1_a0(16'sd0),.tri1_b0(16'sd0),.tri1_c0(32'sd0),
        .tri1_a1(16'sd0),.tri1_b1(16'sd0),.tri1_c1(32'sd0),
        .tri1_a2(16'sd0),.tri1_b2(16'sd0),.tri1_c2(32'sd0),
        .tri1_r(4'd0),.tri1_g(4'd0),.tri1_b(4'd0),
        .tri1_z0(16'd0),.tri1_z1(16'd0),.tri1_z2(16'd0),
        .scene_rx_byte(rx_byte),.scene_rx_valid(rx_valid),
        .vga_r(vr),.vga_g(vg),.vga_b(vb),.vga_hsync(),.vga_vsync(),
        .tmds_clk_p(),.tmds_clk_n(),.tmds_d_p(),.tmds_d_n());
    always #5 clk = ~clk;

    task check(input condition, input [8*80-1:0] label); begin
        checks=checks+1; if (condition !== 1'b1) begin
            failures=failures+1; $display("FAIL: %0s",label); end
    end endtask
    task send_byte(input [7:0] value); begin
        @(negedge clk); rx_byte=value; rx_valid=1;
        @(negedge clk); rx_valid=0; rx_byte=0;
    end endtask
    task send_scene(input [503:0] value); integer j; reg [503:0] held; begin
        held=dut.active_scene; send_byte(8'hA5);
        for (j=0;j<63;j=j+1) begin
            send_byte(value[j*8 +: 8]);
            check(dut.active_scene===held,"candidate writes cannot alter active raw scene");
        end
    end endtask
    task wait_prepared(input [503:0] old_scene, input [503:0] expected_candidate);
        reg signed [55:0] old_A0; reg [6:0] old_f0; begin
        old_A0=dut.active_A_z0; old_f0=dut.active_frac_bits0;
        force dut.frame_start = 1'b1;
        @(posedge clk); #1;
        check(!dut.activate_scene && dut.active_scene===old_scene,
              "early frame_start activated incomplete candidate");
        early_frames=early_frames+1;
        release dut.frame_start;
        while (!dut.prepared_generation_matches) begin
            @(negedge clk);
            check(dut.active_scene===old_scene,"preparation changed active raw scene");
            check(dut.candidate_scene===expected_candidate,
                  "pending candidate scene is not stable/read-only");
            check(dut.active_A_z0===old_A0,"preparation changed active retained depth");
            check(dut.attr_frac_bits0===old_f0,"candidate frac_bits leaked into renderer");
            if (dut.frame_start) begin
                early_frames=early_frames+1;
                check(!dut.activate_scene,"incomplete preparation activated at frame_start");
            end
            if (dut.prepared_ready0 && !dut.prepared_ready1)
                check(!dut.activate_scene,"triangle 0 readiness activated alone");
        end
    end endtask
    task wait_activation(input [503:0] expected); integer prior_count; begin
        prior_count=activations; while (!dut.activate_scene) @(negedge clk);
        check(dut.frame_start && dut.scene_commit_pending,"activation lacks qualification");
        @(negedge clk);
        check(dut.active_scene===expected,"qualified activation selected wrong raw scene");
        check(activations==prior_count+1,"raw-bank activation count is not exactly one");
    end endtask

    always @(posedge clk) if (rst_n && dut.activate_scene) begin
        activations=activations+1;
        check(dut.frame_start && dut.scene_commit_pending &&
              dut.prepared_ready0 && dut.prepared_ready1 &&
              dut.prepared_generation_matches,
              "activation requires frame pending readiness and generation");
        bypass_cov_expected=dut.ca_a0_0;
        bypass_depth_expected=dut.A_z0;
        #1;
        check(dut.u_rast.u0.u_e0.a_r===bypass_cov_expected,
              "activation-edge coverage bypass sampled stale scene");
        check(dut.u_attr0.a_r===bypass_depth_expected,
              "activation-edge depth bypass sampled stale result");
    end

    initial begin
        repeat(3) @(negedge clk); rst_n=1; @(negedge clk);
        check(dut.active_scene===504'b0 && !dut.scene_commit_pending,"reset state");
        send_scene(SCENE_A);
        $display("TRACE: A received at %0t", $time);
        check(dut.candidate_scene===SCENE_A && dut.active_scene===0,"P1 A pending privately");
        wait_prepared(504'b0,SCENE_A); $display("TRACE: A prepared at %0t", $time);
        wait_activation(SCENE_A); $display("TRACE: A active at %0t", $time);
        check(dut.active_A_z0===dut.A_z0 && dut.active_frac_bits0===dut.frac_bits0,
              "P1 retained depth equals prepared A");

        send_scene(SCENE_B);
        $display("TRACE: B received at %0t", $time);
        check(dut.candidate_scene===SCENE_B && dut.active_scene===SCENE_A,"P2 B private");
        wait_prepared(SCENE_A,SCENE_B); $display("TRACE: B prepared at %0t", $time);
        check(dut.frac_bits0!==dut.active_frac_bits0,"N6 fixture has distinct frac_bits");
        force dut.prepared_generation_matches = 1'b0;
        while (!dut.frame_start) @(negedge clk);
        @(negedge clk); check(dut.active_scene===SCENE_A,"N5 generation mismatch activated");
        release dut.prepared_generation_matches;
        wait_activation(SCENE_B); $display("TRACE: B active at %0t", $time);
        check(dut.active_frac_bits0===dut.frac_bits0,"N6 B frac_bits activates atomically");

        send_scene(SCENE_C); $display("TRACE: C received at %0t", $time);
        wait_prepared(SCENE_B,SCENE_C); $display("TRACE: C prepared at %0t", $time);
        wait_activation(SCENE_C); $display("TRACE: C active at %0t", $time);
        check(dut.active_scene===SCENE_C,"P4 repeated B to C activation");
        check(activations==3 && early_frames>0,"P1-P4 activation/early-frame coverage");
        if (!failures) $display("PASS: prepared scene P1-P4 N1-N10 (%0d checks)",checks);
        else $display("FAIL: prepared scene %0d/%0d checks failed",failures,checks);
        $finish;
    end
endmodule
