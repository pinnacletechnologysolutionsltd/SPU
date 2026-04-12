`timescale 1ns/1ps

// Minimal simulation stubs to satisfy references when GPU BRAM IP is excluded
// These are intentionally small and infrequently used in smoke tests.

// rplu_bram_wrapper stub removed (real implementation present in gpu/rplu_bram_wrapper.v)

module spu4_bram_ip #(
    parameter ADDR_WIDTH = 6,
    parameter DATA_WIDTH = 64,
    parameter MEM_FILE = "hardware/common/rtl/gpu/rplu_trim.mem"
) (
    input  wire clk,
    input  wire [ADDR_WIDTH-1:0] addr,
    output reg  [DATA_WIDTH-1:0] data_out
);
    // Simple reg-array backed stub
    always @(posedge clk) begin
        data_out <= {DATA_WIDTH{1'b0}};
    end
endmodule
