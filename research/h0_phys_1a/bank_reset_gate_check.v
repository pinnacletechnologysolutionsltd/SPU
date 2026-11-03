`timescale 1ns/1ps
// Force the normally reset-held admission state to isolate the reset write gate.
module bank_reset_gate_check;
 reg clk=0,base_rst_n=0,run_owned=0,begin_load=0,write_valid=0,validate=0;
 reg [3:0] write_addr=0,fetch_addr=0;reg [63:0] write_data=0;reg [31:0] expected_crc=0;
 wire active_valid,loading,checking,accepted,rejected,promoted;wire [63:0] fetch_data;
 h0_phys_program_banks dut(.*);
 always #5 clk=~clk;
 task tick;begin @(posedge clk);#1;end endtask
 task check(input c,input [255:0] msg);begin if(c!==1'b1)begin $display("FAIL %0s",msg);$fatal(1);end end endtask
 initial begin
  tick();@(negedge clk);base_rst_n=1;begin_load=1;tick();check(accepted,"begin");
  @(negedge clk);begin_load=0;write_valid=1;write_addr=0;write_data=64'h123456789abcdef0;
  tick();check(accepted && dut.bank1[0]==64'h123456789abcdef0,"seed written");
  @(negedge clk);write_valid=0;base_rst_n=0;tick();
  // In real operation these flags clear in reset. Force only these internal
  // controls so the test independently probes reset priority at the write edge.
  @(negedge clk);force dut.loading=1;force dut.count=0;force dut.active_sel=0;
  write_valid=1;write_data=64'hdeadbeefcafefeed;tick();
  check(dut.bank1[0]===64'h123456789abcdef0 && !accepted,"reset blocks normal write");
  release dut.loading;release dut.count;release dut.active_sel;
  $display("BANK_RESET_GATE PASS");$finish;
 end
 initial begin #10000;$fatal(1,"watchdog");end
endmodule
