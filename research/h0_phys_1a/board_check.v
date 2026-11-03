`timescale 1ns/1ps
module board_check;
 reg sys_clk=0,raw_rst_n=0;wire ca,ba,ea,da,fa,oa,va;wire [5:0] ma;wire [191:0] ra;
 wire cb,bb,eb,db,fb,ob,vb;wire [5:0] mb;wire [191:0] rb;
 integer s,n,i,observed_a=0,observed_b=0;reg [63:0] before_word;
 h0_board_top #(.DEMO_B(0)) a(.sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.cpu_clk(ca),.base_rst_n(ba),.exec_rst_n(ea),.complete(da),.fault(fa),.owned(oa),.active_valid(va),.result_valid(ma),.result(ra));
 h0_board_top #(.DEMO_B(1)) b(.sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.cpu_clk(cb),.base_rst_n(bb),.exec_rst_n(eb),.complete(db),.fault(fb),.owned(ob),.active_valid(vb),.result_valid(mb),.result(rb));
 always #5 sys_clk=~sys_clk;
 task check(input c,input [255:0] msg);begin if(c!==1'b1)begin $display("FAIL %0s state=%0d",msg,a.cpu.state);$fatal(1);end end endtask
 task reset_board;begin
  @(negedge sys_clk);raw_rst_n=0;#1;
  check(!ba && !bb && !ea && !eb && !va && !vb && !oa && !ob && !da && !db && ma==0 && mb==0,"physical reset dominates");
  repeat(5) @(negedge sys_clk);raw_rst_n=1;
 end endtask
 task wait_state(input integer x);begin
  n=0;while(a.cpu.state!=x && n<3000)begin @(posedge ca);#1;n=n+1;end
  check(n<3000,"state coverage timeout");
 end endtask
 always @(posedge ca) if(ba) begin
  if(a.write_valid && observed_a<14)begin
   $display("PROGRAM A %0d %016h",a.write_addr,a.write_data);observed_a=observed_a+1;end
  if(b.write_valid && observed_b<14)begin
   $display("PROGRAM B %0d %016h",b.write_addr,b.write_data);observed_b=observed_b+1;end
  if((a.cpu.state==1 || a.cpu.state==2 || a.cpu.state==3) && a.cpu.valid)
   begin $display("FAIL issue during initialization");$fatal(1);end
  if(a.cpu.valid && !oa)begin $display("FAIL issue without owner");$fatal(1);end
  if(!da && (ma!==0 || ra!==0))begin $display("FAIL partial result exposed");$fatal(1);end
 end
 initial begin
  repeat(4) @(negedge sys_clk);raw_rst_n=1;
  n=0;while((!da || !db) && n<3000)begin @(posedge ca);#1;n=n+1;end
  check(n<3000 && !fa && !fb && ma==6'h3f && mb==6'h3f,"both complete");
  $display("BOARD_RESULT A %048h",ra);$display("BOARD_RESULT B %048h",rb);
  check(ra=={32'd0,32'd9,32'd0,32'd4,32'd0,32'd13},"A result");
  check(rb=={32'd0,32'd4,32'd0,32'd4,32'd0,32'd7},"B result");
  // Exercise a physical reset while each naturally reachable state is active.
  for(s=0;s<=8;s=s+1)begin reset_board();wait_state(s);reset_board();$display("RESET_STATE %0d PASS",s);end
  // Force a spurious retirement to enter FAILED, then physically reset it.
  reset_board();wait_state(3);@(negedge ca);force a.cpu.retire=1;@(posedge ca);#1;
  check(a.cpu.state==9 && fa,"failed state reached");release a.cpu.retire;
  reset_board();$display("RESET_STATE 9 PASS");
  // A failure after a partial result must not publish it at the board boundary.
  n=0;while(!(a.cpu.result_valid!=0 && a.cpu.state==7) && n<3000)begin @(posedge ca);#1;n=n+1;end
  check(n<3000,"partial result before fault");
  @(negedge ca);force a.cpu.retire=1;force a.cpu.status=4;@(posedge ca);#1;
  check(fa && !da && ma==0 && ra==0,"fault suppresses partial result");
  release a.cpu.retire;release a.cpu.status;reset_board();
  // Force a write during base reset and inspect the actual staging storage.
  before_word=a.cpu.banks.bank1[0];
  force a.write_valid=1;force a.write_addr=0;force a.write_data=64'hdeadbeefcafefeed;
  @(negedge sys_clk);raw_rst_n=0;repeat(5) @(posedge ca);#1;
  check(a.cpu.banks.bank1[0]===before_word && !a.cpu.bank_accept,"no write while base reset");
  release a.write_valid;release a.write_addr;release a.write_data;
  $display("H0_PHYS_1A BOARD PASS");$finish;
 end
 initial begin #5000000;$fatal(1,"board watchdog");end
endmodule
