// Generic rPLL stub for iverilog simulation / syntax check
module rPLL (
    input  CLKIN,
    output CLKOUT,
    output LOCK,
    input  RESET,
    input  RESET_P,
    input  [5:0] FBDSEL,
    input  [5:0] IDSEL,
    input  [5:0] ODSEL,
    input  [3:0] PSDA,
    input  [3:0] DUTYDA,
    input  [3:0] FDLY
);
    parameter FCLKIN = "27";
    parameter IDIV_SEL = 0;
    parameter FBDIV_SEL = 0;
    parameter ODIV_SEL = 0;
    parameter DEVICE = "GW1N-9C";

    reg clk_out_reg = 0;
    assign CLKOUT = CLKIN; // Passthrough for syntax check
    assign LOCK = 1'b1;
endmodule
