// Experimental 8N1 receiver, sampled in the H0 cpu_clk domain.
module h0_uart_rx #(parameter integer CLKS_PER_BIT=217)(
 input wire clk,rst_n,rx,
 output reg [7:0] data, output reg valid, framing_error
);
 localparam integer CW=$clog2(CLKS_PER_BIT+1);
 localparam IDLE=0, START=1, DATA=2, STOP=3;
 (* ASYNC_REG = "TRUE" *) reg rx_meta,rx_sync;
 reg [1:0] state;
 reg [CW-1:0] counter;
 reg [2:0] bit_index;
 reg [7:0] shift;
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin rx_meta<=1;rx_sync<=1;end
  else begin rx_meta<=rx;rx_sync<=rx_meta;end
 end
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin state<=IDLE;counter<=0;bit_index<=0;shift<=0;data<=0;valid<=0;framing_error<=0;end
  else begin
   valid<=0;framing_error<=0;
   case(state)
    IDLE: if(!rx_sync) begin counter<=CLKS_PER_BIT/2-1;state<=START;end
    START: if(counter!=0)counter<=counter-1;else if(rx_sync)state<=IDLE;else begin counter<=CLKS_PER_BIT-1;bit_index<=0;state<=DATA;end
    DATA: if(counter!=0)counter<=counter-1;else begin shift[bit_index]<=rx_sync;counter<=CLKS_PER_BIT-1;if(bit_index==7)state<=STOP;else bit_index<=bit_index+1'b1;end
    STOP: if(counter!=0)counter<=counter-1;else begin if(rx_sync)begin data<=shift;valid<=1;end else framing_error<=1;state<=IDLE;end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
