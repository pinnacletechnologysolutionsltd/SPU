`timescale 1ns/1ps
module tb;
  reg clk=0, rst_n=0, boot_ready=0, issue_ready=0, retire_valid=0;
  reg [3:0] retire_status=0;
  reg read_valid=0, write_valid=0;
  reg [31:0] read_data=0;
  wire inst_valid, halted, fault;
  wire [63:0] inst_word;
  wire [3:0] pc, state;
  wire [191:0] result;
  wire [5:0] result_valid;
  integer i, k;
  reg [5:0] expected_valid;
  reg [191:0] expected_result;

  cpu_fetch_1b dut(.*);
  always #5 clk=~clk;

  function [63:0] expected_word(input integer n);
    case(n)
      0: expected_word=64'h7000000000000100;
      1: expected_word=64'h7000010000000000;
      2: expected_word=64'h7000020000000200;
      3: expected_word=64'h7000030000000000;
      4: expected_word=64'h7000040000000300;
      5: expected_word=64'h7000050000000000;
      6: expected_word=64'h7100000000000000;
      7: expected_word=64'h7300000000000000;
      8: expected_word=64'h7200000000000000;
      9: expected_word=64'h7200010000000000;
      10: expected_word=64'h7200020000000000;
      11: expected_word=64'h7200030000000000;
      12: expected_word=64'h7200040000000000;
      13: expected_word=64'h7200050000000000;
      default: expected_word=64'hffffffffffffffff;
    endcase
  endfunction

  task tick; begin @(posedge clk); #1; end endtask
  task check(input condition, input [255:0] message);
    begin if (condition !== 1'b1) begin
      $display("FAIL %0s pc=%0d state=%0d word=%h", message, pc, state, inst_word);
      $fatal(1, "frontend assertion");
    end end
  endtask
  task clear_inputs; begin
    @(negedge clk); issue_ready=0; retire_valid=0; retire_status=0;
    read_valid=0; write_valid=0; read_data=0;
  end endtask
  task reset_frontend; begin
    clear_inputs(); rst_n=0; boot_ready=0; tick();
    check(pc==0 && state==0 && !halted && !fault && result_valid==0 && result==0,
          "reset state");
  end endtask
  task await_issue(input integer n);
    integer timeout;
    begin
      timeout=0;
      while (!inst_valid && timeout<12) begin tick(); timeout=timeout+1; end
      check(inst_valid && state==3 && pc==n, "issue pc and valid");
      check(inst_word===expected_word(n), "instruction word");
      check(!fault && !halted, "premature terminal");
    end
  endtask

  initial begin
    reset_frontend();
    @(negedge clk); rst_n=1;
    repeat(3) begin tick(); check(state==0 && pc==0 && !inst_valid, "boot wait"); end
    @(negedge clk); boot_ready=1;
    await_issue(0);
    repeat(2) begin tick(); check(inst_valid && pc==0 && inst_word===expected_word(0), "issue stall"); end
    // Reset during an owned instruction returns the frontend to BOOT.
    reset_frontend();
    @(negedge clk); rst_n=1; boot_ready=1;
    expected_valid=0; expected_result=0;
    for(i=0;i<14;i=i+1) begin
      await_issue(i);
      @(negedge clk); issue_ready=1;
      if ((i%2)==0) begin
        retire_valid=1; read_valid=(i>=8); write_valid=(i==6 || i==7);
        read_data=32'h10203040+(i-8);
        tick();
      end else begin
        tick();
        check(state==4 && pc==i && !inst_valid, "wait retire");
        @(negedge clk); issue_ready=0;
        tick(); check(state==4 && pc==i, "retire stall");
        @(negedge clk); retire_valid=1; read_valid=(i>=8);
        write_valid=(i==6 || i==7); read_data=32'h10203040+(i-8);
        tick();
      end
      if (i>=8) begin
        expected_valid[i-8]=1;
        expected_result[32*(i-8) +: 32]=32'h10203040+(i-8);
      end
      check(state==5 && pc==i && !fault && !halted, "retire accepted");
      check(result_valid===expected_valid && result===expected_result, "read result");
      clear_inputs(); tick();
      if(i<13) check(pc==i+1 && state==1 && !halted && !fault, "pc progression");
      else check(pc==14 && state==6 && halted && !fault, "final halt");
    end
    repeat(4) begin tick(); check(pc==14 && state==6 && halted && !fault && !inst_valid,
                                  "halt holds"); end
    reset_frontend();
    @(negedge clk); rst_n=1; boot_ready=1;
    await_issue(0);
    // A retirement when no instruction is accepted is a protocol fault.
    @(negedge clk); issue_ready=0; retire_valid=1;
    tick(); check(fault && state==7 && !halted, "unexpected retire fault");
    clear_inputs(); repeat(2) begin tick(); check(fault && state==7, "fault holds"); end
    reset_frontend();
    $display("CPU_FRONTEND PASS: 14 words, handshakes, results, reset, halt, fault");
    $finish;
  end
  initial begin #200000; $fatal(1,"test timeout"); end
endmodule
