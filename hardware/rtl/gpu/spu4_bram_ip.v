// Vendor BRAM IP wrapper for RPLU
// Inferred Block RAM for Lattice ECP5 synthesis; simulation uses $readmemh.
`timescale 1ns / 1ps

module spu4_bram_ip #(
    parameter ADDR_WIDTH = 6,
    parameter DATA_WIDTH = 64,
    parameter MEM_FILE = "hardware/rtl/arch/rplu_dual_bank.mem"
) (
    input  wire                     clk,
    input  wire                     bank_sel,  // 0=Smooth(Q3), 1=Turbulent(Q5 Fibonacci)
    input  wire [ADDR_WIDTH-1:0]    addr,
    output reg  [DATA_WIDTH-1:0]    data_out
);

// Depth is doubled: MSB is bank_sel, lower bits are the user address.
localparam DEPTH = (1 << (ADDR_WIDTH + 1));

// Use reg-array backed RAM for both synthesis and simulation. This allows
// Yosys to infer optimal DP16KD primitives for Lattice ECP5.

    (* ram_style = "block", keep = "true", dont_touch = "true" *) reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            mem[i] = {DATA_WIDTH{1'b0}};
        end
        $readmemh(MEM_FILE, mem);
    end

    always @(posedge clk) begin
        // bank_sel drives address MSB — coherent switch on any clock edge.
        // For hard coherency, gate bank_sel changes to clk_piranha (Phase 3).
        data_out <= mem[{bank_sel, addr}];
    end


endmodule
