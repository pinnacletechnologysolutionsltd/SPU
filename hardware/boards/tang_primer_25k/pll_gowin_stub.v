// pll_gowin_stub.v — rPLL blackbox stub for Yosys synthesis
// The actual rPLL primitive is instantiated by GOWIN EDA / nextpnr-gowin
// during place-and-route. Yosys treats any empty module as a blackbox.
// CC0 1.0 Universal.
(* blackbox *)
module rPLL #(
    parameter FCLKIN    = "50",
    parameter IDIV_SEL  = 0,
    parameter FBDIV_SEL = 0,
    parameter ODIV_SEL  = 8,
    parameter DEVICE    = "GW5A-25"
)(
    input  wire CLKIN,
    output wire CLKOUT,
    output wire LOCK,
    input  wire RESET, RESET_P,
    input  wire [5:0] FBDSEL, IDSEL, ODSEL,
    input  wire [3:0] PSDA, DUTYDA, FDLY
);
endmodule
