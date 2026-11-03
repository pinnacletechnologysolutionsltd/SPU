// Experimental board boundary; exec_rst_n is a single register output.
module h0_reset_ctl(input wire clk,base_rst_n,exec_release,output reg exec_rst_n);
 always @(posedge clk or negedge base_rst_n)
  if(!base_rst_n) exec_rst_n<=0;
  else exec_rst_n<=exec_release;
endmodule
