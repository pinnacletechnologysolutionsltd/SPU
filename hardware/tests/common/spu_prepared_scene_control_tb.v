`timescale 1ns/1ps
module spu_prepared_scene_control_tb;
    reg clk=0, rst_n=0, pending=0, frame_start=0, ready0=0, ready1=0;
    reg signed [55:0] A0=56'sd11,B0=56'sd12,C0=56'sd13;
    reg signed [55:0] A1=56'sd21,B1=56'sd22,C1=56'sd23;
    reg [6:0] F0=7'd4,F1=7'd5;
    wire prep0,prep1,activate,seen0,seen1,match;
    wire signed [55:0] active_A0,active_B0,active_C0,active_A1,active_B1,active_C1;
    wire [6:0] active_F0,active_F1;
    integer checks=0,failures=0;

    spu_prepared_scene_control dut(
        .clk(clk),.rst_n(rst_n),.commit_pending(pending),.frame_start(frame_start),
        .ready0(ready0),.ready1(ready1),
        .candidate_A_z0(A0),.candidate_B_z0(B0),.candidate_C_z0(C0),.candidate_frac_bits0(F0),
        .candidate_A_z1(A1),.candidate_B_z1(B1),.candidate_C_z1(C1),.candidate_frac_bits1(F1),
        .prepare0(prep0),.prepare1(prep1),.activate_scene(activate),
        .ready0_seen(seen0),.ready1_seen(seen1),.generation_matches(match),
        .active_A_z0(active_A0),.active_B_z0(active_B0),.active_C_z0(active_C0),
        .active_frac_bits0(active_F0),.active_A_z1(active_A1),.active_B_z1(active_B1),
        .active_C_z1(active_C1),.active_frac_bits1(active_F1));
    always #5 clk=~clk;
    task check(input condition,input [8*64-1:0] label); begin
        checks=checks+1; if(condition!==1'b1) begin failures=failures+1;
            $display("FAIL: %0s",label); end
    end endtask
    task pulse(input integer which); begin
        @(negedge clk); if(which==0) ready0=1; else ready1=1;
        @(negedge clk); ready0=0; ready1=0;
    end endtask
    task pulse_frame; begin
        @(negedge clk); frame_start=1; @(negedge clk); frame_start=0;
    end endtask

    initial begin
        repeat(2) @(negedge clk); rst_n=1; @(negedge clk); pending=1;
        @(negedge clk); check(prep0&&prep1,"one bounded preparation request per triangle");
        pulse(1); check(seen1&&!seen0&&!match,"N3 triangle 1 alone is incomplete");
        pulse_frame(); check(!activate,"N3 triangle 1 alone cannot activate");
        pulse(0); check(seen0&&seen1&&match,"both coherent results prepare scene");
        force dut.generation_matches=1'b0;
        pulse_frame(); check(!activate,"N5 generation mismatch cannot activate");
        release dut.generation_matches;
        @(negedge clk); frame_start=1; #1;
        check(activate,"fully qualified frame asserts activation");
        @(negedge clk); frame_start=0; pending=0;
        check(active_A0==56'sd11&&active_C1==56'sd23&&active_F0==7'd4&&active_F1==7'd5,
              "activation retains complete two-triangle derived state");

        A0=56'sd31; F0=7'd9; @(negedge clk); pending=1;
        @(negedge clk); pulse(0);
        check(seen0&&!seen1&&!match,"N2 triangle 0 alone is incomplete");
        pulse_frame(); check(!activate&&active_A0==56'sd11&&active_F0==7'd4,
              "N2 incomplete next generation preserves active state");
        if(!failures) $display("PASS: prepared control N2 N3 N5 (%0d checks)",checks);
        else $display("FAIL: prepared control %0d/%0d checks failed",failures,checks);
        $finish;
    end
endmodule
