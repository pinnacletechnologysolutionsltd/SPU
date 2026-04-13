// Extra stubs: serial multiplier needed by spi/serial davis gate
`timescale 1ns/1ps

module spu_serial_multiplier(
    input clk,
    input reset,
    input [15:0] a,
    input [15:0] b,
    input start,
    output [31:0] product,
    output ready
);
    // Simple combinational placeholder: zero product, always ready
    assign product = 32'h0;
    assign ready = 1'b1;
endmodule
