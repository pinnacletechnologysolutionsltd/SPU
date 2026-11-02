`timescale 1ns/1ps
module cpu_check;
 reg clk=0,raw_rst_n=0,start=0,begin_load=0,write_valid=0,validate=0;
 reg [3:0] write_addr=0;reg [63:0] write_data=0;reg [31:0] expected_crc=0;
 wire active_valid,loading,checking,bank_accept,bank_reject,promoted,owned,complete,fault,cpu_rst_n;
 wire [3:0] pc;wire [191:0] result;wire [5:0] result_valid;wire [31:0] run_id;
 integer i,n,init_samples;
 h0_cpu_program_probe dut(.*);
 always #5 clk=~clk;
 task tick;begin @(posedge clk);#1;end endtask
 task check(input c,input [255:0] msg);begin if(c!==1'b1)begin $display("FAIL %0s pc=%0d",msg,pc);$fatal(1);end end endtask
 function [63:0] word(input integer pos,input integer which);
  case(pos)
   0:word=which==0?64'h7000000000000100:64'h7000000000000200;
   1:word=64'h7000010000000000;
   2:word=which==0?64'h7000020000000200:64'h7000020000000100;
   3:word=64'h7000030000000000;
   4:word=which==0?64'h7000040000000300:64'h7000040000000200;
   5:word=64'h7000050000000000;6:word=64'h7100000000000000;7:word=64'h7300000000000000;
   default:word=64'h7200000000000000 | (64'(pos-8)<<40);
  endcase
 endfunction
 task stage(input integer which,input reg bad_crc);
  begin
   @(negedge clk);begin_load=1;expected_crc=bad_crc?32'h12345678:(which==0?32'hfde536c7:32'h750e4cad);
   tick();check(bank_accept,"load accepted");@(negedge clk);begin_load=0;
   for(i=0;i<14;i=i+1)begin @(negedge clk);write_valid=1;write_addr=i;write_data=word(i,which);tick();check(bank_accept,"word accepted");end
   @(negedge clk);write_valid=0;validate=1;tick();@(negedge clk);validate=0;
   repeat(14)tick();
  end
 endtask
 task begin_run;begin
  @(negedge clk);start=1;tick();check(owned && !complete && !cpu_rst_n,"owned before init");
  @(negedge clk);start=0;
  init_samples=0;while(!cpu_rst_n && init_samples<5)begin tick();init_samples=init_samples+1;end
  check(init_samples>=2 && cpu_rst_n,"two reset edges");
 end endtask
 task finish_run(input integer which,input integer id);
  begin n=0;while(!complete && !fault && n<1000)begin tick();n=n+1;end
   check(complete && !fault && !owned && result_valid==6'h3f && pc==14 && run_id==id,"completion");
   if(which==0)check(result=={32'd0,32'd9,32'd0,32'd4,32'd0,32'd13},"result A");
   else check(result=={32'd0,32'd4,32'd0,32'd4,32'd0,32'd7},"result B");
  end endtask
 initial begin
  tick();@(negedge clk);raw_rst_n=1;
  stage(0,0);check(promoted && active_valid,"A promoted");
  if($test$plusargs("stale_issue")) begin
   begin_run();n=0;
   while(!(dut.state==6 && dut.ready) && n<1000)begin tick();n=n+1;end
   check(n<1000,"first issue reached");
   @(negedge clk);force dut.retire=1;force dut.status=0;force dut.rd=0;force dut.we=0;
   #1;check(!dut.valid && !dut.core.inst_accept,"stale retirement blocks issue");
   tick();check(fault && !complete && pc==0 && result_valid==0,"stale retirement rejected");
   release dut.retire;release dut.status;release dut.rd;release dut.we;
   $display("CONTROL stale_issue PASS");
   $finish;
  end
  if($test$plusargs("before_accept")) begin
   begin_run();n=0;
   while(dut.state!=6 && n<1000)begin tick();n=n+1;end
   check(n<1000,"issue reached");
   @(negedge clk);force dut.ready=0;force dut.retire=1;#1;
   check(!dut.valid && !dut.core.inst_accept,"preaccept blocks issue");
   tick();check(fault && !complete && pc==0 && result_valid==0,"preaccept retirement rejected");
   release dut.ready;release dut.retire;
   $display("CONTROL before_accept PASS");
   $finish;
  end
  if($test$plusargs("duplicate")) begin
   begin_run();n=0;
   while(!(dut.state==8 && pc==0) && n<1000)begin tick();n=n+1;end
   check(n<1000,"first retirement reached");
   @(negedge clk);force dut.retire=1;tick();
   check(fault && !complete && pc==0 && result_valid==0,"duplicate retirement rejected");
   release dut.retire;
   $display("CONTROL duplicate PASS");
   $finish;
  end
  begin_run();
  @(negedge clk);begin_load=1;tick();check(bank_reject && owned,"busy load rejected");@(negedge clk);begin_load=0;
  finish_run(0,1);
  stage(1,1);check(bank_reject && active_valid && !promoted,"bad identity rejected");
  begin_run();finish_run(0,2);
  stage(1,0);check(promoted,"B promoted");begin_run();finish_run(1,3);
  // Physical reset while loading invalidates the image and stale result.
  @(negedge clk);begin_load=1;tick();@(negedge clk);begin_load=0;raw_rst_n=0;#1;
  check(!active_valid && !complete && result_valid==0 && !owned,"physical reset invalidates");
  @(negedge clk);raw_rst_n=1;stage(0,0);check(promoted,"reload after reset");
  begin_run(); n=0;while(!(pc==7 && dut.busy) && n<1000)begin tick();n=n+1;end
  check(n<1000,"multiply reached");@(negedge clk);raw_rst_n=0;#1;
  check(!complete && !owned && result_valid==0 && !active_valid,"reset during multiply");
  @(negedge clk);raw_rst_n=1;stage(0,0);begin_run();
  n=0;while(result_valid==0 && n<1000)begin tick();n=n+1;end
  check(n<1000 && owned && !complete,"partial result reached");
  @(negedge clk);raw_rst_n=0;start=1;#1;
  check(!complete && !owned && result_valid==0 && !active_valid,"reset during result and start");
  tick();check(!owned && !complete,"physical reset priority");
  @(negedge clk);start=0;raw_rst_n=1;stage(0,0);begin_run();
  n=0;while(dut.state!=3 && n<20)begin tick();n=n+1;end
  check(n<20,"wait boot reached");
  @(negedge clk);force dut.retire=1;tick();
  check(fault && !complete,"stale retirement during initialization faults");
  release dut.retire;
  $display("H0_RTL_1F EXPERIMENTAL PASS");$finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
