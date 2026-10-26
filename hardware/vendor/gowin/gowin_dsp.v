// Gowin DSP primitive declarations used by Yosys hierarchy checks.
// Implemented by the Gowin backend/device library during technology mapping.

(* blackbox *)
module MULT27X36 (
    output [62:0] DOUT,
    input  [26:0] A,
    input  [35:0] B,
    input  [25:0] D,
    input  [1:0]  CLK,
    input  [1:0]  CE,
    input  [1:0]  RESET,
    input         PSEL,
    input         PADDSUB
);
endmodule
