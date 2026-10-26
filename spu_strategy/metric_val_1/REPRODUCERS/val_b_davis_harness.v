// val_b_davis_harness.v — audit harness (own copy). Drives vectors from +VEC hex file, prints raw observations to +OBS.
// DUT parameter via -DDEV="SIM"|"GW5A". Samples at negedge to avoid races. No $dumpfile.
`timescale 1ns/1ps
module val_b_davis_tb;
    reg clk = 0, rst_n = 0; reg [63:0] qv = 0;
    wire [63:0] qrot; wire [31:0] quad, ivm; wire [15:0] gsum; wire signed [31:0] ap, aq;
    davis_gate_dsp #(.DEVICE(`DEV)) dut (.clk(clk), .rst_n(rst_n), .q_vector(qv), .q_rotated(qrot),
        .quadrance(quad), .ivm_quadrance(ivm), .gasket_sum(gsum), .audio_p(ap), .audio_q(aq));
    always #10 clk = ~clk;
    reg [63:0] mem [0:65535]; integer n, i, k, fd; reg [1023:0] vecf, obsf;
    initial begin
        if (!$value$plusargs("VEC=%s", vecf) || !$value$plusargs("OBS=%s", obsf)) begin $display("FAIL: need +VEC +OBS"); $finish; end
        for (i = 0; i < 65536; i = i + 1) mem[i] = 64'hx;
        $readmemh(vecf, mem); n = 0; while (n < 65536 && mem[n] !== 64'hx) n = n + 1;
        fd = $fopen(obsf, "w"); #1;
        repeat (3) @(negedge clk); rst_n = 1;
        // static phase: first S entries (S = mem[0] low bits) are held 6 cycles each
        // convention: entry 0 = number of static vectors, entry 1 = number of dynamic vectors; data follows
        for (i = 0; i < mem[0]; i = i + 1) begin
            qv = mem[2 + i]; repeat (6) @(negedge clk);
            $fdisplay(fd, "S %0d %h %h %h %h %h", i, qv, quad, ivm, gsum, qrot);
        end
        // dynamic phase: a new vector every cycle, observe every cycle (pipeline alignment probe)
        for (k = 0; k < mem[1]; k = k + 1) begin
            qv = mem[2 + mem[0] + k]; @(negedge clk);
            $fdisplay(fd, "D %0d %h %h %h %h %h", k, qv, quad, ivm, gsum, qrot);
        end
        repeat (4) begin qv = 0; @(negedge clk); end
        $fclose(fd); $display("PASS: val_b_davis_tb observations written (static=%0d dynamic=%0d)", mem[0], mem[1]); $finish;
    end
endmodule
