`timescale 1ns/1ps
module embedded_check;
 reg clk=0,rst_n=0,host_start=0,done_valid=0;reg [7:0] host_byte=0;
 wire host_tx,host_busy,dut_tx,req_valid,read_valid,read_error;
 wire [7:0] req_cmd,read_byte;wire [71:0] req_payload;wire [3:0] req_len;
 integer requests=0,responses=0,i;
 always #5 clk=~clk;
 h0_uart_tx #(.CLKS_PER_BIT(16)) host(clk,rst_n,host_start,host_byte,host_tx,host_busy);
 h0_uart_rx #(.CLKS_PER_BIT(16)) listen(clk,rst_n,dut_tx,read_byte,read_valid,read_error);
 h0_uart_link #(.CLKS_PER_BIT(16),.FRAME_TIMEOUT(1000)) dut(clk,rst_n,host_tx,dut_tx,req_valid,1'b1,req_cmd,req_payload,req_len,done_valid,8'h20,5'd0,192'd0);
 always @(posedge clk)begin
  if(read_valid)responses=responses+1;
  if(read_error)$fatal(1,"response framing");
  done_valid<=0;if(req_valid)begin requests=requests+1;done_valid<=1;end
 end
 task send(input [7:0] b);begin @(negedge clk);host_byte=b;host_start=1;@(negedge clk);host_start=0;wait(!host_busy);end endtask
 task send_bad_stop;
 begin @(negedge clk);host_byte=9;host_start=1;@(negedge clk);host_start=0;
  wait(host.position==9);force host_tx=0;wait(!host_busy);release host_tx;
 end endtask
 task embedded_start;begin send(8'ha5);send(1);send(3);send(0);send(8'ha7);end endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  send(8'ha5);send(2);send(1);send(9);repeat(5)send(0);embedded_start();send(0);
  repeat(3000)@(negedge clk);
  if(requests!=0 || responses!=6)$fatal(1,"embedded bad-version request");
  // A broken stop bit mid-frame must also drain trailing embedded frames.
  send(8'ha5);send(1);send(1);send_bad_stop();repeat(8)send(0);embedded_start();
  repeat(3000)@(negedge clk);
  if(requests!=0 || responses!=12)$fatal(1,"embedded framing-error request");
  // An oversized payload continues beyond an immediate six-byte response.
  send(8'ha5);send(1);send(1);send(20);repeat(10)send(0);embedded_start();repeat(5)send(0);send(0);
  repeat(3000)@(negedge clk);
  if(requests!=0 || responses!=18)$fatal(1,"embedded oversize request");
  // A fresh request after quiet is accepted once.
  send(8'ha5);send(1);send(4);send(0);send(8'ha0);
  repeat(3000)@(negedge clk);
  if(requests!=1 || responses!=24)$fatal(1,"quiet recovery");
  $display("EMBEDDED FRAME CONTROLS PASS");$finish;
 end
 initial begin #2000000;$fatal(1,"timeout");end
endmodule
