// Temporary constant-table test adapter; no transport or board pin assignment.
module h0_demo_sequencer #(parameter DEMO_B=0)(
 input wire clk,base_rst_n,promoted,bank_reject,
 output wire begin_load,write_valid,validate,start,
 output wire [3:0] write_addr,output reg [63:0] write_data,output wire [31:0] expected_crc
);
 localparam BEGIN_LOAD=0,WRITE=1,VALIDATE=2,WAIT_PROMOTE=3,START=4,DONE=5,ERROR=6;
 reg [2:0] state;reg [3:0] index;
 assign begin_load=state==BEGIN_LOAD;
 assign write_valid=state==WRITE;
 assign validate=state==VALIDATE;
 assign start=state==START;
 assign write_addr=index;
 assign expected_crc=DEMO_B?32'h750e4cad:32'hfde536c7;
 always @* begin
  case(index)
   0:write_data=DEMO_B?64'h7000000000000200:64'h7000000000000100;
   1:write_data=64'h7000010000000000;
   2:write_data=DEMO_B?64'h7000020000000100:64'h7000020000000200;
   3:write_data=64'h7000030000000000;
   4:write_data=DEMO_B?64'h7000040000000200:64'h7000040000000300;
   5:write_data=64'h7000050000000000;
   6:write_data=64'h7100000000000000;7:write_data=64'h7300000000000000;
   default:write_data=64'h7200000000000000 | ((index-4'd8)*64'h10000000000);
  endcase
 end
 always @(posedge clk or negedge base_rst_n) begin
  if(!base_rst_n)begin state<=BEGIN_LOAD;index<=0;end
  else if(bank_reject)state<=ERROR;
  else case(state)
   BEGIN_LOAD:state<=WRITE;
   WRITE:if(index==13)state<=VALIDATE;else index<=index+1'b1;
   VALIDATE:state<=WAIT_PROMOTE;
   WAIT_PROMOTE:if(promoted)state<=START;
   START:state<=DONE;
   default:state<=state;
  endcase
 end
endmodule
