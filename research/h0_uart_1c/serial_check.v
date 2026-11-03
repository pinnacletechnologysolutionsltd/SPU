`timescale 1ns/1ps
module serial_check;
 reg sys_clk=0,raw_rst_n=0,host_start=0;reg [7:0] host_byte=0;
 wire host_tx,host_busy,dut_tx;wire [7:0] rb;wire rv,re;
 reg [7:0] response[0:63];integer n=0,i,j,k,requests=0;reg [7:0] checksum;reg [191:0] result;
 wire cpu_clk=dut.cpu_clk;wire base_rst_n=dut.base_rst_n;
 always #5 sys_clk=~sys_clk;
 h0_uart_cpu_top #(.CLKS_PER_BIT(16),.FRAME_TIMEOUT(1000)) dut(sys_clk,raw_rst_n,host_tx,dut_tx);
 h0_uart_tx #(.CLKS_PER_BIT(16)) host(cpu_clk,base_rst_n,host_start,host_byte,host_tx,host_busy);
 h0_uart_rx #(.CLKS_PER_BIT(16)) listen(cpu_clk,base_rst_n,dut_tx,rb,rv,re);
 always @(posedge cpu_clk) begin if(dut.req_valid && dut.req_ready)requests=requests+1; if(rv)begin response[n]=rb;n=n+1;end if(re)$fatal(1,"UART framing");end
 task byte_out(input [7:0] b);begin @(negedge cpu_clk);host_byte=b;host_start=1;@(negedge cpu_clk);host_start=0;wait(!host_busy);end endtask
 task begin_frame(input [7:0] cmd,input [7:0] len);begin n=0;checksum=8'ha5^1^cmd^len;byte_out(8'ha5);byte_out(1);byte_out(cmd);byte_out(len);end endtask
 task payload(input [7:0] b);begin checksum=checksum^b;byte_out(b);end endtask
 task finish_frame;begin byte_out(checksum);end endtask
 task response_check(input [7:0] cmd,input [7:0] status,input integer len);
 reg [7:0] c;integer x;begin
  wait(n>=6+len);@(negedge cpu_clk);c=0;
  if(response[0]!=8'ha5 || response[1]!=1 || response[2]!=(cmd|8'h80) || response[3]!=status || response[4]!=len)$fatal(1,"response cmd=%h status=%h len=%0d got=%h %h %h",cmd,status,len,response[2],response[3],response[4]);
  for(x=0;x<5+len;x=x+1)c=c^response[x];if(response[5+len]!=c)$fatal(1,"response checksum");
 end endtask
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
 task load_program(input integer which,input badcrc);
 reg [31:0] crc;reg [63:0] w;begin
  crc=badcrc?32'h12345678:(which==0?32'hfde536c7:32'h750e4cad);
  begin_frame(1,4);for(j=0;j<4;j=j+1)payload(crc>>(8*j));finish_frame();response_check(1,0,0);
  for(i=0;i<14;i=i+1)begin
   w=word(i,which);if(!badcrc)$display("PROGRAM %s %0d %016h",which==0?"A":"B",i,w);
   begin_frame(1,9);payload(i);for(j=0;j<8;j=j+1)payload(w>>(8*j));finish_frame();response_check(1,0,0);
  end
  begin_frame(2,0);finish_frame();response_check(2,badcrc?8'h20:0,0);
 end endtask
 task run_program(input integer which);
 begin
  if(which==0)begin force dut.cpu.cpu.ready=0;force dut.cpu.cpu.valid=0;end
  begin_frame(3,0);finish_frame();response_check(3,0,0);
  if(which==0)begin
   if(!dut.owned)$fatal(1,"owner missing state=%0d ready=%b run_id=%0d complete=%b",dut.cpu.cpu.state,dut.cpu.cpu.ready,dut.run_id,dut.complete);
   begin_frame(1,4);repeat(4)payload(0);finish_frame();response_check(1,8'h20,0);
   if(!dut.owned || !dut.active_valid || dut.run_id!=1)$fatal(1,"competing LOAD corrupted owner");
   release dut.cpu.cpu.ready;release dut.cpu.cpu.valid;
  end
  wait(dut.complete || dut.fault);if(dut.fault)$fatal(1,"CPU fault");
  begin_frame(4,0);finish_frame();response_check(4,0,5);
  if(!response[5][2])$fatal(1,"status not complete");
  begin_frame(5,0);finish_frame();response_check(5,0,24);result=0;
  for(k=0;k<24;k=k+1)result[k*8 +:8]=response[5+k];
  $display("BOARD_RESULT %s %048h",which==0?"A":"B",result);
 end endtask
 initial begin
  #30;raw_rst_n=1;wait(base_rst_n);repeat(10)@(negedge cpu_clk);
  // A bad-version frame containing a valid START must not reach the endpoint.
  byte_out(8'ha5);byte_out(2);byte_out(1);byte_out(9);repeat(5)byte_out(0);
  byte_out(8'ha5);byte_out(1);byte_out(3);byte_out(0);byte_out(8'ha7);byte_out(0);
  repeat(1500)@(negedge cpu_clk);if(requests!=0 || dut.run_id!=0)$fatal(1,"malformed frame reached endpoint");
  load_program(0,0);run_program(0);
  load_program(1,1);
  if(!dut.active_valid || !dut.complete || dut.result!={32'd0,32'd9,32'd0,32'd4,32'd0,32'd13})$fatal(1,"bad replacement corrupts A");
  load_program(1,0);run_program(1);
  // Hold the core at issue and reset an owned run with a partial UART frame.
  force dut.cpu.cpu.ready=0;force dut.cpu.cpu.valid=0;
  begin_frame(3,0);finish_frame();response_check(3,0,0);if(!dut.owned)$fatal(1,"reset test owner");
  byte_out(8'ha5);byte_out(1);byte_out(3); // incomplete START request
  @(negedge sys_clk);raw_rst_n=0;wait(!base_rst_n);repeat(3)@(negedge cpu_clk);
  if(dut.active_valid || dut.owned || dut.complete || dut.result_valid!=0 || dut.result!=0 || dut.req_valid)$fatal(1,"physical reset invalidation");
  release dut.cpu.cpu.ready;release dut.cpu.cpu.valid;
  @(negedge sys_clk);raw_rst_n=1;wait(base_rst_n);repeat(1100)@(negedge cpu_clk);
  if(dut.req_valid || dut.owned || dut.active_valid || dut.run_id!=0)$fatal(1,"reset frame replay");
  $display("SERIAL REAL CORE A/B PASS");$finish;
 end
 initial begin #100000000;$fatal(1,"timeout");end
endmodule
