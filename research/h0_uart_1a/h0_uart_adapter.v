// Experimental byte-stream protocol adapter; endpoint is transport-independent.
module h0_uart_adapter #(parameter integer FRAME_TIMEOUT=10000)(
 input wire clk,rst_n,
 input wire rx_valid,input wire [7:0] rx_data,input wire rx_error,input wire rx_activity,
 output reg tx_valid,output reg [7:0] tx_data,input wire tx_ready,
 output reg req_valid,input wire req_ready,output reg [7:0] req_cmd,
 output reg [71:0] req_payload,output reg [3:0] req_len,
 input wire done_valid,input wire [7:0] done_status,
 input wire [4:0] done_len,input wire [191:0] done_payload
);
 localparam [7:0] SOF=8'ha5,VERSION=8'h01;
 localparam [7:0] BAD_FRAME=8'h01,BAD_LENGTH=8'h02,UNSUPPORTED=8'h03,TIMEOUT=8'h04;
 localparam IDLE=0,VER=1,CMD=2,LEN=3,PAYLOAD=4,CHECK=5,WAIT_ACCEPT=6,WAIT_DONE=7,RESP=8,DISCARD=9,DRAIN=10;
 localparam integer TW=$clog2(FRAME_TIMEOUT+1);
 reg [3:0] state;
 reg [7:0] checksum,command,length,index,rcmd,rstatus,rlen,rindex,rsum;
 reg [8:0] discard_left;
 reg drain_pending;
 reg [71:0] payload;
 reg [191:0] rpayload;
 reg [TW-1:0] timer;
 function valid_length;
 input [7:0] cmd, len;
 begin case(cmd)
  8'h01:valid_length=(len==4 || len==9); // LOAD begin or word
  8'h02,8'h03,8'h04,8'h05:valid_length=(len==0);
  default:valid_length=0;
 endcase end endfunction
 task reply;
 input [7:0] cmd, status, size;
 input [191:0] value;
 begin drain_pending<=0;rcmd<=cmd|8'h80;rstatus<=status;rlen<=size;rpayload<=value;rindex<=0;rsum<=0;state<=RESP;req_valid<=0;end
 endtask
 task error_reply;
 input [7:0] cmd, status;
 begin reply(cmd,status,0,0);drain_pending<=1;timer<=0;end
 endtask
 always @* begin
  tx_valid=(state==RESP);tx_data=0;
  if(state==RESP) begin
   if(rindex==0)tx_data=SOF;
   else if(rindex==1)tx_data=VERSION;
   else if(rindex==2)tx_data=rcmd;
   else if(rindex==3)tx_data=rstatus;
   else if(rindex==4)tx_data=rlen;
   else if(rindex<5+rlen)tx_data=rpayload[(rindex-5)*8 +:8];
   else tx_data=rsum;
  end
 end
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n)begin state<=IDLE;drain_pending<=0;discard_left<=0;checksum<=0;command<=0;length<=0;index<=0;payload<=0;timer<=0;req_valid<=0;req_cmd<=0;req_payload<=0;req_len<=0;rcmd<=0;rstatus<=0;rlen<=0;rindex<=0;rsum<=0;rpayload<=0;end
  else begin
   if((state>=VER && state<=CHECK) || state==DISCARD)begin
    if(rx_error)begin timer<=0;error_reply(command,BAD_FRAME);end
    else if(!rx_valid && timer==FRAME_TIMEOUT-1)begin timer<=0;error_reply(command,state==DISCARD ? BAD_LENGTH : TIMEOUT);end
    else if(!rx_valid)timer<=timer+1'b1;
    else begin
     timer<=0;
     case(state)
      VER:if(rx_data!=VERSION)error_reply(0,BAD_FRAME);else begin checksum<=SOF^VERSION;state<=CMD;end
      CMD:begin command<=rx_data;checksum<=checksum^rx_data;state<=LEN;end
      LEN:begin
       length<=rx_data;checksum<=checksum^rx_data;index<=0;payload<=0;
       if(rx_data>9)begin discard_left<={1'b0,rx_data}+9'd1;state<=DISCARD;end
       else if(rx_data==0)state<=CHECK;
       else state<=PAYLOAD;
      end
      PAYLOAD:begin payload[index*8 +:8]<=rx_data;checksum<=checksum^rx_data;if(index+1==length)state<=CHECK;else index<=index+1'b1;end
      DISCARD:if(discard_left==1)error_reply(command,BAD_LENGTH);else discard_left<=discard_left-1'b1;
      CHECK:if(rx_data!=checksum)error_reply(command,BAD_FRAME);
       else if(command<1 || command>5)error_reply(command,UNSUPPORTED);
       else if(!valid_length(command,length))error_reply(command,BAD_LENGTH);
       else begin req_cmd<=command;req_len<=length[3:0];req_payload<=payload;req_valid<=1;state<=WAIT_ACCEPT;end
      default:state<=IDLE;
     endcase
    end
   end else case(state)
    IDLE:if(rx_valid && rx_data==SOF)begin checksum<=0;command<=0;timer<=0;state<=VER;end
    WAIT_ACCEPT:if(req_ready)begin req_valid<=0;if(done_valid)begin if(done_len>24)reply(req_cmd,BAD_LENGTH,0,0);else reply(req_cmd,done_status,done_len,done_payload);end else state<=WAIT_DONE;end
    WAIT_DONE:if(done_valid)begin if(done_len>24)reply(req_cmd,BAD_LENGTH,0,0);else reply(req_cmd,done_status,done_len,done_payload);end
    RESP:begin
     if(drain_pending)begin
      if(rx_valid || rx_error || rx_activity)timer<=0;
      else if(timer<FRAME_TIMEOUT-1)timer<=timer+1'b1;
     end
     if(tx_ready)begin
     if(rindex==5+rlen)begin if(drain_pending)state<=DRAIN;else state<=IDLE;rsum<=0;end
     else begin rsum<=rsum^tx_data;rindex<=rindex+1'b1;end
     end
    end
    DRAIN:if(rx_valid || rx_error || rx_activity)timer<=0;
          else if(timer==FRAME_TIMEOUT-1)begin timer<=0;drain_pending<=0;state<=IDLE;end
          else timer<=timer+1'b1;
    default:state<=IDLE;
   endcase
  end
 end
endmodule
