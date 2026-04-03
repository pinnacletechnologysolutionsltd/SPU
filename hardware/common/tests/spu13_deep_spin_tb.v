`timescale 1ns/1ps

/*
 * spu13_deep_spin_tb.v (v1.0 - 1,000-Rotation Stress Test)
 * Objective: Verify SPU-13 13-axis manifold stability over long duration.
 * Target: spu13_core (v1.7 Strictly Phi-Gated)
 */

`include "spu_arch_defines.vh"
`include "sqr_params.vh"

module spu13_deep_spin_tb;

    reg clk, rst_n;
    wire phi_8, phi_13, phi_21, phi_heart;

    // --- 1. Clock Generation ---
    spu_sierpinski_clk u_clk (
        .clk(clk), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .heartbeat(phi_heart)
    );

    // --- 2. Memory Model (PSRAM Burst) ---
    reg [`MANIFOLD_WIDTH-1:0] psram_storage;
    reg mem_ready;
    reg mem_burst_done;
    reg [`MANIFOLD_WIDTH-1:0] mem_rd_manifold;
    
    wire mem_burst_rd, mem_burst_wr;
    wire [`MEM_ADDR_WIDTH-1:0] mem_addr;
    wire [`MANIFOLD_WIDTH-1:0] mem_wr_manifold;

    integer a;
    initial begin
        // Seed the PSRAM with unit vectors on all 13 axes
        psram_storage = 0;
        for (a = 0; a < 13; a = a + 1) begin
            psram_storage[a*64 + 48 +: 16] = 16'h1000; // Chord A = 1.0 (Q12)
        end
        mem_ready = 1;
        mem_burst_done = 0;
    end



    always @(posedge clk) begin
        if (mem_burst_rd) begin
            #400; // Simulated latency
            mem_rd_manifold <= psram_storage;
            mem_burst_done <= 1;
            #80; mem_burst_done <= 0;
        end
        if (mem_burst_wr) begin
            #400; // Simulated latency
            psram_storage <= mem_wr_manifold;
            mem_burst_done <= 1;
            #80; mem_burst_done <= 0;
        end
    end

    // --- 3. DUT: SPU-13 Sovereign Core ---
    wire is_janus_point, bloom_complete;
    wire [3:0]  artery_ptr;
    wire [63:0] artery_data;

    spu13_core uut (
        .clk(clk), .rst_n(rst_n),
        .phi_8(phi_8), .phi_13(phi_13), .phi_21(phi_21),
        .mem_ready(mem_ready),
        .mem_burst_rd(mem_burst_rd),
        .mem_burst_wr(mem_burst_wr),
        .mem_addr(mem_addr),
        .mem_rd_manifold(mem_rd_manifold),
        .mem_wr_manifold(mem_wr_manifold),
        .mem_burst_done(mem_burst_done),
        .current_axis_ptr(artery_ptr),
        .current_axis_data(artery_data),
        .manifold_out(),
        .bloom_complete(bloom_complete),
        .is_janus_point(is_janus_point)
    );

    // --- 4. Artery Monitor ---
    wire tx_out, tx_active;
    spu_artery_tx u_tx (
        .clk(clk), .phi_21(phi_21),
        .axis_ptr(artery_ptr), .axis_data(artery_data),
        .tx_out(tx_out), .tx_active(tx_active)
    );

    // --- 5. Simulation Logic ---
    initial clk = 0;
    always #41.66 clk = ~clk; // 12 MHz

    integer rotations;
    initial begin
        $dumpfile("spu13_deep_spin.vcd");
        $dumpvars(0, spu13_deep_spin_tb);
        
        rst_n = 0;
        #1000;
        rst_n = 1;
        
        $display("--- [SPU-13 Deep Spin] Manifold Seeding Complete ---");
        $display("    Initial Energy (Axis 0): %h", psram_storage[63:0]);
        
        rotations = 0;
        while (rotations < 1000) begin
            wait(phi_heart && uut.axis_ptr == 12);
            wait(!phi_heart);
            rotations = rotations + 1;
            if (rotations % 100 == 0)
                $display("[TB] Rotation %0d... Janus Status: %b", rotations, is_janus_point);
            
            if (!is_janus_point && rotations > 1) begin
                $display("[FAIL] Manifold Dissonance Detected at rotation %0d!", rotations);
                $finish;
            end
        end

        $display("--- [SPU-13 Deep Spin] 1,000 Rotations COMPLETE ---");
        $display("    Final Energy (Axis 0): %h", psram_storage[63:0]);
        $display("[PASS] SPU-13 Sovereign Stiffness Verified.");
        $finish;
    end

endmodule
