// Experimental 8N1 transmitter; start is accepted only when !busy.
module h0_uart_tx #(parameter integer CLKS_PER_BIT=217)(
 input wire clk,rst_n,start,input wire [7:0] data,
 output reg tx,busy
);
 localparam integer CW=$clog2(CLKS_PER_BIT+1);
 reg [CW-1:0] counter;
 reg [3:0] position;
 reg [9:0] shift;
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin tx<=1;busy<=0;counter<=0;position<=0;shift<=10'h3ff;end
  else if(!busy) begin
   tx<=1;
   if(start)begin shift<={1'b1,data,1'b0};tx<=0;busy<=1;counter<=CLKS_PER_BIT-1;position<=0;end
  end else if(counter!=0)counter<=counter-1;
  else if(position==9)begin tx<=1;busy<=0;end
  else begin shift<={1'b1,shift[9:1]};tx<=shift[1];position<=position+1'b1;counter<=CLKS_PER_BIT-1;end
 end
endmodule
