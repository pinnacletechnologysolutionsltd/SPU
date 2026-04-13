// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vlaminar_node_tb.h for the primary calling header

#ifndef VERILATED_VLAMINAR_NODE_TB___024ROOT_H_
#define VERILATED_VLAMINAR_NODE_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vlaminar_node_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vlaminar_node_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ laminar_node_tb__DOT__clk;
    CData/*0:0*/ laminar_node_tb__DOT__rst_n;
    CData/*0:0*/ laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift;
    CData/*0:0*/ __Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__laminar_node_tb__DOT__rst_n__0;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    IData/*31:0*/ laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP;
    IData/*31:0*/ laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ;
    IData/*31:0*/ __VactIterCount;
    QData/*63:0*/ laminar_node_tb__DOT__surd_in;
    QData/*63:0*/ laminar_node_tb__DOT__surd_out;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vlaminar_node_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vlaminar_node_tb___024root(Vlaminar_node_tb__Syms* symsp, const char* namep);
    ~Vlaminar_node_tb___024root();
    VL_UNCOPYABLE(Vlaminar_node_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
