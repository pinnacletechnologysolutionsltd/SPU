// CPU-BOARD-2R isolated wrapper: packetizer has no async reset; one registered TX flop drives the pin.
module cpu_board_2r_top(input wire sys_clk, raw_rst_n, output wire uart_tx);
 wire cpu_clk,cpu_rst_n,ack,complete,halted,fault;
 wire [3:0] pc,state; wire [191:0] result; wire [5:0] result_valid;
 cpu_integrate_1_top cpu(.sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.cpu_clk(cpu_clk),.cpu_rst_n(cpu_rst_n),.reset_ack(ack),.complete(complete),.halted(halted),.fault(fault),.pc(pc),.state(state),.result(result),.result_valid(result_valid));
 cpu_board_2r_packet packet(.clk(cpu_clk),.cpu_rst_n(cpu_rst_n),.halted(halted),.fault(fault),.pc(pc),.result(result),.valid(result_valid),.tx(uart_tx));
endmodule

// All state is synchronous to clk. cpu_rst_n (async-asserted by the supervisor) is only ever sampled
// through the two-flop rs; ok=rs[1]. Reset response: TX forced high within 3 clk periods of cpu_rst_n falling.
module cpu_board_2r_packet(input wire clk, cpu_rst_n, halted, fault,
 input wire [3:0] pc, input wire [191:0] result, input wire [5:0] valid, output reg tx=1'b1);
 localparam DIV=217, IDLE=2'd0, PREP=2'd1, SEND=2'd2;
 (* ASYNC_REG="TRUE" *) reg [1:0] rs=2'b00;
 wire ok = rs[1];
 reg [1:0] st=IDLE; reg is_f=0, sent_ok=0, sent_f=0;
 reg [3:0] pc_q=0, bitno=0, guard=0; reg [5:0] mask_q=0, idx=0; reg [7:0] cnt=0;
 reg [191:0] res_q=0; reg [31:0] crc=32'hffffffff; integer i;
 function [31:0] crc8(input [31:0] c, input [7:0] d); integer k; reg [31:0] x;
  begin x=c^{24'd0,d}; for(k=0;k<8;k=k+1) x = x[0] ? (x>>1)^32'hedb88320 : (x>>1); crc8=x; end endfunction
 function [7:0] bsel(input [5:0] n, input f, input [3:0] p, input [5:0] m, input [191:0] r, input [31:0] c);
  begin
   case(n)
    0: bsel=8'ha5; 1: bsel=8'h01; 2: bsel=f?8'h02:8'h01; 3: bsel={2'b00,m}; 4: bsel={4'b0000,p};
    29: bsel=~c[7:0]; 30: bsel=~c[15:8]; 31: bsel=~c[23:16]; 32: bsel=~c[31:24];
    default: bsel=r[(n-5)*8 +: 8];
   endcase
  end endfunction
 wire [7:0] cur = bsel(idx,is_f,pc_q,mask_q,res_q,crc);
 task load(input f); begin
  is_f<=f; pc_q<=pc; mask_q<=valid; crc<=32'hffffffff; idx<=0; cnt<=0; guard<=12; st<=PREP; tx<=1'b1;
  for(i=0;i<24;i=i+1) res_q[i*8 +: 8] <= valid[i/4] ? result[i*8 +: 8] : 8'h00;
 end endtask
 always @(posedge clk) begin
  rs <= {rs[0], cpu_rst_n};
  if(!ok) begin st<=IDLE; tx<=1'b1; sent_ok<=0; sent_f<=0; idx<=0; bitno<=0; cnt<=0; end
  else if(fault && !sent_f) begin load(1'b1); sent_f<=1; end
  else if(st==IDLE && halted && !fault && valid==6'h3f && !sent_ok && !sent_f) begin load(1'b0); sent_ok<=1; end
  else if(st==PREP) begin
   if(idx<29) begin crc<=crc8(crc,cur); idx<=idx+1; end
   if(cnt==DIV-1) begin cnt<=0;
    if(guard==1) begin st<=SEND; tx<=1'b0; idx<=0; bitno<=0; end else guard<=guard-1;
   end else cnt<=cnt+1;
  end else if(st==SEND) begin
   if(cnt==DIV-1) begin cnt<=0;
    if(bitno<8) begin tx<=cur[bitno[2:0]]; bitno<=bitno+1; end
    else if(bitno==8) begin tx<=1'b1; bitno<=9; end
    else if(idx==32) st<=IDLE;
    else begin idx<=idx+1; bitno<=0; tx<=1'b0; end
   end else cnt<=cnt+1;
  end
 end
endmodule
