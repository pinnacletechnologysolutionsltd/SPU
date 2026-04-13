// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vtang25k_smoketest_tb.h for the primary calling header

#ifndef VERILATED_VTANG25K_SMOKETEST_TB___024ROOT_H_
#define VERILATED_VTANG25K_SMOKETEST_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vtang25k_smoketest_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vtang25k_smoketest_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ tang25k_smoketest_tb__DOT__clk;
    CData/*0:0*/ tang25k_smoketest_tb__DOT__rst_n;
    CData/*0:0*/ tang25k_smoketest_tb__DOT__smoke_ok;
    CData/*0:0*/ tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started;
    CData/*3:0*/ tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
    CData/*0:0*/ tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
    CData/*0:0*/ __Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__rst_n__0;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    SData/*15:0*/ tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
    IData/*31:0*/ tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vtang25k_smoketest_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vtang25k_smoketest_tb___024root(Vtang25k_smoketest_tb__Syms* symsp, const char* namep);
    ~Vtang25k_smoketest_tb___024root();
    VL_UNCOPYABLE(Vtang25k_smoketest_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
