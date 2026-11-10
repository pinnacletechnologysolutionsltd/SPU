`timescale 1ns/1ps
// GEN1-ISA-COVERAGE-2 integration bench: frozen cpu_board_2r_top, unchanged. One case per run (+CASE=<id>).
// ROM overrides are hierarchical writes at t=1 ns, after every t=0 initial block, while raw_rst_n is held low
// (fetch in BOOT); every overridden word is read back before reset is released at 200 ns.
// At 150 ns, still under reset and after counted cpu_clk edges, PRECOND checks reset, BOOT and every overridden word.
// Output lines: OVR, PRECOND, ISSUE, RETIRE, FAULT_ENTER, RX, FRAME_ERROR, FINAL, END, FAIL. Judging is done by the Python runner.
module gen1_integration_sim;
  reg clk = 0, rn = 0; wire tx;
  always #10 clk = ~clk;                                   // 50 MHz sys_clk; cpu_clk = 25 MHz
  cpu_board_2r_top u(.sys_clk(clk), .raw_rst_n(rn), .uart_tx(tx));
  localparam real BIT_NS = 217 * 40.0;                     // DIV=217 cpu_clk periods per UART bit
  integer cs = -1, nbytes = 0, k; reg no_ovr = 0; real last_t = 0.0;
  reg [63:0] want [0:15]; reg [15:0] ovr_mask = 0; reg [7:0] b;
  integer cpu_edges = 0; reg pre_ok;
  always @(posedge u.cpu_clk) cpu_edges = cpu_edges + 1;           // evidence that clock edges reached the CPU under reset
  task ovr(input integer a, input [63:0] w); begin want[a] = w; ovr_mask[a] = 1'b1; end endtask
  initial begin
    if (!$value$plusargs("CASE=%d", cs)) begin $display("FAIL no CASE"); $finish; end
    if ($test$plusargs("NO_OVERRIDE")) no_ovr = 1;         // negative-control mutant: skip the writes
    case (cs)                                               // 0=G 1=N1 2=N2 3=O 4=I 5=M1 6=M2
      0: begin ovr(0,64'h7000000000000100); ovr(2,64'h7000020000000200); ovr(4,64'h7000040000000300); end
      1: begin ovr(2,64'h700002fffffffe00); ovr(3,64'h700003ffffffff00); end
      2: begin ovr(0,64'h7000000000000000); ovr(1,64'h7000010000000100); ovr(2,64'h7000020000000000);
               ovr(3,64'h700003ffffffff00); ovr(4,64'h7000040000000000); ovr(5,64'h7000050000000100); end
      3: begin ovr(0,64'h700000ffffffff00); ovr(1,64'h7000017fffffff00); ovr(2,64'h700002ffffffff00);
               ovr(3,64'h7000037fffffff00); ovr(4,64'h7000040000000100); ovr(5,64'h7000050000000000); end
      4: begin ovr(4,64'h7000040000000000); ovr(5,64'h7000050000000000); end
      5: begin ovr(1,64'h7000010000000001); end
      6: begin ovr(7,64'h7400000000000000); end
      default: begin $display("FAIL bad CASE"); $finish; end
    endcase
    #1;
    for (k = 0; k < 16; k = k + 1) if (ovr_mask[k] && !no_ovr) u.cpu.f.rom[k] = want[k];
    for (k = 0; k < 16; k = k + 1) if (ovr_mask[k]) begin
      if (u.cpu.f.rom[k] === want[k]) $display("OVR %0d %016h OK", k, u.cpu.f.rom[k]);
      else                            $display("OVR %0d %016h MISMATCH", k, u.cpu.f.rom[k]);
    end
    #149;                                                   // t = 150 ns: reset still asserted
    pre_ok = (cpu_edges >= 2) && (rn === 1'b0) && (u.cpu.cpu_rst_n === 1'b0) && (u.cpu.f.state === 4'd0);
    for (k = 0; k < 16; k = k + 1) if (ovr_mask[k] && u.cpu.f.rom[k] !== (no_ovr ? u.cpu.f.rom[k] : want[k])) pre_ok = 0;
    if (pre_ok) $display("PRECOND OK %0d", cpu_edges);
    else $display("FAIL precondition edges=%0d rn=%b cpu_rst_n=%b state=%h", cpu_edges, rn, u.cpu.cpu_rst_n, u.cpu.f.state);
    #50 rn = 1;
  end
  // Traces sampled at posedge cpu_clk (internal observation, simulation only; the UART fault frame carries no status code):
  // ISSUE pc word on entry to ISSUE (3); RETIRE pc status for every core retirement; FAULT_ENTER from-state and pc on entry to FAULT (7).
  reg [3:0] pst = 0;
  always @(posedge u.cpu_clk) begin
    if (u.cpu.f.state == 4'd3 && pst != 4'd3) $display("ISSUE %0d %016h", u.cpu.f.pc, u.cpu.f.inst_word);
    if (u.cpu.retire) $display("RETIRE %0d %0d", u.cpu.f.pc, u.cpu.status);
    if (u.cpu.f.state == 4'd7 && pst != 4'd7) $display("FAULT_ENTER %0d %0d", pst, u.cpu.f.pc);
    pst <= u.cpu.f.state;
  end
  // UART receiver: start-bit edge, sample at bit centres, check stop bit
  always @(negedge tx) if (rn) begin : rx
    integer i;
    #(BIT_NS * 1.5);
    for (i = 0; i < 8; i = i + 1) begin b[i] = tx; if (i < 7) #(BIT_NS); end
    #(BIT_NS);
    if (tx !== 1'b1) $display("FRAME_ERROR at %0t", $time);
    $display("RX %02h", b); nbytes = nbytes + 1; last_t = $realtime;
  end
  // End: 1 ms of silence after the last byte, or 5.2 ms after release with no bytes
  initial begin
    #200;
    forever begin
      #100000;
      if ((nbytes > 0 && $realtime - last_t > 1.0e6) || $realtime > 5.2e6) begin
        $display("FINAL state=%0d pc=%0d halted=%0d fault=%0d valid=%02h", u.cpu.f.state, u.cpu.f.pc,
                 u.cpu.halted, u.cpu.fault, u.cpu.result_valid);
        $display("END bytes=%0d", nbytes); $finish;
      end
    end
  end
endmodule
