// Experimental single-clock virtual UART top; no board pin assignments.
module h0_uart_cpu_top #(parameter integer CLKS_PER_BIT=217, FRAME_TIMEOUT=50000)(
 input wire sys_clk,raw_rst_n,uart_rx,output wire uart_tx
);
 wire cpu_clk,base_rst_n,exec_rst_n,start,begin_load,write_valid,validate;
 wire [3:0] write_addr;wire [63:0] write_data;wire [31:0] expected_crc;
 wire active_valid,loading,checking,bank_accept,bank_reject,promoted,owned,complete,fault,start_rejected;
 wire [3:0] pc;wire [31:0] run_id;wire [191:0] result;wire [5:0] result_valid;
 wire req_valid,req_ready,done_valid;wire [7:0] req_cmd,done_status;wire [71:0] req_payload;
 wire [3:0] req_len;wire [4:0] done_len;wire [191:0] done_payload;
 h0_variable_top cpu(sys_clk,raw_rst_n,start,begin_load,write_valid,validate,write_addr,write_data,expected_crc,
  cpu_clk,base_rst_n,exec_rst_n,active_valid,loading,checking,bank_accept,bank_reject,promoted,
  owned,complete,fault,start_rejected,pc,run_id,result,result_valid);
 h0_uart_link #(.CLKS_PER_BIT(CLKS_PER_BIT),.FRAME_TIMEOUT(FRAME_TIMEOUT)) link(cpu_clk,base_rst_n,uart_rx,uart_tx,
  req_valid,req_ready,req_cmd,req_payload,req_len,done_valid,done_status,done_len,done_payload);
 h0_uart_endpoint endpoint(cpu_clk,base_rst_n,req_valid,req_ready,req_cmd,req_payload,req_len,done_valid,done_status,done_len,done_payload,
  start,begin_load,write_valid,validate,write_addr,write_data,expected_crc,active_valid,loading,checking,bank_accept,bank_reject,promoted,
  owned,complete,fault,start_rejected,run_id,result,result_valid);
endmodule
