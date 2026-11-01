// Isolated RTL candidate: direct registered asynchronous reset source.
module cpu_rst_1b_supervisor(
 input wire sys_clk,raw_rst_n, test_pause,
 input wire halted,fault,input wire [5:0] result_valid,
 output reg cpu_clk=0, output wire cpu_rst_n,
 output reg reset_ack=0, output wire result_complete,
 output reg reset_hold=1, output reg request_pending=1,
 output reg completion_latched=0
);
 reg [3:0] hold_count=0;
 (* ASYNC_REG="TRUE" *) reg [1:0] release_sync=0;
 // Raw reset asynchronously sets both capture and the single reset source.
 always @(posedge sys_clk or negedge raw_rst_n)
  if(!raw_rst_n) request_pending<=1;
  else if(request_pending) request_pending<=0;
 always @(posedge sys_clk or negedge raw_rst_n) begin
  if(!raw_rst_n) begin reset_hold<=1;hold_count<=0;reset_ack<=0;end
  else begin
   reset_ack<=0;
   if(request_pending) begin reset_hold<=1;hold_count<=0;reset_ack<=1;end
   else if(reset_hold) begin
    if(hold_count==4'd7) begin reset_hold<=0;hold_count<=0;end
    else hold_count<=hold_count+1'b1;
   end
  end
 end
 always @(posedge sys_clk) begin
  if(test_pause && !request_pending && !reset_hold && cpu_rst_n) cpu_clk<=0;
  else cpu_clk<=~cpu_clk;
 end
 // Only reset_hold, a flip-flop output, drives these async reset controls.
 always @(posedge cpu_clk or posedge reset_hold) begin
  if(reset_hold) release_sync<=0;
  else release_sync<={release_sync[0],1'b1};
 end
 assign cpu_rst_n=release_sync[1];
 always @(posedge cpu_clk or posedge reset_hold) begin
  if(reset_hold) completion_latched<=0;
  else if(cpu_rst_n && halted && !fault && (&result_valid)) completion_latched<=1;
  else if(fault) completion_latched<=0;
 end
 assign result_complete=raw_rst_n && !request_pending && cpu_rst_n && completion_latched && !fault;
endmodule
