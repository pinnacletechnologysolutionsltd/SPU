// BRAM-backed RPLU ROM wrapper
// Loads trimmed RPLU defaults from rplu_trim.mem for synthesis (Gowin will infer BRAM)
`timescale 1ns / 1ps
(* keep = "true", keep_hierarchy = "true" *) module rplu_bram_wrapper #(
    parameter ADDR_WIDTH = 6,
    parameter DATA_WIDTH = 64,
    parameter MEM_FILE = "rplu_trim.mem"
) (
    input  wire clk,
    input  wire [ADDR_WIDTH-1:0] addr,
    output reg  [DATA_WIDTH-1:0] data_out
);

localparam DEPTH = (1 << ADDR_WIDTH);

// Hint synthesis tools to map this array to block RAM on supported flows.
(* ram_style = "block", keep = "true", dont_touch = "true" *) reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
integer i;
initial begin
    // Default all entries to zero to provide safe fallbacks for simulation
    for (i = 0; i < DEPTH; i = i + 1) begin
        mem[i] = {DATA_WIDTH{1'b0}};
    end

    // Load trimmed RPLU defaults. Place rplu_trim.mem in the same directory as this file for synthesis.
    $readmemh(MEM_FILE, mem);
end

// Synchronous read to match BRAM behaviour (1-cycle latency)
always @(posedge clk) begin
    data_out <= mem[addr];
end

endmodule
