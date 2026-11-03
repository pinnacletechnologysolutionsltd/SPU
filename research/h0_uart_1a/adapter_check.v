`timescale 1ns/1ps
module adapter_check;
 reg clk=0,rst_n=0,rx_valid=0,rx_error=0,tx_ready=1,req_ready=0,done_valid=0;
 reg [7:0] rx_data=0,done_status=0;reg [4:0] done_len=0;reg [191:0] done_payload=0;
 wire tx_valid,req_valid;wire [7:0] tx_data,req_cmd;wire [71:0] req_payload;wire [3:0] req_len;
 reg [7:0] out[0:255];integer count=0,accepted=0,i;reg [7:0] sum;
 h0_uart_adapter #(.FRAME_TIMEOUT(30)) dut(clk,rst_n,rx_valid,rx_data,rx_error,1'b0,tx_valid,tx_data,tx_ready,req_valid,req_ready,req_cmd,req_payload,req_len,done_valid,done_status,done_len,done_payload);
 always #5 clk=~clk;
 always @(posedge clk)begin if(tx_valid && tx_ready)begin out[count]=tx_data;count=count+1;end if(req_valid && req_ready)accepted=accepted+1;end
 task send(input [7:0] b);begin @(negedge clk);rx_valid=1;rx_data=b;@(negedge clk);rx_valid=0;end endtask
 task head(input [7:0] cmd,input [7:0] len);begin sum=8'ha5^8'h01^cmd^len;send(8'ha5);send(1);send(cmd);send(len);end endtask
 task wait_reply(input integer base,input [7:0] code,input [7:0] status,input [7:0] len);
 integer k;reg [7:0] c;begin
  wait(count>=base+6+len);@(negedge clk);c=0;
  if(out[base]!=8'ha5 || out[base+1]!=1 || out[base+2]!=code || out[base+3]!=status || out[base+4]!=len)$fatal(1,"response header");
  for(k=0;k<5+len;k=k+1)c=c^out[base+k];
  if(out[base+5+len]!=c)$fatal(1,"response checksum");
  wait(dut.state==0);
 end endtask
 integer base;
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  // Malformed checksum must never issue.
  base=count;head(1,4);for(i=0;i<4;i=i+1)begin send(i);sum=sum^i;end send(sum^8'h01);repeat(2)@(negedge clk);if(req_valid || accepted)$fatal(1,"bad checksum issued");wait_reply(base,8'h81,1,0);if(accepted || req_valid)$fatal(1,"bad checksum issued");
  base=count;head(1,10);for(i=0;i<11;i=i+1)send(i==2?8'ha5:0);wait_reply(base,8'h81,2,0);if(accepted || req_valid)$fatal(1,"oversize issued");
  base=count;head(1,8);for(i=0;i<8;i=i+1)begin send(i);sum=sum^i;end send(sum);repeat(2)@(negedge clk);if(req_valid)$fatal(1,"invalid LOAD length issued");wait_reply(base,8'h81,2,0);
  base=count;head(8'h55,0);send(sum);wait_reply(base,8'hd5,3,0);
  base=count;head(2,1);send(0);send(sum);wait_reply(base,8'h82,2,0);
  base=count;send(8'ha5);send(1);repeat(40)@(negedge clk);wait_reply(base,8'h80,4,0);
  base=count;send(8'ha5);send(8'h02);wait_reply(base,8'h80,1,0);
  base=count;head(1,4);send(8'h33);repeat(40)@(negedge clk);wait_reply(base,8'h81,4,0);if(req_valid)$fatal(1,"truncated issued");
  base=count;send(8'ha5);send(1);send(1);@(negedge clk);rst_n=0;@(negedge clk);rst_n=1;repeat(40)@(negedge clk);if(count!=base || req_valid)$fatal(1,"partial reset");
  // Complete frame: no response at receipt or acceptance; only endpoint completion.
  base=count;head(1,4);for(i=0;i<4;i=i+1)begin send(8'h10+i);sum=sum^(8'h10+i);end send(sum);
  wait(req_valid);if(req_cmd!=1 || req_len!=4 || req_payload[31:0]!=32'h13121110)$fatal(1,"request payload");
  repeat(4)@(negedge clk);if(count!=base || accepted!=0)$fatal(1,"early reply");
  req_ready=1;@(negedge clk);req_ready=0;repeat(4)@(negedge clk);if(count!=base || accepted!=1)$fatal(1,"accept mistaken for completion");
  done_status=8'h20;done_valid=1;@(negedge clk);done_valid=0;wait_reply(base,8'h81,8'h20,0);
  // An endpoint response exceeding 24 bytes must be refused.
  base=count;head(4,0);send(sum);wait(req_valid);@(negedge clk);req_ready=1;@(negedge clk);req_ready=0;
  done_status=0;done_len=25;done_valid=1;@(negedge clk);done_valid=0;wait(count>=base+5);if(out[base+3]!=2 || out[base+4]!=0)$fatal(1,"oversized endpoint response accepted");wait_reply(base,8'h84,2,0);
  // Reset while request is waiting must cancel it and not replay.
  base=count;head(3,0);send(sum);wait(req_valid);@(negedge clk);rst_n=0;@(negedge clk);rst_n=1;req_ready=1;repeat(5)@(negedge clk);req_ready=0;if(req_valid || accepted!=2 || count!=base)$fatal(1,"reset replay");
  // Complete successful RESULT response with 24 bytes.
  base=count;head(5,0);send(sum);wait(req_valid);@(negedge clk);req_ready=1;@(negedge clk);req_ready=0;
  done_status=0;done_len=24;done_payload=192'h0123456789abcdef0123456789abcdef0123456789abcdef;done_valid=1;@(negedge clk);done_valid=0;
  wait_reply(base,8'h85,0,24);if(out[base+5]!=8'hef || out[base+28]!=8'h01)$fatal(1,"result bytes");
  // Validate, START and STATUS each reach the endpoint with no payload.
  for(i=2;i<=4;i=i+1)begin
   base=count;head(i,0);send(sum);wait(req_valid);
   if(req_cmd!=i || req_len!=0)$fatal(1,"command identity");
   @(negedge clk);req_ready=1;@(negedge clk);req_ready=0;
   done_len=0;done_status=0;done_valid=1;@(negedge clk);done_valid=0;
   wait_reply(base,8'h80|i,0,0);
  end
  // A nine-byte LOAD word preserves its address and all data bytes.
  base=count;head(1,9);for(i=0;i<9;i=i+1)begin send(i);sum=sum^i;end send(sum);
  wait(req_valid);if(req_len!=9 || req_payload!==72'h080706050403020100)$fatal(1,"LOAD word");
  @(negedge clk);req_ready=1;@(negedge clk);req_ready=0;done_status=0;done_len=0;done_valid=1;@(negedge clk);done_valid=0;wait_reply(base,8'h81,0,0);
  base=count;send(8'ha5);send(1);@(negedge clk);rx_error=1;@(negedge clk);rx_error=0;wait_reply(base,8'h80,1,0);
  $display("ADAPTER FOCUSED PASS");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
