`timescale 1ns/1ps

module spu_cluster_tb;

    reg clk_ghost, clk_piranha, clk_fast;
    reg rst_n;
    
    // Ghost OS Interface
    reg wr_en;
    reg [63:0] wr_data;
    wire fifo_full;

    // Cluster Telemetry
    wire [831:0] manifold_state;
    wire [3:0]   satellite_snaps;
    wire         is_janus_point;

    // 1. SPU Sovereign Cluster
    spu_system uut (
        .clk_ghost(clk_ghost),
        .clk_piranha(clk_piranha),
        .clk_fast(clk_fast),
        .rst_n(rst_n),
        .wr_en(wr_en),
        .wr_data(wr_data),
        .fifo_full(fifo_full),
        .manifold_state(manifold_state),
        .satellite_snaps(satellite_snaps),
        .is_janus_point(is_janus_point)
    );

    // 2. Clock Generation
    always #3.76  clk_ghost    = ~clk_ghost;    // ~133 MHz
    always #20.83 clk_fast     = ~clk_fast;     // ~24 MHz
    always #8138  clk_piranha  = ~clk_piranha;  // ~61.44 kHz

    // 3. Test Sequence
    integer i;
    initial begin
        $dumpfile("cluster_trace.vcd");
        $dumpvars(0, spu_cluster_tb);

        clk_ghost = 0; clk_piranha = 0; clk_fast = 0;
        rst_n = 0;
        wr_en = 0; wr_data = 0;
        #20000;
        rst_n = 1;
        #1000;

        $display("--- Sovereign Cluster Integration Test Start ---");
        
        // Step 1: Ghost OS Hydrates the Cluster
        $display("Ghost OS: Hydrating 13D manifold via Artery...");
        for (i = 0; i < 13; i = i + 1) begin
            @(posedge clk_ghost);
            wr_en = 1;
            wr_data = 64'hC000_0000_0000_0000 + (i << 16); // Rational field pattern
        end
        @(posedge clk_ghost);
        wr_en = 0;

        // Step 2: SPU Inhales (Wait for 20 heartbeats to catch all 13 axes)
        $display("SPU-13 Mother: Inhaling and broadcasting Chords...");
        repeat(20) @(posedge clk_piranha);

        $display("Manifold State (Axis 0): %h", manifold_state[63:0]);
        $display("Manifold State (Axis 12): %h", manifold_state[831:768]);
        
        // Step 3: Check Satellites (Sentinel Lock)
        // Satellites default to SNAP lock on NOP if reset is healthy.
        #100;
        if (satellite_snaps == 4'hF) begin
             $display("PASS: SPU-13/4 Sovereign Cluster is coherent and pulse-locked.");
        end else begin
             $display("FAIL: Satellite synchronization or SNAP failure. (Snaps: %b)", satellite_snaps);
        end

        #100;
        $finish;
    end

endmodule
