`timescale 1ns/1ps
module edge_check;
 reg clk=0,rst_n=0,rx_valid=0,rx_error=0,rx_activity=0,req_ready=0,done_valid=0;
 reg [7:0] rx_data=0;wire tx_valid;wire [7:0] tx_data,req_cmd;wire req_valid;wire [71:0] req_payload;wire [3:0] req_len;
 reg [7:0] out[0:31];integer count=0;
 always #5 clk=~clk;
 h0_uart_adapter #(.FRAME_TIMEOUT(30)) dut(clk,rst_n,rx_valid,rx_data,rx_error,rx_activity,tx_valid,tx_data,1'b1,
 req_valid,req_ready,req_cmd,req_payload,req_len,done_valid,8'h00,5'd25,192'd0);
 always @(posedge clk)if(tx_valid)begin out[count]=tx_data;count=count+1;end
 task send(input [7:0] b);begin @(negedge clk);rx_data=b;rx_valid=1;@(negedge clk);rx_valid=0;end endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  send(8'ha5);send(1);send(4);send(0);send(8'ha0);wait(req_valid);
  @(negedge clk);req_ready=1;done_valid=1;@(negedge clk);req_ready=0;done_valid=0;
  wait(count>=6);@(negedge clk);if(out[3]!=2 || out[4]!=0)$fatal(1,"simultaneous oversized response");
  wait(dut.state==0);count=0;
  send(8'ha5);send(2);wait(count>=6);@(negedge clk);rx_activity=1;repeat(50)@(negedge clk);
  if(dut.state!=10)$fatal(1,"line activity drain");
  rx_activity=0;repeat(35)@(negedge clk);if(dut.state!=0)$fatal(1,"quiet recovery");
  $display("SIMULTANEOUS LENGTH AND LINE ACTIVITY PASS");$finish;
 end
 initial begin #500000;$fatal(1,"timeout");end
endmodule
