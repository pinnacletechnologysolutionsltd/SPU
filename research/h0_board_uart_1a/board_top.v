// Experimental V03 board shell; no LED or external header assignments.
// At a 50 MHz input the frozen divide-by-two supervisor supplies 25 MHz.
module h0_board_uart_1a_top #(parameter integer CLKS_PER_BIT=217, FRAME_TIMEOUT=50000)(
 input wire sys_clk,raw_rst_n,uart_rx,output wire uart_tx
);
 h0_uart_cpu_top #(.CLKS_PER_BIT(CLKS_PER_BIT),.FRAME_TIMEOUT(FRAME_TIMEOUT)) board(
  .sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.uart_rx(uart_rx),.uart_tx(uart_tx));
endmodule
