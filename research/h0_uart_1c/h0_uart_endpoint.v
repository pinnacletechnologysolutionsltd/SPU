// Experimental bridge to the existing H0 command signals; no transport logic.
module h0_uart_endpoint(
 input wire clk,rst_n,input wire req_valid,output wire req_ready,
 input wire [7:0] req_cmd,input wire [71:0] req_payload,input wire [3:0] req_len,
 output reg done_valid,output reg [7:0] done_status,output reg [4:0] done_len,output reg [191:0] done_payload,
 output reg start,begin_load,write_valid,validate,output reg [3:0] write_addr,
 output reg [63:0] write_data,output reg [31:0] expected_crc,
 input wire active_valid,loading,checking,bank_accept,bank_reject,promoted,
 input wire owned,complete,fault,start_rejected,input wire [31:0] run_id,
 input wire [191:0] result,input wire [5:0] result_valid
);
 localparam IDLE=0,WAIT_EDGE=1,WAIT_ACK=2,WAIT_VALIDATION=3;
 reg [1:0] state;reg [7:0] command;reg [31:0] prev_run,owner_run;reg owner_valid;
 assign req_ready=(state==IDLE);
 task finish(input [7:0] status,input [4:0] len,input [191:0] payload);
 begin done_valid<=1;done_status<=status;done_len<=len;done_payload<=payload;state<=IDLE;end endtask
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin state<=IDLE;command<=0;prev_run<=0;owner_run<=0;owner_valid<=0;done_valid<=0;done_status<=0;done_len<=0;done_payload<=0;start<=0;begin_load<=0;write_valid<=0;validate<=0;write_addr<=0;write_data<=0;expected_crc<=0;end
  else begin
   done_valid<=0;start<=0;begin_load<=0;write_valid<=0;validate<=0;
   case(state)
    IDLE:if(req_valid)begin
     command<=req_cmd;
     case(req_cmd)
      1:if(req_len==4)begin expected_crc<=req_payload[31:0];begin_load<=1;state<=WAIT_EDGE;end
        else if(req_len==9 && req_payload[7:0]<14)begin write_addr<=req_payload[3:0];write_data<=req_payload[71:8];write_valid<=1;state<=WAIT_EDGE;end
        else finish(8'h20,0,0);
      2:begin validate<=1;state<=WAIT_EDGE;end
      3:begin prev_run<=run_id;start<=1;state<=WAIT_EDGE;end
      4:finish(0,5,{152'd0,run_id,2'b00,checking,loading,fault,complete,owned,active_valid});
      5:if(fault)finish(8'h21,0,0);else if(owned)finish(8'h22,0,0);
        else if(owner_valid && run_id==owner_run && complete && result_valid==6'h3f)finish(0,24,result);else finish(8'h20,0,0);
      default:finish(8'h20,0,0);
     endcase
    end
    WAIT_EDGE:state<=WAIT_ACK;
    WAIT_ACK:if(command==3)begin
      if(start_rejected)finish(8'h20,0,0);
      else if(owned && run_id==prev_run+1'b1)begin owner_valid<=1;owner_run<=run_id;finish(0,0,0);end
      else finish(8'h20,0,0);
     end else if(bank_reject)finish(8'h20,0,0);
     else if(bank_accept)begin if(command==2)state<=WAIT_VALIDATION;else finish(0,0,0);end
    WAIT_VALIDATION:if(promoted)finish(0,0,0);else if(bank_reject)finish(8'h20,0,0);
    default:state<=IDLE;
   endcase
  end
 end
endmodule
