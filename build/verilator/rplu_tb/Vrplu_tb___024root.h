// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vrplu_tb.h for the primary calling header

#ifndef VERILATED_VRPLU_TB___024ROOT_H_
#define VERILATED_VRPLU_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vrplu_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vrplu_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ rplu_tb__DOT__clk;
    CData/*0:0*/ rplu_tb__DOT__rst_n;
    CData/*0:0*/ rplu_tb__DOT__start;
    CData/*0:0*/ rplu_tb__DOT__material_id;
    CData/*0:0*/ rplu_tb__DOT__dissoc;
    CData/*0:0*/ __Vtrigprevexpr___TOP__rplu_tb__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__rplu_tb__DOT__rst_n__0;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    SData/*9:0*/ rplu_tb__DOT__addr;
    IData/*31:0*/ rplu_tb__DOT__p_out;
    IData/*31:0*/ rplu_tb__DOT__q_out;
    IData/*31:0*/ rplu_tb__DOT__errors;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<QData/*63:0*/, 1024> rplu_tb__DOT__exp_carbon;
    VlUnpacked<QData/*63:0*/, 1024> rplu_tb__DOT__exp_iron;
    VlUnpacked<CData/*0:0*/, 1024> rplu_tb__DOT__exp_diss_c;
    VlUnpacked<CData/*0:0*/, 1024> rplu_tb__DOT__exp_diss_i;
    VlUnpacked<QData/*63:0*/, 1024> rplu_tb__DOT__uut__DOT__rom_carbon;
    VlUnpacked<QData/*63:0*/, 1024> rplu_tb__DOT__uut__DOT__rom_iron;
    VlUnpacked<CData/*0:0*/, 1024> rplu_tb__DOT__uut__DOT__diss_carbon;
    VlUnpacked<CData/*0:0*/, 1024> rplu_tb__DOT__uut__DOT__diss_iron;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vrplu_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vrplu_tb___024root(Vrplu_tb__Syms* symsp, const char* namep);
    ~Vrplu_tb___024root();
    VL_UNCOPYABLE(Vrplu_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
