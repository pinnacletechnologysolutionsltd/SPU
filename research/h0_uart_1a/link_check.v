`timescale 1ns/1ps
module link_check;
 reg clk=0,rst_n=0,host_start=0,req_ready=1,done_valid=0;
 reg [7:0] host_byte=0;wire host_tx,host_busy,dut_tx,req_valid;
 wire [7:0] req_cmd,read_byte;wire [71:0] req_payload;wire [3:0] req_len;
 wire read_valid,read_error;reg [7:0] response[0:5];integer n=0,requests=0;
 always #5 clk=~clk;
 h0_uart_tx #(.CLKS_PER_BIT(16)) host(clk,rst_n,host_start,host_byte,host_tx,host_busy);
 h0_uart_rx #(.CLKS_PER_BIT(16)) listen(clk,rst_n,dut_tx,read_byte,read_valid,read_error);
 h0_uart_link #(.CLKS_PER_BIT(16),.FRAME_TIMEOUT(1000)) dut(clk,rst_n,host_tx,dut_tx,
  req_valid,req_ready,req_cmd,req_payload,req_len,done_valid,8'h00,5'd0,192'd0);
 always @(posedge clk)begin
  if(read_valid)begin response[n]=read_byte;n=n+1;end
  if(read_error)$fatal(1,"response UART framing");
  done_valid<=0;
  if(req_valid && req_ready)begin if(req_cmd!=4 || req_len!=0)$fatal(1,"endpoint command");requests=requests+1;done_valid<=1;end
 end
 task byte_out(input [7:0] b);begin @(negedge clk);host_byte=b;host_start=1;@(negedge clk);host_start=0;wait(!host_busy);end endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  byte_out(8'ha5);byte_out(1);byte_out(4);byte_out(0);byte_out(8'ha0);
  wait(n==6);@(negedge clk);
  if(requests!=1 || response[0]!=8'ha5 || response[1]!=1 || response[2]!=8'h84 || response[3]!=0 || response[4]!=0 || response[5]!=8'h20)$fatal(1,"serial response");
  $display("UART LINK MOCK PASS");$finish;
 end
 initial begin #1000000;$fatal(1,"timeout");end
endmodule
