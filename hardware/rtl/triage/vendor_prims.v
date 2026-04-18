`timescale 1ns/1ps

module OSER10 #(
    parameter GSREN = "false",
    parameter LSREN = "true"
)(
    input D0, input D1, input D2, input D3, input D4, input D5, input D6, input D7, input D8, input D9,
    input PCLK, input FCLK, input RESET,
    output Q
);
    assign Q = 1'b0;
endmodule

module ELVDS_OBUF(
    input I,
    output O,
    output OB
);
    assign O = I;
    assign OB = ~I;
endmodule
