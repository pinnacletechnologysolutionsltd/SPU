`timescale 1ns/1ps
module banks_check;
 reg clk=0, raw_rst_n=0,run_owned=0,begin_load=0,write_valid=0,validate=0;
 reg [3:0] write_addr=0,fetch_addr=0; reg [63:0] write_data=0;
 wire active_valid,loading,checking,accepted,rejected,promoted; wire [63:0] fetch_data;
 integer i;
 h0_program_banks dut(.*);
 always #5 clk=~clk;
 task tick; begin @(posedge clk); #1; end endtask
 task check(input c,input [255:0] why); begin if(c!==1'b1) begin $display("FAIL %0s",why); $fatal(1); end end endtask
 function [63:0] word(input integer n,input integer a);
  if(n<6) case(n)
   0: word=64'h7000000000000000 | (a<<8);
   2: word=64'h7000020000000200;
   4: word=64'h7000040000000300;
   default: word=64'h7000000000000000 | (64'(n)<<40);
  endcase
  else if(n==6) word=64'h7100000000000000;
  else if(n==7) word=64'h7300000000000000;
  else word=64'h7200000000000000 | (64'(n-8)<<40);
 endfunction
 task begin_stage; begin @(negedge clk); begin_load=1; tick(); check(accepted,"begin"); @(negedge clk); begin_load=0; end endtask
 task send_word(input integer n,input [63:0] w); begin
  @(negedge clk); write_valid=1;write_addr=n;write_data=w; tick();check(accepted,"write");
  @(negedge clk);write_valid=0;
 end endtask
 task start_check; begin @(negedge clk);validate=1;tick();@(negedge clk);validate=0;end endtask
 task read_a(input integer v); begin @(negedge clk);fetch_addr=0;tick();check(fetch_data==word(0,v),"active word preserved");end endtask
 initial begin
  tick(); @(negedge clk);raw_rst_n=1;
  begin_stage(); for(i=0;i<14;i=i+1)send_word(i,word(i,1)); start_check();
  repeat(13) tick(); check(checking && !active_valid,"no premature promotion");
  tick(); check(promoted && active_valid,"first promotion"); read_a(1);
  begin_stage();send_word(0,word(0,2));start_check();check(rejected && active_valid,"incomplete rejected");read_a(1);
  begin_stage();for(i=0;i<14;i=i+1)send_word(i,i==7 ? 64'h0 : word(i,2));start_check();
  repeat(14) tick();check(rejected && active_valid,"invalid replacement");read_a(1);
  begin_stage();for(i=0;i<14;i=i+1)send_word(i,word(i,2));start_check();
  repeat(13) tick();check(checking && active_valid,"verify before promote");read_a(1);
  // read_a consumed the final checking edge and promoted B.
  check(promoted && active_valid,"second promotion");read_a(2);
  @(negedge clk);run_owned=1;begin_load=1;tick();check(rejected && !loading,"owned rejects load");
  @(negedge clk);begin_load=0;run_owned=0;
  begin_stage();send_word(0,word(0,3));
  // Restarting a staging load abandons incomplete candidate but not active bank.
  begin_stage();read_a(2);
  @(negedge clk);raw_rst_n=0;#1;check(!active_valid && !loading && !checking,"physical reset invalidation");
  $display("H0_PROGRAM_BANKS PARTIAL PASS");$finish;
 end
 initial begin #100000; $fatal(1,"timeout"); end
endmodule
