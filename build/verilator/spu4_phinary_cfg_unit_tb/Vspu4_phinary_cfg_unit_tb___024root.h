// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu4_phinary_cfg_unit_tb.h for the primary calling header

#ifndef VERILATED_VSPU4_PHINARY_CFG_UNIT_TB___024ROOT_H_
#define VERILATED_VSPU4_PHINARY_CFG_UNIT_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu4_phinary_cfg_unit_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu4_phinary_cfg_unit_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ spu4_phinary_cfg_unit_tb__DOT__clk;
    CData/*0:0*/ __Vtrigprevexpr___TOP__spu4_phinary_cfg_unit_tb__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vspu4_phinary_cfg_unit_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu4_phinary_cfg_unit_tb___024root(Vspu4_phinary_cfg_unit_tb__Syms* symsp, const char* namep);
    ~Vspu4_phinary_cfg_unit_tb___024root();
    VL_UNCOPYABLE(Vspu4_phinary_cfg_unit_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
