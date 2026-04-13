// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vrational_surd5_norm_tb.h for the primary calling header

#ifndef VERILATED_VRATIONAL_SURD5_NORM_TB___024ROOT_H_
#define VERILATED_VRATIONAL_SURD5_NORM_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vrational_surd5_norm_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vrational_surd5_norm_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ rational_surd5_norm_tb__DOT__uut__DOT__need_shift;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    IData/*31:0*/ rational_surd5_norm_tb__DOT__uut__DOT__sP;
    IData/*31:0*/ rational_surd5_norm_tb__DOT__uut__DOT__sQ;
    QData/*63:0*/ rational_surd5_norm_tb__DOT__in_val;
    QData/*32:0*/ rational_surd5_norm_tb__DOT__uut__DOT__sP_ext;
    QData/*32:0*/ rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;

    // INTERNAL VARIABLES
    Vrational_surd5_norm_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vrational_surd5_norm_tb___024root(Vrational_surd5_norm_tb__Syms* symsp, const char* namep);
    ~Vrational_surd5_norm_tb___024root();
    VL_UNCOPYABLE(Vrational_surd5_norm_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
