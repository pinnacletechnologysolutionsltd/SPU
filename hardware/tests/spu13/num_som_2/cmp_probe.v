`timescale 1ns/1ps
// NUM-SOM-2 comparator probe: production spu_surd_lt_serial and the experimental signed-P fixture
// spu_surd_lt_serial_expsgn driven in lockstep by the vectors in +vec=<hexfile> (+n=<count>).
// Each line: V <idx> <lhs> <rhs> <old_lt> <new_lt> <old_latency> <new_latency>
module cmp_probe;
  reg clk=0, rst_n=0, start=0; reg [63:0] lhs, rhs;
  wire done_o, lt_o, done_n, lt_n;
  spu_surd_lt_serial        uo(.clk(clk),.rst_n(rst_n),.start(start),.lhs(lhs),.rhs(rhs),.done(done_o),.lt(lt_o));
  spu_surd_lt_serial_expsgn un(.clk(clk),.rst_n(rst_n),.start(start),.lhs(lhs),.rhs(rhs),.done(done_n),.lt(lt_n));
  always #5 clk=~clk;
  reg [127:0] vec [0:65535]; reg [1023:0] path; integer n, i, cyc, lo, ln; reg go, gn, olt, nlt;
  initial begin
    if (!$value$plusargs("n=%d", n)) n=0;
    if (!$value$plusargs("vec=%s", path)) begin $display("NOVEC"); $finish; end
    $readmemh(path, vec);
    #20 rst_n=1; repeat(2) @(posedge clk);
    for (i=0;i<n;i=i+1) begin
      @(negedge clk); lhs=vec[i][127:64]; rhs=vec[i][63:0]; start=1; cyc=0; go=0; gn=0; lo=-1; ln=-1;
      @(negedge clk); start=0;
      while (!(go && gn)) begin
        @(posedge clk); cyc=cyc+1;
        if (done_o) begin go=1; lo=cyc; olt=lt_o; end
        if (done_n) begin gn=1; ln=cyc; nlt=lt_n; end
      end
      $display("V %0d %h %h %b %b %0d %0d", i, lhs, rhs, olt, nlt, lo, ln);
    end
    $display("DONE"); $finish;
  end
endmodule
