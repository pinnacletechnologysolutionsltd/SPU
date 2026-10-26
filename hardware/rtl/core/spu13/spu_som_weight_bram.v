`timescale 1ns / 1ps

// spu_som_weight_bram.v -- BRAM-backed SOM node weight storage
//
// Four parallel BRAM slices, one per feature dimension.  Each slice stores
// MAX_NODES weight vectors as {Q, P} rational surd pairs (FEATURE_W bits).
//
// Synchronous read: 1-cycle latency, all 4 features returned in parallel.
// Synchronous write: per-feature byte-enable for training updates.
//
// Initialisation: For simulation and synthesis, the 7-node fixture weights
// are set in an initial block.  For larger maps, extend the initial block or
// hydrate through the write port; .mem files are staged for later tooling.
//
// CC0 1.0 Universal.

module spu_som_weight_bram #(
    parameter MAX_NODES = 64,
    parameter WIDTH     = 18
) (
    input  wire                                    clk,

    // Read port (synchronous, 1-cycle latency)
    // rd_data = {feat3_{Q,P}, feat2_{Q,P}, feat1_{Q,P}, feat0_{Q,P}}
    input  wire [$clog2(MAX_NODES)-1 : 0]          rd_addr,
    output wire [4 * 2 * WIDTH - 1 : 0]            rd_data,

    // Write port (per-feature byte-enable)
    input  wire                                     wr_en,
    input  wire [$clog2(MAX_NODES)-1 : 0]           wr_addr,
    input  wire [3:0]                               wr_be,   // bit N = write feature N
    input  wire [4 * 2 * WIDTH - 1 : 0]             wr_data
);

    localparam FEATURE_W = 2 * WIDTH;
    localparam DEPTH     = MAX_NODES;
    localparam ADDR_W    = $clog2(MAX_NODES);

    // Four BRAM slices, one per feature.
    (* ram_style = "block", keep = "true", dont_touch = "true" *)
        reg [FEATURE_W-1 : 0] mem0 [0:DEPTH-1];
    (* ram_style = "block", keep = "true", dont_touch = "true" *)
        reg [FEATURE_W-1 : 0] mem1 [0:DEPTH-1];
    (* ram_style = "block", keep = "true", dont_touch = "true" *)
        reg [FEATURE_W-1 : 0] mem2 [0:DEPTH-1];
    (* ram_style = "block", keep = "true", dont_touch = "true" *)
        reg [FEATURE_W-1 : 0] mem3 [0:DEPTH-1];

    // Initialisation: 7-node fixture, parameterised by WIDTH.
    // Helper: pack a {Q, P} surd into FEATURE_W bits
    function [FEATURE_W-1:0] rs;
        input signed [WIDTH-1:0] p;
        input signed [WIDTH-1:0] q;
        begin
            rs = {q, p};
        end
    endfunction

    integer ni;
    initial begin
        for (ni = 0; ni < DEPTH; ni = ni + 1) begin
            mem0[ni] = {FEATURE_W{1'b0}};
            mem1[ni] = {FEATURE_W{1'b0}};
            mem2[ni] = {FEATURE_W{1'b0}};
            mem3[ni] = {FEATURE_W{1'b0}};
        end

        // Seven-node fixture from spu_som_bmu.v
        // Node 0: all zeros
        // Node 1: feat0 = (2, 0)
        mem0[1] = rs(2, 0);
        // Node 2: feat1 = (2, 0)
        mem1[2] = rs(2, 0);
        // Node 3: feat2 = (2, 0)
        mem2[3] = rs(2, 0);
        // Node 4: feat0 = (-2, 0)
        mem0[4] = rs(-2, 0);
        // Node 5: feat1 = (-2, 0)
        mem1[5] = rs(-2, 0);
        // Node 6: feat2 = (-2, 0), feat3 = (1, 1)
        mem2[6] = rs(-2, 0);
        mem3[6] = rs(1, 1);
    end

    // Registered read data: 1-cycle latency from rd_addr to rd_data.
    reg [FEATURE_W-1 : 0] rd0;
    reg [FEATURE_W-1 : 0] rd1;
    reg [FEATURE_W-1 : 0] rd2;
    reg [FEATURE_W-1 : 0] rd3;

    always @(posedge clk) begin
        rd0 <= mem0[rd_addr];
        rd1 <= mem1[rd_addr];
        rd2 <= mem2[rd_addr];
        rd3 <= mem3[rd_addr];
    end

    initial begin
        rd0 = {FEATURE_W{1'b0}};
        rd1 = {FEATURE_W{1'b0}};
        rd2 = {FEATURE_W{1'b0}};
        rd3 = {FEATURE_W{1'b0}};
    end

    // Output: all four features in parallel.
    assign rd_data = {
        rd3,  // feature 3: {Q, P}
        rd2,  // feature 2: {Q, P}
        rd1,  // feature 1: {Q, P}
        rd0   // feature 0: {Q, P}
    };

    // Write with per-feature byte-enable.
    always @(posedge clk) begin
        if (wr_en) begin
            if (wr_be[0]) mem0[wr_addr] <= wr_data[0*FEATURE_W +: FEATURE_W];
            if (wr_be[1]) mem1[wr_addr] <= wr_data[1*FEATURE_W +: FEATURE_W];
            if (wr_be[2]) mem2[wr_addr] <= wr_data[2*FEATURE_W +: FEATURE_W];
            if (wr_be[3]) mem3[wr_addr] <= wr_data[3*FEATURE_W +: FEATURE_W];
        end
    end

endmodule
