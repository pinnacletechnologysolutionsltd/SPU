// gowin_sp_stub.v - blackbox stub for Gowin single-port BRAM primitive
// This stub allows Yosys to parse designs that instantiate the vendor BRAM.
(* blackbox *)
(* syn_black_box = "true" *)
module \$__GOWIN_SP_ #(
    parameter INIT = 0,
    parameter OPTION_RESET_MODE = "SYNC",
    parameter PORT_A_WIDTH = 64,
    parameter PORT_A_OPTION_WRITE_MODE = 0,
    parameter PORT_A_WR_BE_WIDTH = 4
) (
    input PORT_A_CLK,
    input PORT_A_CLK_EN,
    input PORT_A_WR_EN,
    input PORT_A_RD_SRST,
    input PORT_A_RD_ARST,
    input [13:0] PORT_A_ADDR,
    input [PORT_A_WR_BE_WIDTH-1:0] PORT_A_WR_BE,
    input [PORT_A_WIDTH-1:0] PORT_A_WR_DATA,
    output [PORT_A_WIDTH-1:0] PORT_A_RD_DATA
);

// blackbox: implementation provided by vendor toolchain / packer

endmodule
