// Experimental logical board top; no physical pins, transport or constraints.
module h0_board_top #(parameter DEMO_B=0)(
 input wire sys_clk,raw_rst_n,
 output wire cpu_clk,base_rst_n,exec_rst_n,complete,fault,owned,active_valid,
 output wire [5:0] result_valid,output wire [191:0] result
);
 wire begin_load,write_valid,validate,start,promoted,bank_reject;
 wire [3:0] write_addr;wire [63:0] write_data;wire [31:0] expected_crc;
 wire [5:0] result_mask;wire [191:0] result_data;
 assign result_valid=(base_rst_n && complete && !fault) ? result_mask : 6'b0;
 assign result=(base_rst_n && complete && !fault) ? result_data : 192'b0;
 cpu_rst_1b_supervisor supervisor(.sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.test_pause(1'b0),
  .halted(1'b0),.fault(1'b0),.result_valid(6'b0),.cpu_clk(cpu_clk),.cpu_rst_n(base_rst_n),
  .reset_ack(),.result_complete(),.reset_hold(),.request_pending(),.completion_latched());
 h0_demo_sequencer #(.DEMO_B(DEMO_B)) demo(.clk(cpu_clk),.base_rst_n(base_rst_n),
  .promoted(promoted),.bank_reject(bank_reject),.begin_load(begin_load),.write_valid(write_valid),
  .validate(validate),.start(start),.write_addr(write_addr),.write_data(write_data),.expected_crc(expected_crc));
 h0_phys_cpu_controller cpu(.clk(cpu_clk),.base_rst_n(base_rst_n),.start(start),.begin_load(begin_load),
  .write_valid(write_valid),.validate(validate),.write_addr(write_addr),.write_data(write_data),
  .expected_crc(expected_crc),.active_valid(active_valid),.loading(),.checking(),.bank_accept(),
  .bank_reject(bank_reject),.promoted(promoted),.owned(owned),.complete(complete),.fault(fault),
  .start_rejected(),.pc(),.result(result_data),.result_valid(result_mask),.run_id(),.cpu_rst_n(exec_rst_n));
endmodule
