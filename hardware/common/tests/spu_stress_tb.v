`timescale 1ns/1ps

module spu_stress_tb;

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
    always #3.76  clk_ghost   = ~clk_ghost;   // ~133 MHz
    always #20.83 clk_fast    = ~clk_fast;    // ~24 MHz
    always #8138  clk_piranha = ~clk_piranha; // ~61.44 kHz Heartbeat

    // 3. Test Sequence
    integer i;
    initial begin
        $dumpfile("stress_trace.vcd");
        $dumpvars(0, spu_stress_tb);

        clk_ghost = 0; clk_piranha = 0; clk_fast = 0;
        rst_n = 0;
        wr_en = 0; wr_data = 0;
        #20000;
        rst_n = 1;
        #1000;

        $display("--- Janus Guard Stress Test Start ---");
        
        // Step 1: Burst-Breath (64 Chords at 133 MHz)
        $display("Ghost OS: Burst-Hydrating 64 Chords into Artery...");
        for (i = 0; i < 64; i = i + 1) begin
            @(posedge clk_ghost); #1;
            wr_en = 1;
            // Unit chord for all 64 entries: A=1.0 (0x1000 in Q12), B=C=D=0
            // All axes receive identical stable unit vectors
            wr_data = 64'h1000_0000_0000_0000;
        end
        @(posedge clk_ghost); #1;
        wr_en = 0;

        $display("Waiting for inhale→snapshot→bloom...");
        // 64 chords across ~5 full inhale cycles (13 axes each).
        // First cycle sets inhale_primed and triggers the snapshot.
        // 30 piranha periods gives ample margin for snapshot + bloom stability.
        repeat(30) @(posedge clk_piranha);

        // Step 2: Verify Janus Bit (The Stability Sentinel)
        $display("Janus Bit Status: %b", is_janus_point);
        
        if (is_janus_point == 1'b1) begin
             $display("PASS: Janus Guard detected the identity-leak (unstable Axis 10).");
        end else begin
             $display("FAIL: Davis Gasket is blind to the instability.");
        end

        // Step 3: Check SPU-4 Coherence
        if (satellite_snaps == 4'hF) begin
             $display("PASS: Cluster Coherence maintained during stress.");
        end else begin
             $display("FAIL: Cluster synchronization lost. (Snaps: %b)", satellite_snaps);
        end

        #1000;
        $finish;
    end

endmodule
