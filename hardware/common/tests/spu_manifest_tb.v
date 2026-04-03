`timescale 1ns/1ps

module spu_manifest_tb;

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

    // 1. SPU TDM Sovereign Cluster
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
    always #3.76 clk_ghost = ~clk_ghost; // ~133 MHz
    always #20.83 clk_fast = ~clk_fast; // ~24 MHz Fast Clock
    always #8138 clk_piranha = ~clk_piranha; // ~61.44 kHz Master Pulse

    // 3. Test Sequence
    integer i;
    initial begin
        $dumpfile("manifest_trace.vcd");
        $dumpvars(0, spu_manifest_tb);

        clk_ghost=0; clk_fast=0; clk_piranha=0;
        rst_n = 0;
        wr_en = 0; wr_data = 0;
        #20000;
        rst_n = 1;
        #1000;

        $display("--- TDM Sovereignty Manifest Test Start ---");
        
        // Step 1: Ghost OS Burst-Hydration (13 axes)
        $display("Ghost OS: Hydrating 13D manifold via Artery (133 MHz)...");
        for (i = 0; i < 13; i = i + 1) begin
            @(posedge clk_ghost); #1;
            wr_en = 1;
            // Unit chord: A=1.0 (0x1000 in Q12), B=C=D=0
            // After 60° rotation: A'=B'=0.5, quadrance=1.0 → stable
            wr_data = 64'h1000_0000_0000_0000;
        end
        @(posedge clk_ghost); #1;
        wr_en = 0;

        // Step 2: Wait for inhale to consume all 13 axes and snapshot into int_mem.
        // The piranha clock runs at 61.44 kHz (16.276 µs period).
        // 15 periods covers: 13 inhale cycles + 2-FF CDC sync + 1 snapshot cycle.
        // 5 additional bloom periods ensure is_janus_point fires before we check.
        $display("Waiting for inhale→snapshot→bloom...");
        repeat(20) @(posedge clk_piranha);

        // Step 3: Observe TDM Rotation (After hydration)
        $display("Manifold State (Axis 0): %h", manifold_state[63:0]);
        $display("Janus Status: %b", is_janus_point);
        
        if (is_janus_point == 1'b1) begin
             $display("PASS: TDM Davis Gasket acknowledges bit-exact stability.");
        end else begin
             $display("FAIL: Stability parity lost in TDM loop.");
        end

        #20000;
        $finish;
    end

endmodule
