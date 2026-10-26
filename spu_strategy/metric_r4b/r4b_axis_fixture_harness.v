// r4b_axis_fixture_harness.v — PREPARED, NOT COMPILED OR RUN. Isolated SIM-path reproduction of the spu13_core wiring:
//   axis word --> spu_cross_rotor(DEVICE="SIM") --> q_prime --> davis_gate_dsp(DEVICE="SIM") --> quadrance --> (quadrance > 0)
// Input file +VEC: line0 = count; then per fixture two words: axis {a,b}, rotor {ra,rb}.  Output +OBS.
// Samples at negedge. Per fixture: s0 = immediately after inputs change (stale expected), s1 = after 1 posedge, s2 = after 2 posedges.
`timescale 1ns/1ps
module r4b_axis_fixture_tb;
    reg clk = 0, rst_n = 0; reg [63:0] axis = 0, rotor = 64'h0000100000000000;
    wire [63:0] qp, qrot; wire [31:0] quad, ivm; wire [15:0] gs; wire signed [31:0] ap, aq;
    spu_cross_rotor #(.DEVICE("SIM")) u_rot (.clk(clk), .reset(!rst_n), .q_axis(axis), .r_rotor(rotor), .q_prime(qp));
    davis_gate_dsp  #(.DEVICE("SIM")) u_gate (.clk(clk), .rst_n(rst_n), .q_vector(qp), .q_rotated(qrot),
        .quadrance(quad), .ivm_quadrance(ivm), .gasket_sum(gs), .audio_p(ap), .audio_q(aq));
    wire stable = (quad > 32'd0);                 // the spu13_core expression, rplu_dissoc held 0
    always #10 clk = ~clk;
    reg [63:0] mem [0:4095]; integer n, i, fd; reg [1023:0] vecf, obsf; reg [31:0] q0, q1, q2;
    initial begin
        if (!$value$plusargs("VEC=%s", vecf) || !$value$plusargs("OBS=%s", obsf)) begin $display("FAIL: need +VEC +OBS"); $finish; end
        for (i = 0; i < 4096; i = i + 1) mem[i] = 64'hx;
        $readmemh(vecf, mem); n = mem[0]; fd = $fopen(obsf, "w");
        repeat (3) @(negedge clk); rst_n = 1; repeat (3) @(negedge clk);
        for (i = 0; i < n; i = i + 1) begin
            axis = mem[1 + 2*i]; rotor = mem[2 + 2*i]; #1; q0 = quad;
            @(negedge clk); q1 = quad;
            @(negedge clk); q2 = quad;
            $fdisplay(fd, "F F%02d %h %h %h %h %h", i, qp, ivm, gs, quad, stable);
            $fdisplay(fd, "L F%02d %h %h %h", i, q0, q1, q2);
        end
        $fclose(fd); $display("PASS: r4b_axis_fixture_tb wrote %0d fixtures", n); $finish;
    end
endmodule
