// Embedded default RPLU LUT for minimal triage builds
// Parameterized small ROM containing precomputed defaults to avoid external .mem dependencies.
`timescale 1ns / 1ps
module rplu_default_lut #(
    parameter ADDR_WIDTH = 6,
    parameter DATA_WIDTH = 32
) (
    input  wire [ADDR_WIDTH-1:0] addr,
    output reg  [DATA_WIDTH-1:0] data_out
);

// Simple synchronous/asynchronous ROM implemented with an initialised reg array.
reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];
integer i;
initial begin
    // Populate with simple incremental defaults (safe, deterministic for triage).
    for (i = 0; i < (1<<ADDR_WIDTH); i = i + 1) begin
        mem[i] = i;
    end
end

always @* begin
    data_out = mem[addr];
end

endmodule
