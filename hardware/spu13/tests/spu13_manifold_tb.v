// spu13_manifold_tb.v (v2.0) — SPU-13 manifold test via spu_system
// Updated to use the v2.3 spu_system interface (clk_fast + memory model).
`timescale 1ns/1ps

module spu13_manifold_tb;

    reg clk_ghost, clk_piranha, clk_fast;
    reg rst_n;
    reg wr_en;
    reg [63:0] wr_data;
    wire fifo_full;
    wire [831:0] manifold_state;
    wire [3:0]   satellite_snaps;
    wire         is_janus_point;

    spu_system uut (
        .clk_ghost(clk_ghost), .clk_piranha(clk_piranha), .clk_fast(clk_fast),
        .rst_n(rst_n),
        .wr_en(wr_en), .wr_data(wr_data), .fifo_full(fifo_full),
        .manifold_state(manifold_state),
        .satellite_snaps(satellite_snaps),
        .is_janus_point(is_janus_point)
    );

    always #3.76  clk_ghost   = ~clk_ghost;
    always #20.83 clk_fast    = ~clk_fast;
    always #8138  clk_piranha = ~clk_piranha;

    integer mi;
    initial begin
        $dumpfile("spu13_trace.vcd");
        $dumpvars(0, spu13_manifold_tb);

        clk_ghost = 0; clk_fast = 0; clk_piranha = 0;
        rst_n = 0; wr_en = 0; wr_data = 0;
        #20000;
        rst_n = 1;
        #1000;

        $display("--- SPU-13 Manifold Test Start ---");

        // Hydrate 13 axes with stable identity chords
        for (mi = 0; mi < 13; mi = mi + 1) begin
            @(posedge clk_ghost);
            wr_en = 1;
            wr_data = 64'h1000_0000_0000_0000; // A=1.0 in Q12
        end
        @(posedge clk_ghost);
        wr_en = 0;

        // Wait for inhale + TDM rotation cycle
        repeat(20) @(posedge clk_piranha);

        $display("Manifold State (Axis 0): %h", manifold_state[63:0]);
        $display("Janus Status: %b", is_janus_point);

        if (is_janus_point === 1'b1 || manifold_state !== 832'h0)
            $display("PASS: SPU-13 manifold pipeline is active.");
        else
            $display("FAIL: Manifold pipeline did not engage.");

        #10000;
        $finish;
    end

endmodule
