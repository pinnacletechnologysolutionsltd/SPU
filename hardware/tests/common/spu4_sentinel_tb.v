`timescale 1ns/1ps

`include "sqr_params.vh"

module spu4_sentinel_tb;

    reg        clk, rst_n;
    reg        heartbeat;

    // Rotation Mode: 60-degree (01)
    localparam [1:0] ROT_MODE = 2'b01;


    // Seed: unit vector along B axis (to test non-axis rotation)
    // Scaling: Q12 (1.0 = 16'h1000)
    localparam [15:0] A_SEED = 16'h0000;
    localparam [15:0] B_SEED = 16'h1000; // 1.0 in Q12
    localparam [15:0] C_SEED = 16'h0000;
    localparam [15:0] D_SEED = 16'h0000;

    wire [15:0] A_out, B_out, C_out, D_out;
    wire [31:0] quadrance, quadrance_seed;
    wire        janus_stable, test_pass;
    wire [9:0]  heartbeat_count;

    spu4_sentinel u_dut (
        .clk(clk), .rst_n(rst_n),
        .heartbeat(heartbeat),
        .A_seed(A_SEED), .B_seed(B_SEED), .C_seed(C_SEED), .D_seed(D_SEED),
        .rot_mode(ROT_MODE),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .quadrance(quadrance),
        .quadrance_seed(quadrance_seed),
        .janus_stable(janus_stable),
        .heartbeat_count(heartbeat_count),
        .test_pass(test_pass)
    );

    always #41.66 clk = ~clk; // 12 MHz

    integer drift, i;

    initial begin
        $dumpfile("sentinel_sqr.vcd");
        $dumpvars(0, spu4_sentinel_tb);

        clk = 0; rst_n = 0; heartbeat = 0;
        #500; rst_n = 1; #200;

        $display("--- [Sentinel SQR] Seeding Manifold ---");
        $display("    A=%04x  B=%04x  C=%04x  D=%04x", A_SEED, B_SEED, C_SEED, D_SEED);
        $display("    Mode: 60-degree Rational SQR (Q12)");
        $display("--- [Sentinel SQR] Beginning 1,000-Heartbeat Stress Test ---");

        for (i = 0; i < 1001; i = i+1) begin
            heartbeat = 1; #83.33; heartbeat = 0;
            #(83.33 * 99);
        end
        
        // Extra wait for the last heartbeat to process
        #1000;


        $display("--- [Sentinel SQR] Results after %0d heartbeats ---", heartbeat_count);
        $display("    Final:   A=%04x  B=%04x  C=%04x  D=%04x",
                  A_out, B_out, C_out, D_out);
        $display("    Q_seed:  %08x", quadrance_seed);
        $display("    Q_now:   %08x", quadrance);

        drift = $signed(quadrance) - $signed(quadrance_seed);
        if (drift < 0) drift = -drift;
        $display("    |Drift|: %0d LSBs", drift);

        if (heartbeat_count == 10'd1000 && drift <= 4096)
            $display("[PASS] SQR Geometric Persistence VERIFIED. Janus Parity stable (drift <= 4096 LSB).");
        else if (drift > 4096)
            $display("[FAIL] JANUS PARITY DRIFT DETECTED (%0d LSBs). SQR stiffness requires recalibration.", drift);
        else
            $display("[WARN] Heartbeat count not reached: %0d/1000", heartbeat_count);

        $finish;
    end

endmodule

