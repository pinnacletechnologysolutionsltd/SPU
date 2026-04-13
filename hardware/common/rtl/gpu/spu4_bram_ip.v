// Vendor BRAM IP wrapper for RPLU
// Instantiates Gowin single-port BRAM primitive for synthesis; simulation uses $readmemh.
`timescale 1ns / 1ps

module spu4_bram_ip #(
    parameter ADDR_WIDTH = 6,
    parameter DATA_WIDTH = 64,
    parameter MEM_FILE = "hardware/common/rtl/gpu/rplu_trim.mem"
) (
    input  wire                     clk,
    input  wire [ADDR_WIDTH-1:0]    addr,
    output reg  [DATA_WIDTH-1:0]    data_out
);

localparam DEPTH = (1 << ADDR_WIDTH);

// Use reg-array backed RAM for both synthesis and simulation.  This avoids
// inserting IBUF/OBUF cells around the vendor primitive that can appear as
// unconstrained IO during P&R. Yosys should infer a block RAM from this
// pattern when targeting Gowin.

    (* ram_style = "block", keep = "true", dont_touch = "true" *) reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            mem[i] = {DATA_WIDTH{1'b0}};
        end
        $readmemh(MEM_FILE, mem);
    end

    always @(posedge clk) begin
        data_out <= mem[addr];
    end


endmodule
