`timescale 1ns/1ps
// Independent refusal-path bench (Claude audit). Reuses GTP's serial helper style.
module refusals;
 reg sys_clk=0,raw_rst_n=0,host_start=0;reg [7:0] host_byte=0;
 wire host_tx,host_busy,dut_tx;wire [7:0] rb;wire rv,re;
 reg [7:0] response[0:63];integer n=0,i,j,requests=0,starts=0;reg [7:0] checksum;
 wire cpu_clk=dut.cpu_clk;wire base_rst_n=dut.base_rst_n;
 always #5 sys_clk=~sys_clk;
 h0_uart_cpu_top #(.CLKS_PER_BIT(16),.FRAME_TIMEOUT(1000)) dut(sys_clk,raw_rst_n,host_tx,dut_tx);
 h0_uart_tx #(.CLKS_PER_BIT(16)) host(cpu_clk,base_rst_n,host_start,host_byte,host_tx,host_busy);
 h0_uart_rx #(.CLKS_PER_BIT(16)) listen(cpu_clk,base_rst_n,dut_tx,rb,rv,re);
 always @(posedge cpu_clk) begin if(dut.req_valid && dut.req_ready)requests=requests+1;
  if(dut.start)starts=starts+1; if(rv)begin response[n]=rb;n=n+1;end if(re)$fatal(1,"UART framing");end
 task byte_out(input [7:0] b);begin @(negedge cpu_clk);host_byte=b;host_start=1;@(negedge cpu_clk);host_start=0;wait(!host_busy);end endtask
 task begin_frame(input [7:0] cmd,input [7:0] len);begin n=0;checksum=8'ha5^1^cmd^len;byte_out(8'ha5);byte_out(1);byte_out(cmd);byte_out(len);end endtask
 task payload(input [7:0] b);begin checksum=checksum^b;byte_out(b);end endtask
 task finish_frame;begin byte_out(checksum);end endtask
 task expectr(input [7:0] cmd,input [7:0] status,input integer len,input [511:0] what);
 reg [7:0] c;integer x,cycles;begin
  cycles=0;while(n<6+len && cycles<8000)begin @(negedge cpu_clk);cycles=cycles+1;end
  if(n<6+len)begin $display("FAIL %0s: response timeout",what);$fatal(1);end
  @(negedge cpu_clk);c=0;
  if(response[2]!=(cmd|8'h80) || response[3]!=status || response[4]!=len)
   begin $display("FAIL %0s: got status=%h len=%0d",what,response[3],response[4]);$fatal(1);end
  for(x=0;x<5+len;x=x+1)c=c^response[x];if(response[5+len]!=c)begin $display("FAIL %0s checksum",what);$fatal(1);end
  // error replies (parser or endpoint 0x20+) may trigger drain only for parser errors; wait out quiet anyway
  repeat(1100)@(negedge cpu_clk);
 end endtask
 task simple(input [7:0] cmd,input [7:0] status,input integer len,input [511:0] what);
  begin begin_frame(cmd,0);finish_frame();expectr(cmd,status,len,what);end endtask
 function [63:0] word(input integer pos);
  case(pos)0:word=64'h7000000000000100;1:word=64'h7000010000000000;2:word=64'h7000020000000200;
   3:word=64'h7000030000000000;4:word=64'h7000040000000300;5:word=64'h7000050000000000;
   6:word=64'h7100000000000000;7:word=64'h7300000000000000;default:word=64'h7200000000000000|(64'(pos-8)<<40);endcase
 endfunction
 task load_word(input [7:0] addr,input [63:0] w,input [7:0] status,input [511:0] what);
  begin begin_frame(1,9);payload(addr);for(j=0;j<8;j=j+1)payload(w>>(8*j));finish_frame();expectr(1,status,0,what);end endtask
 task load_crc(input [31:0] crc,input [7:0] status,input [511:0] what);
  begin begin_frame(1,4);for(j=0;j<4;j=j+1)payload(crc>>(8*j));finish_frame();expectr(1,status,0,what);end endtask
 initial begin
  #30;raw_rst_n=1;wait(base_rst_n);repeat(10)@(negedge cpu_clk);
  simple(3,8'h20,0,"START with no valid image refused");
  if(dut.owned || dut.run_id!=0)begin $display("FAIL refused START changed state");$fatal(1);end
  simple(5,8'h20,0,"RESULT before any run refused");
  simple(2,8'h20,0,"VALIDATE without load refused");
  load_word(0,word(0),8'h20,"word without begin_load refused");
  load_crc(32'hfde536c7,0,"begin load");
  load_word(8'h10,word(0),8'h20,"address 0x10 refused (no alias to 0)");
  if(dut.loading)begin $display("NOTE address refusal kept load open");end
  load_crc(32'hfde536c7,0,"restart load");
  load_word(1,word(1),8'h20,"out-of-order address refused");
  load_crc(32'hfde536c7,0,"restart load 2");
  for(i=0;i<14;i=i+1)load_word(i,word(i),0,"word");
  simple(3,8'h20,0,"START before VALIDATE refused");
  simple(2,0,0,"VALIDATE A");
  force dut.cpu.cpu.ready=0;force dut.cpu.cpu.valid=0;
  simple(3,0,0,"START A");
  if(dut.run_id!=1)begin $display("FAIL run id");$fatal(1);end
  simple(5,8'h22,0,"RESULT while owned busy");
  simple(3,8'h20,0,"second START while owned refused");
  if(dut.run_id!=1 || starts!=4)begin $display("FAIL second START changed run %0d starts %0d",dut.run_id,starts);$fatal(1);end
  load_crc(32'hfde536c7,8'h20,"LOAD while owned refused");
  if(!dut.owned || dut.run_id!=1 || !dut.active_valid)begin $display("FAIL competing LOAD changed ownership");$fatal(1);end
  simple(4,0,5,"STATUS while owned");
  if(response[5][0]!==1 || response[5][1]!==1 || response[5][2]!==0 || {response[9],response[8],response[7],response[6]}!=1)
   begin $display("FAIL STATUS owned flags=%h",response[5]);$fatal(1);end
  release dut.cpu.cpu.ready;release dut.cpu.cpu.valid;
  wait(dut.complete);
  simple(5,0,24,"RESULT A");
  if(response[5]!=13 || response[13]!=4 || response[21]!=9)begin $display("FAIL RESULT A bytes");$fatal(1);end
  simple(5,0,24,"RESULT A repeatable");
  // Wrong-length commands rejected by the parser before endpoint.
  i=requests; begin_frame(3,1);payload(0);finish_frame();expectr(3,8'h02,0,"START len1 bad length");
  if(requests!=i)begin $display("FAIL bad-length START reached endpoint");$fatal(1);end
  i=requests; begin_frame(6,0);finish_frame();expectr(6,8'h03,0,"unsupported cmd");
  if(requests!=i)begin $display("FAIL unsupported reached endpoint");$fatal(1);end
  force dut.cpu.cpu.ready=0;force dut.cpu.cpu.valid=0;
  simple(3,0,0,"START again run 2");
  if(dut.run_id!=2 || dut.complete)begin $display("FAIL rerun did not clear completion");$fatal(1);end
  simple(5,8'h22,0,"RESULT of new run busy, not stale A");
  release dut.cpu.cpu.ready;release dut.cpu.cpu.valid;
  wait(dut.complete);simple(5,0,24,"RESULT run 2");
  $display("REFUSALS PASS requests=%0d",requests);$finish;
 end
 initial begin #200000000;$fatal(1,"timeout");end
endmodule
