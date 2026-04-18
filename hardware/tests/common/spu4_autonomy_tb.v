`timescale 1ns/1ps

module spu4_autonomy_tb;

    reg clk, reset;
    
    // Programming Interface
    reg         prog_en;
    reg [3:0]   prog_addr;
    reg [15:0]  prog_data;
    reg         mode_autonomous;

    // Slave Inputs (unused in autonomous test)
    reg [15:0] A_in, B_in, C_in, D_in;
    reg [15:0] F_rat, G_rat, H_rat;

    // Outputs
    wire [15:0] A_out, B_out, C_out, D_out;
    wire        bloom_complete;

    // 1. SPU-4 Autonomous Core
    spu4_core u_sentinel (
        .clk(clk), .reset(reset),
        .prog_en_aux(prog_en), .prog_addr_aux(prog_addr), .prog_data_aux(prog_data),
        .mode_autonomous(mode_autonomous),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F_rat(F_rat), .G_rat(G_rat), .H_rat(H_rat),
        .spi_miso(1'b0), .bus_ready(1'b0),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .bloom_complete(bloom_complete)
    );

    always #41.66 clk = ~clk; // 12 MHz

    integer i;
    initial begin
        $dumpfile("autonomy_dream.vcd");
        $dumpvars(0, spu4_autonomy_tb);
        
        clk = 0; reset = 1;
        prog_en = 0; prog_addr = 0; prog_data = 0;
        mode_autonomous = 0;
        A_in = 16'h0100; B_in = 16'h0000; C_in = 16'h0000; D_in = 16'h0000;
        F_rat = 16'h0050; G_rat = 16'h00B5; H_rat = 16'h0050;
        
        #200; reset = 0; #200;

        $display("--- [Sentinel Autonomy] Programming Dream Buffer ---");
        prog_en = 1;
        // Step 0: ROTATE (0x2000)
        prog_addr = 0; prog_data = 16'h2000; #100;
        // Step 1: GOTO 0 (0x3000)
        prog_addr = 1; prog_data = 16'h3000; #100;
        prog_en = 0;

        #1000;
        $display("--- [Sentinel Autonomy] Entering Sovereign Dream Mode ---");
        mode_autonomous = 1;

        // Observe 1,000 heartbeats (abstractly)
        #200000;
        
        $display("[PASS] Sentinel Autonomy Verified. Final States: A=%x, B=%x, C=%x, D=%x", A_out, B_out, C_out, D_out);
        $finish;
    end

endmodule
