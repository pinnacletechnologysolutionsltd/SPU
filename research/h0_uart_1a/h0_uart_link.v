// UART/byte-stream bridge; connects only to an abstract endpoint.
module h0_uart_link #(parameter integer CLKS_PER_BIT=217, FRAME_TIMEOUT=50000)(
 input wire clk,rst_n,uart_rx,output wire uart_tx,
 output wire req_valid,input wire req_ready,output wire [7:0] req_cmd,
 output wire [71:0] req_payload,output wire [3:0] req_len,
 input wire done_valid,input wire [7:0] done_status,input wire [4:0] done_len,
 input wire [191:0] done_payload
);
 (* ASYNC_REG = "TRUE" *) reg activity_meta,activity_sync;
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n)begin activity_meta<=1;activity_sync<=1;end
  else begin activity_meta<=uart_rx;activity_sync<=activity_meta;end
 end
 wire [7:0] received,send_data;wire received_valid,rx_error,send_valid,tx_busy;
 h0_uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) rx(clk,rst_n,uart_rx,received,received_valid,rx_error);
 h0_uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) tx(clk,rst_n,send_valid && !tx_busy,send_data,uart_tx,tx_busy);
 h0_uart_adapter #(.FRAME_TIMEOUT(FRAME_TIMEOUT)) adapter(clk,rst_n,received_valid,received,rx_error,!activity_sync,
  send_valid,send_data,!tx_busy,req_valid,req_ready,req_cmd,req_payload,req_len,
  done_valid,done_status,done_len,done_payload);
endmodule
