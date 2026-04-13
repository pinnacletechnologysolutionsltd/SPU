// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vrational_surd5_scale_manager_tb.h for the primary calling header

#ifndef VERILATED_VRATIONAL_SURD5_SCALE_MANAGER_TB___024ROOT_H_
#define VERILATED_VRATIONAL_SURD5_SCALE_MANAGER_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vrational_surd5_scale_manager_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vrational_surd5_scale_manager_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ rational_surd5_scale_manager_tb__DOT__clk;
    CData/*0:0*/ rational_surd5_scale_manager_tb__DOT__rst_n;
    CData/*0:0*/ rational_surd5_scale_manager_tb__DOT__write_en;
    CData/*3:0*/ rational_surd5_scale_manager_tb__DOT__write_idx;
    CData/*3:0*/ rational_surd5_scale_manager_tb__DOT__write_shift;
    CData/*0:0*/ rational_surd5_scale_manager_tb__DOT__write_overflow;
    CData/*0:0*/ rational_surd5_scale_manager_tb__DOT__uut__DOT____Vlvbound_h95ca7be9__0;
    CData/*3:0*/ rational_surd5_scale_manager_tb__DOT__uut__DOT____Vlvbound_h161fecb4__0;
    CData/*0:0*/ __Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__rst_n__0;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    SData/*12:0*/ rational_surd5_scale_manager_tb__DOT__overflow_table;
    IData/*31:0*/ __VactIterCount;
    QData/*51:0*/ rational_surd5_scale_manager_tb__DOT__scale_table;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vrational_surd5_scale_manager_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vrational_surd5_scale_manager_tb___024root(Vrational_surd5_scale_manager_tb__Syms* symsp, const char* namep);
    ~Vrational_surd5_scale_manager_tb___024root();
    VL_UNCOPYABLE(Vrational_surd5_scale_manager_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
