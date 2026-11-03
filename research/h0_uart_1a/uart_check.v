`timescale 1ns/1ps
module uart_check;
 reg clk=0,rst_n=0,start=0,rx=1;reg [7:0] data=0;
 wire tx,busy;wire [7:0] received;wire valid,framing_error;
 integer i;reg [7:0] captured;integer count=0,errors=0;
 wire [7:0] loop_data;wire loop_valid,loop_error;integer loop_count=0;reg [7:0] loop_capture;
 h0_uart_tx #(.CLKS_PER_BIT(16)) t(clk,rst_n,start,data,tx,busy);
 h0_uart_rx #(.CLKS_PER_BIT(16)) r(clk,rst_n,rx,received,valid,framing_error);
 h0_uart_rx #(.CLKS_PER_BIT(16)) loopback(clk,rst_n,tx,loop_data,loop_valid,loop_error);
 always #5 clk=~clk;
 always @(posedge clk)begin if(valid)begin captured<=received;count<=count+1;end if(framing_error)errors<=errors+1;if(loop_valid)begin loop_count<=loop_count+1;loop_capture<=loop_data;end if(loop_error)$fatal(1,"loop framing");end
 task send_byte(input [7:0] x,input badstop);
 begin
  @(negedge clk);rx=0;repeat(16)@(negedge clk);
  for(i=0;i<8;i=i+1)begin rx=x[i];repeat(16)@(negedge clk);end
  rx=!badstop;repeat(16)@(negedge clk);rx=1;repeat(8)@(negedge clk);
 end endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  send_byte(8'ha5,0);if(count!=1 || captured!==8'ha5)$fatal(1,"RX byte");
  send_byte(8'h3c,1);if(errors!=1 || count!=1)$fatal(1,"stop error");
  @(negedge clk);data=8'h96;start=1;@(negedge clk);start=0;
  if(!busy || tx!==0)$fatal(1,"TX start");
  wait(!busy);repeat(4)@(negedge clk);if(tx!==1 || loop_count!=1 || loop_capture!==8'h96)$fatal(1,"TX loopback");
  $display("UART RX/TX FOCUSED PASS");$finish;
 end
endmodule
