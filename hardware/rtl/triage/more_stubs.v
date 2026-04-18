// Additional triage stubs: rplu_exp and spu_core
`timescale 1ns/1ps

// rplu_exp: stub removed — implementation is in hardware/common/rtl/gpu/rplu_exp.v to avoid duplicate module declarations

// spu_core: stub removed — use real implementation in hardware/common/rtl/core/spu_core.v

// spu_psram_ctrl: stub removed — use real implementation in hardware/common/rtl/prim/spu_psram_ctrl.v

// Vendor primitive stubs (OSER10, ELVDS_OBUF)
module OSER10 #(
    parameter GSREN = "false",
    parameter LSREN = "true"
)(
    input D0, input D1, input D2, input D3, input D4, input D5, input D6, input D7, input D8, input D9,
    input PCLK, input FCLK, input RESET,
    output Q
);
    // Simple placeholder: tie output low
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
