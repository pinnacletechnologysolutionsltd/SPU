`timescale 1ns/1ps
module probe_tb;
 reg clk=0,raw_rst_n=0,init_req=0,cmd_valid=0;reg [63:0] cmd_word=0;
 wire cpu_rst_n,init_done,cmd_ready,busy,retire,rd,we;wire [3:0] status;
 wire [31:0] data;wire [191:0] results;wire [5:0] result_valid;wire complete;
 reg run_owned=0,begin_load=0,write_valid=0,validate=0;reg [3:0] write_addr=0,fetch_addr=0;
 reg [63:0] write_data=0;wire active_valid,loading,checking,accepted,rejected,promoted;wire [63:0] fetch_data;
 integer i,n;
 h0_reset_core_probe dut(.*);
 h0_program_banks bank(.clk(clk),.raw_rst_n(raw_rst_n),.run_owned(run_owned),.begin_load(begin_load),
  .write_valid(write_valid),.write_addr(write_addr),.write_data(write_data),.validate(validate),
  .active_valid(active_valid),.loading(loading),.checking(checking),.accepted(accepted),
  .rejected(rejected),.promoted(promoted),.fetch_addr(fetch_addr),.fetch_data(fetch_data));
 always #5 clk=~clk;
 task tick; begin @(posedge clk);#1; end endtask
 task check(input c,input [255:0] why); begin if(c!==1'b1)begin $display("FAIL %0s",why);$fatal(1);end end endtask
 function [63:0] instr(input integer pos);
  case(pos)
   0:instr=64'h7000000000000100;1:instr=64'h7000010000000000;
   2:instr=64'h7000020000000200;3:instr=64'h7000030000000000;
   4:instr=64'h7000040000000300;5:instr=64'h7000050000000000;
   6:instr=64'h7100000000000000;7:instr=64'h7300000000000000;
   default:instr=64'h7200000000000000 | (64'(pos-8)<<40);
  endcase
 endfunction
 task wait_ready; begin n=0;while(!init_done && n<1000)begin tick();n=n+1;end check(init_done,"init timeout");end endtask
 task initialize; begin
  @(negedge clk);init_req=1;tick();check(!cpu_rst_n && !complete && result_valid==0,"init clears completion");
  @(negedge clk);init_req=0;tick();check(!cpu_rst_n,"reset edge one");
  tick();check(cpu_rst_n && !init_done,"reset edge two");wait_ready();
  check(active_valid,"bank retained");
 end endtask
 task send(input [63:0] w); begin
  n=0;while(!cmd_ready && n<1000)begin tick();n=n+1;end check(cmd_ready,"ready timeout");
  @(negedge clk);cmd_word=w;cmd_valid=1;tick();@(negedge clk);cmd_valid=0;
  n=0;while(dut.pending && n<10000)begin tick();n=n+1;end check(n<10000,"retire timeout");
 end endtask
 task start_multiply; begin
  n=0;while(!cmd_ready && n<1000)begin tick();n=n+1;end check(cmd_ready,"multiply ready");
  @(negedge clk);cmd_word=64'h7300000000000000;cmd_valid=1;tick();
  @(negedge clk);cmd_valid=0;check(busy,"multiply busy");
 end endtask
 task start_large; begin
  send(64'h7000000000000000);send(64'h7000010000000100);
  send(64'h7000020000000000);send(64'h7000030000000000);
  send(64'h7000040000000000);send(64'h7000050000000100);
  send(64'h7100000000000000);start_multiply();
 end endtask
 initial begin
  tick();@(negedge clk);raw_rst_n=1;wait_ready();
  @(negedge clk);begin_load=1;tick();@(negedge clk);begin_load=0;
  for(i=0;i<14;i=i+1)begin @(negedge clk);write_valid=1;write_addr=i;write_data=instr(i);tick();end
  @(negedge clk);write_valid=0;validate=1;tick();@(negedge clk);validate=0;
  repeat(14)tick();check(active_valid && promoted,"program loaded");
  // Tuple (2^32 + 0 sqrt3)/2^32: square needs normalization.
  start_large();
  n=0;while(!dut.core.gen_surd_cpu.u_surd.arithmetic_unit.normalizer.gcd_busy && n<50)begin tick();n=n+1;end
  check(n<50 && busy,"GCD entered");
  $display("TRACE reset during GCD busy at t=%0t",$time);
  initialize();
  check(!busy && !retire && result_valid==0 && !complete,"old activity cleared");
  check(!dut.core.gen_surd_cpu.u_surd.arithmetic_unit.normalizer.gcd_busy,"GCD reset cleared");
  @(negedge clk);fetch_addr=0;tick();check(fetch_data==instr(0),"bank after initialization");
  start_large();
  n=0;while(!dut.core.gen_surd_cpu.u_surd.arithmetic_unit.normalizer.qa_busy && n<1000)begin tick();n=n+1;end
  check(n<1000 && busy,"quotient entered");
  $display("TRACE reset during quotient busy at t=%0t",$time);
  initialize();check(!busy && !retire && !complete,"quotient activity cleared");
  check(!dut.core.gen_surd_cpu.u_surd.arithmetic_unit.normalizer.qa_busy,"quotient reset cleared");
  repeat(20) begin tick();check(!retire && !busy && !complete,"late retirement window");end
  // Interrupt a fast-path multiply and then complete a fresh 14-instruction run.
  for(i=0;i<7;i=i+1)send(instr(i));start_multiply();
  $display("TRACE reset during PRODUCT at t=%0t",$time);initialize();
  for(i=0;i<14;i=i+1)send(instr(i));
  check(complete && result_valid==6'h3f && results=={32'd0,32'd9,32'd0,32'd4,32'd0,32'd13},"fresh second result");
  $display("TRACE fresh run slices=13,0,4,0,9,0 at t=%0t",$time);
  initialize();check(!complete && result_valid==0 && results==0,"stale completion cleared");
  for(i=0;i<14;i=i+1) begin
   if(i==0) send(64'h7000000000000200);
   else if(i==2) send(64'h7000020000000100);
   else if(i==4) send(64'h7000040000000200);
   else send(instr(i));
  end
  check(complete && result_valid==6'h3f && results=={32'd0,32'd4,32'd0,32'd4,32'd0,32'd7},"second execution result");
  $display("TRACE second run slices=7,0,4,0,4,0 at t=%0t",$time);
  $display("H0_RTL_1E EXPERIMENTAL PASS");$finish;
 end
 initial begin #2000000;$fatal(1,"watchdog");end
endmodule
