// pll_gowin_gw2a_stub.v — rPLL blackbox stub for Yosys / GW2A-18
// The actual rPLL primitive is resolved by GOWIN EDA / nextpnr-gowin
// during place-and-route.  Yosys treats the empty module as a blackbox.
// CC0 1.0 Universal.
(* blackbox *)
module rPLL #(
    parameter FCLKIN    = "27",
    parameter IDIV_SEL  = 0,
    parameter FBDIV_SEL = 15,
    parameter ODIV_SEL  = 18,
    parameter DEVICE    = "GW2A-18"
)(
    input  wire CLKIN,
    output wire CLKOUT,
    output wire LOCK,
    input  wire RESET, RESET_P,
    input  wire [5:0] FBDSEL, IDSEL, ODSEL,
    input  wire [3:0] PSDA, DUTYDA, FDLY
);
endmodule
