`timescale 1ns / 1ps

module spu_bram_32x64_array #(
    parameter ADDR_WIDTH = 6,
    parameter DATA_WIDTH = 32
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
    // Default all entries to zero for simulation
    for (i = 0; i < DEPTH; i = i + 1) begin
        mem[i] = {DATA_WIDTH{1'b0}};
    end
    // In a real scenario, this would be loaded from a .mem file or by a configuration interface
end

// Synchronous read to match BRAM behaviour (1-cycle latency)
always @(posedge clk) begin
    data_out <= mem[addr];
end

endmodule
