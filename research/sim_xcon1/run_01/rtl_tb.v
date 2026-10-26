`timescale 1ns/1ps
module s2_changed_datapath_tb;
reg clk=0,rst_n=0,start=0,edge_setup=0,attr_setup=0,step_x=0,step_y=0;
always #5 clk=~clk;
wire [63:0] edge_coef_0_0=64'h0000023000000000;
wire edge_inside_0_0;
spu_edge_stepper e_0_0(.clk(clk),.rst_n(rst_n),.setup(edge_setup),.coef_pack(edge_coef_0_0),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside_0_0));
wire [63:0] edge_coef_0_1=64'h01ccffb0ffffb820;
wire edge_inside_0_1;
spu_edge_stepper e_0_1(.clk(clk),.rst_n(rst_n),.setup(edge_setup),.coef_pack(edge_coef_0_1),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside_0_1));
wire [63:0] edge_coef_0_2=64'hfe34fe2000043620;
wire edge_inside_0_2;
spu_edge_stepper e_0_2(.clk(clk),.rst_n(rst_n),.setup(edge_setup),.coef_pack(edge_coef_0_2),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside_0_2));
wire signed [15:0] t0_a0=16'h0000;
wire signed [15:0] t0_b0=16'h0230;
wire signed [31:0] t0_c0=32'h00000000;
wire signed [15:0] t0_a1=16'h01cc;
wire signed [15:0] t0_b1=16'hffb0;
wire signed [31:0] t0_c1=32'hffffb820;
wire signed [15:0] t0_a2=16'hfe34;
wire signed [15:0] t0_b2=16'hfe20;
wire signed [31:0] t0_c2=32'h00043620;
wire [15:0] t0_z0=16'h02bc;
wire [15:0] t0_z1=16'h0e10;
wire [15:0] t0_z2=16'h0190;
wire signed [55:0] A_z0,B_z0,C_z0;
wire [6:0] frac0; wire done0;
spu_depth_math d0(.clk(clk),.rst_n(rst_n),.start(start),.a0(t0_a0),.b0(t0_b0),.a1(t0_a1),.b1(t0_b1),.a2(t0_a2),.b2(t0_b2),.c0(t0_c0),.c1(t0_c1),.c2(t0_c2),.z0(t0_z0),.z1(t0_z1),.z2(t0_z2),.A_z(A_z0),.B_z(B_z0),.C_z(C_z0),.frac_bits(frac0),.done(done0));
wire signed [55:0] depth0;
spu_attr_stepper a0(.clk(clk),.rst_n(rst_n),.setup(attr_setup),.a_coef(A_z0),.b_coef(B_z0),.c_coef(C_z0),.step_x(step_x),.step_y(step_y),.frac_bits(frac0),.value_out(depth0));
wire [63:0] edge_coef_1_0=64'h0000023000000000;
wire edge_inside_1_0;
spu_edge_stepper e_1_0(.clk(clk),.rst_n(rst_n),.setup(edge_setup),.coef_pack(edge_coef_1_0),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside_1_0));
wire [63:0] edge_coef_1_1=64'h01ccfe20ffffb820;
wire edge_inside_1_1;
spu_edge_stepper e_1_1(.clk(clk),.rst_n(rst_n),.setup(edge_setup),.coef_pack(edge_coef_1_1),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside_1_1));
wire [63:0] edge_coef_1_2=64'hfe34ffb000043620;
wire edge_inside_1_2;
spu_edge_stepper e_1_2(.clk(clk),.rst_n(rst_n),.setup(edge_setup),.coef_pack(edge_coef_1_2),.step_x(step_x),.step_y(step_y),.inside_out(edge_inside_1_2));
wire signed [15:0] t1_a0=16'h0000;
wire signed [15:0] t1_b0=16'h0230;
wire signed [31:0] t1_c0=32'h00000000;
wire signed [15:0] t1_a1=16'h01cc;
wire signed [15:0] t1_b1=16'hfe20;
wire signed [31:0] t1_c1=32'hffffb820;
wire signed [15:0] t1_a2=16'hfe34;
wire signed [15:0] t1_b2=16'hffb0;
wire signed [31:0] t1_c2=32'h00043620;
wire [15:0] t1_z0=16'h02bc;
wire [15:0] t1_z1=16'h0190;
wire [15:0] t1_z2=16'h0e10;
wire signed [55:0] A_z1,B_z1,C_z1;
wire [6:0] frac1; wire done1;
spu_depth_math d1(.clk(clk),.rst_n(rst_n),.start(start),.a0(t1_a0),.b0(t1_b0),.a1(t1_a1),.b1(t1_b1),.a2(t1_a2),.b2(t1_b2),.c0(t1_c0),.c1(t1_c1),.c2(t1_c2),.z0(t1_z0),.z1(t1_z1),.z2(t1_z2),.A_z(A_z1),.B_z(B_z1),.C_z(C_z1),.frac_bits(frac1),.done(done1));
wire signed [55:0] depth1;
spu_attr_stepper a1(.clk(clk),.rst_n(rst_n),.setup(attr_setup),.a_coef(A_z1),.b_coef(B_z1),.c_coef(C_z1),.step_x(step_x),.step_y(step_y),.frac_bits(frac1),.value_out(depth1));
wire cov0=(edge_inside_0_0 && edge_inside_0_1 && edge_inside_0_2), cov1=(edge_inside_1_0 && edge_inside_1_1 && edge_inside_1_2);
wire [3:0] pixel_r,pixel_g,pixel_b;
spu_depth_compare cmp(.cov0(cov0),.cov1(cov1),.depth0(depth0),.depth1(depth1),
 .r0(4'hf),.g0(4'h0),.b0(4'h0),
 .r1(4'h0),.g1(4'hf),.b1(4'h0),
 .pixel_r(pixel_r),.pixel_g(pixel_g),.pixel_b(pixel_b));
integer failures=0;
task check_point(input integer px,input integer py,input [11:0] expected); integer k; begin
 @(negedge clk); edge_setup=1; attr_setup=1; @(negedge clk); edge_setup=0; attr_setup=0;
 for(k=0;k<py;k=k+1) begin step_y=1; @(negedge clk); step_y=0; @(negedge clk); end
 for(k=0;k<px;k=k+1) begin step_x=1; @(negedge clk); step_x=0; @(negedge clk); end
 #1;
 if({pixel_r,pixel_g,pixel_b} !== expected) begin
   failures=failures+1; $display("FAIL pixel %0d,%0d expected %h got %h cov=%b%b edges=%b%b%b%b%b%b depth=%0d,%0d",
       px,py,expected,{pixel_r,pixel_g,pixel_b},cov0,cov1,
       edge_inside_0_0,edge_inside_0_1,edge_inside_0_2,edge_inside_1_0,edge_inside_1_1,edge_inside_1_2,depth0,depth1);
 end else $display("PIXEL %0d %0d %h",px,py,{pixel_r,pixel_g,pixel_b});
end endtask
initial begin
 repeat(4) @(negedge clk); rst_n=1;
 @(negedge clk); start=1; @(negedge clk); start=0;
 wait(done0 && done1);
 check_point(0,0,12'h000); check_point(10,10,12'h000); check_point(39,0,12'h000); check_point(40,0,12'hf00); check_point(41,1,12'hf00); check_point(43,23,12'h000); check_point(44,23,12'hf00); check_point(100,300,12'hf00); check_point(119,460,12'h000); check_point(120,460,12'hf00); check_point(200,100,12'hf00); check_point(303,253,12'hf00); check_point(304,253,12'hf00); check_point(319,0,12'hf00); check_point(320,0,12'hf00); check_point(320,100,12'hf00); check_point(320,268,12'hf00); check_point(321,0,12'h0f0); check_point(321,267,12'h0f0); check_point(336,253,12'h0f0); check_point(337,253,12'h0f0); check_point(400,100,12'h0f0); check_point(519,460,12'h000); check_point(520,460,12'h0f0); check_point(540,300,12'h0f0); check_point(596,23,12'h0f0); check_point(597,23,12'h000); check_point(599,1,12'h0f0); check_point(639,479,12'h000);
 if(failures==0) $display("PASS changed T1d datapath RTL");
 else $display("FAIL changed T1d datapath failures=%0d",failures);
 $finish;
end
endmodule
