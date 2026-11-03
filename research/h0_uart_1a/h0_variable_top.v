// Experimental virtual interface: not a board pinout or a host transport.
module h0_variable_top(
 input wire sys_clk, raw_rst_n,
 input wire start, begin_load, write_valid, validate,
 input wire [3:0] write_addr, input wire [63:0] write_data,
 input wire [31:0] expected_crc,
 output wire cpu_clk, base_rst_n, exec_rst_n,
 output wire active_valid, loading, checking, bank_accept, bank_reject, promoted,
 output wire owned, complete, fault, start_rejected,
 output wire [3:0] pc, output wire [31:0] run_id,
 output wire [191:0] result, output wire [5:0] result_valid
);
 wire [191:0] result_raw; wire [5:0] valid_raw;
 cpu_rst_1b_supervisor supervisor(.sys_clk(sys_clk),.raw_rst_n(raw_rst_n),.test_pause(1'b0),
  .halted(1'b0),.fault(1'b0),.result_valid(6'b0),.cpu_clk(cpu_clk),.cpu_rst_n(base_rst_n),
  .reset_ack(),.result_complete(),.reset_hold(),.request_pending(),.completion_latched());
 h0_phys_cpu_controller cpu(.clk(cpu_clk),.base_rst_n(base_rst_n),.start(start),
  .begin_load(begin_load),.write_valid(write_valid),.validate(validate),.write_addr(write_addr),
  .write_data(write_data),.expected_crc(expected_crc),.active_valid(active_valid),.loading(loading),
  .checking(checking),.bank_accept(bank_accept),.bank_reject(bank_reject),.promoted(promoted),
  .owned(owned),.complete(complete),.fault(fault),.start_rejected(start_rejected),.pc(pc),
  .result(result_raw),.result_valid(valid_raw),.run_id(run_id),.cpu_rst_n(exec_rst_n));
 assign result_valid=(base_rst_n && complete && !fault) ? valid_raw : 6'b0;
 assign result=(base_rst_n && complete && !fault) ? result_raw : 192'b0;
endmodule
