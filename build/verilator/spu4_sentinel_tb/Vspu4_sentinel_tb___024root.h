// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu4_sentinel_tb.h for the primary calling header

#ifndef VERILATED_VSPU4_SENTINEL_TB___024ROOT_H_
#define VERILATED_VSPU4_SENTINEL_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu4_sentinel_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu4_sentinel_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ spu4_sentinel_tb__DOT__clk;
    CData/*0:0*/ spu4_sentinel_tb__DOT__rst_n;
    CData/*0:0*/ spu4_sentinel_tb__DOT__heartbeat;
    CData/*0:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__seeded;
    CData/*0:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_valid;
    CData/*0:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding;
    CData/*0:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_henosis_needed;
    CData/*0:0*/ __Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__rst_n__0;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    SData/*15:0*/ spu4_sentinel_tb__DOT__A_out;
    SData/*15:0*/ spu4_sentinel_tb__DOT__B_out;
    SData/*15:0*/ spu4_sentinel_tb__DOT__C_out;
    SData/*15:0*/ spu4_sentinel_tb__DOT__D_out;
    SData/*9:0*/ spu4_sentinel_tb__DOT__heartbeat_count;
    SData/*15:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_A;
    SData/*15:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_B;
    SData/*15:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_C;
    SData/*15:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_D;
    IData/*31:0*/ spu4_sentinel_tb__DOT__quadrance;
    IData/*31:0*/ spu4_sentinel_tb__DOT__quadrance_seed;
    IData/*31:0*/ spu4_sentinel_tb__DOT__u_dut__DOT__p_Q;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vspu4_sentinel_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu4_sentinel_tb___024root(Vspu4_sentinel_tb__Syms* symsp, const char* namep);
    ~Vspu4_sentinel_tb___024root();
    VL_UNCOPYABLE(Vspu4_sentinel_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
