`timescale 1ns/1ps
// NUM-SOM-2 directed probe: BMU (WIDTH=18, 4 features, 7 nodes) driven as the RPLU2 pipeline drives it.
// DUT module is `BMU_MOD (default spu_som_bmu; the runner passes spu_som_bmu_expsgn for the experimental fixture).
// Preserved under hardware/tests/spu13/num_som_2/; run via run_num_som_2.py.
// Weight wiring: default = verbatim rplu_pipeline.v:162 {ONE,ZERO}; -DCTRL = control (P-weight 1, Q-weight 0).
// Input narrowing is a copy of spu13_core.v:582-587 (rplu2_narrow_rs); the core itself is not simulated.
// Inputs are 64-bit QR components {Q[63:32], P[31:0]}. Probes read BMU internals hierarchically (u.*).
`ifndef BMU_MOD
`define BMU_MOD spu_som_bmu
`endif
module numsom2_probe;
  localparam W=18, FW=36, NF=4;
  localparam [W-1:0] ZERO={W{1'b0}}, ONE={{(W-1){1'b0}},1'b1};
  reg clk=0, rst_n=0, start=0; wire done;
  reg [NF*FW-1:0] features;
  wire [NF*FW-1:0] fweights;
`ifdef CTRL
  assign fweights = {NF{ZERO, ONE}};   // control: P-weight 1, Q-weight 0
`else
  assign fweights = {NF{ONE, ZERO}};   // verbatim from rplu_pipeline.v:162
`endif
  wire bmu_valid; wire [15:0] best_id, second_id, label; wire [63:0] best_q, second_q, gap; wire has_second;
  `BMU_MOD #(.NUM_FEATURES(NF),.MAX_NODES(7),.WIDTH(W)) u(
    .clk(clk),.rst_n(rst_n),.start(start),.done(done),.features(features),.feature_weights(fweights),
    .bmu_valid(bmu_valid),.best_node_id(best_id),.second_node_id(second_id),.cluster_label(label),
    .best_q(best_q),.second_q(second_q),.confidence_gap(gap),.has_second(has_second),
    .train_we(1'b0),.train_addr(3'd0),.train_be(4'b0),.train_wdata({NF*FW{1'b0}}),.train_rdata());
  always #5 clk=~clk;
  // copy of spu13_core.v:582-587 rplu2_narrow_rs
  function [FW-1:0] narrow; input [63:0] rs; begin narrow={rs[32+:W],rs[0+:W]}; end endfunction
  integer fi; reg [63:0] cap_l, cap_r; reg [3:0] cap_s;
  always @(posedge clk) begin
    if (u.scan_state==4'd2 && u.pipe_stage==2'd2)
      for (fi=0;fi<NF;fi=fi+1)
        $display("QREG node=%0d f=%0d feat=%h w=%h fw=%h q=%h",u.scan_node,fi,u.f_reg[fi],u.w_reg[fi],u.fw_reg[fi],u.q_reg[fi]);
    if (u.scan_state==4'd2 && u.pipe_stage==2'd3)
      $display("ACC node=%0d pext=%h qext=%h",u.scan_node,u.q_accum_p_ext,u.q_accum_q_ext);
    if (u.cmp_start) begin cap_l<=u.scan_cand_q; cap_r<=u.cmp_rhs; cap_s<=u.scan_state; end
    if (u.cmp_done)
      $display("CMP st=%0d node=%0d lhs=%h rhs=%h lt=%b",cap_s,u.scan_cand_id,cap_l,cap_r,u.cmp_lt);
  end
  task run_case; input integer id; input [63:0] a,b,c,d; begin
    @(negedge clk); features={narrow(d),narrow(c),narrow(b),narrow(a)};
    $display("CASE %0d feats=%h",id,features);
    start=1; @(negedge clk); start=0; wait(done); #1;
    $display("RES %0d best=%0d valid=%b best_q=%h",id,best_id,bmu_valid,best_q);
    repeat(3) @(posedge clk);
  end endtask
  initial begin
    #20 rst_n=1; repeat(3) @(posedge clk);
    run_case(0, 64'h00000000fffffffd, 64'h00000000fffffffd, 64'h00000000fffffffd, 64'h0000000000000002);  // W_witness
    run_case(1, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // Z_zero
    run_case(2, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000003);  // NP_D3
    run_case(3, 64'h0000000000000000, 64'h0000000000000000, 64'h00000000fffffffe, 64'h0000000000000000);  // PP_C-2
    run_case(4, 64'h0000000000000000, 64'h0000000000000000, 64'h00000000fffffffe, 64'h0000000100000001);  // N6_exact0
    run_case(5, 64'h0000000000000001, 64'h0000000000000001, 64'h0000000000000000, 64'h0000000000000000);  // TIE_A1B1
    run_case(6, 64'h0000000100000000, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // QR0_reset
    run_case(7, 64'h00000001ffffffff, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // NPq_A-1,1
    run_case(8, 64'h0000000100000002, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // PPq_A2,1
    run_case(9, 64'hfffffffffffffffd, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // PPq_A-3,-1
    run_case(10, 64'hffffffff00000003, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // NPq_A3,-1
    run_case(11, 64'h0000000000040002, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // ALIAS_P
    run_case(12, 64'h0004000000000002, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // ALIAS_Q
    run_case(13, 64'h000000000001ffff, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // MAXP
    run_case(14, 64'h00000000fffe0000, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // MINP
    run_case(15, 64'h0000000000020000, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // ALIAS_MIN
    run_case(16, 64'hfffe0000fffe0000, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // SQ_WRAP
    run_case(17, 64'h0000000000010000, 64'h0000000000010000, 64'h0000000000000000, 64'h0000000000000000);  // ACC_2x2^16
    run_case(18, 64'h00000000fffe0000, 64'h00000000fffe0000, 64'h00000000fffe0000, 64'h00000000fffe0000);  // ACC_4xMIN
    run_case(19, 64'h000024f1000024f1, 64'h000024f1000024f1, 64'h000024f1000024f1, 64'h000024f1000024f1);  // B_+9457,+9457
    run_case(20, 64'h000024f1ffffdb0f, 64'h000024f1ffffdb0f, 64'h000024f1ffffdb0f, 64'h000024f1ffffdb0f);  // B_-9457,+9457
    run_case(21, 64'hffffdb0f000024f1, 64'hffffdb0f000024f1, 64'hffffdb0f000024f1, 64'hffffdb0f000024f1);  // B_+9457,-9457
    run_case(22, 64'hffffdb0fffffdb0f, 64'hffffdb0fffffdb0f, 64'hffffdb0fffffdb0f, 64'hffffdb0fffffdb0f);  // B_-9457,-9457
    run_case(23, 64'h000024f2000024f2, 64'h000024f2000024f2, 64'h000024f2000024f2, 64'h000024f2000024f2);  // B_+9458,+9458
    run_case(24, 64'h000024f2ffffdb0e, 64'h000024f2ffffdb0e, 64'h000024f2ffffdb0e, 64'h000024f2ffffdb0e);  // B_-9458,+9458
    run_case(25, 64'h000024f3000024f3, 64'h000024f3000024f3, 64'h000024f3000024f3, 64'h000024f3000024f3);  // B_+9459,+9459
    run_case(26, 64'h000024f3ffffdb0d, 64'h000024f3ffffdb0d, 64'h000024f3ffffdb0d, 64'h000024f3ffffdb0d);  // B_-9459,+9459
    run_case(27, 64'h0000251c0000251c, 64'h0000251c0000251c, 64'h0000251c0000251c, 64'h0000251c0000251c);  // B_+9500,+9500
    run_case(28, 64'h0000251cffffdae4, 64'h0000251cffffdae4, 64'h0000251cffffdae4, 64'h0000251cffffdae4);  // B_-9500,+9500
    run_case(29, 64'hffffdb0f000024f1, 64'h000024f1ffffdb0f, 64'h000024f1000024f1, 64'hffffdb0fffffdb0f);  // B_mixed
    run_case(30, 64'h000000000000b505, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // BIG_A46341
    run_case(31, 64'h000000000000b504, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // BIG_A46340
    run_case(32, 64'h00000000ffff4afb, 64'h0000000000000000, 64'h0000000000000000, 64'h0000000000000000);  // BIG_A-46341
    $display("DONE"); $finish;
  end
  initial begin #50000000; $display("TIMEOUT"); $finish; end
endmodule
