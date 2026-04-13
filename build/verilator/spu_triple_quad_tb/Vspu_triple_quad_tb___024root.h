// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu_triple_quad_tb.h for the primary calling header

#ifndef VERILATED_VSPU_TRIPLE_QUAD_TB___024ROOT_H_
#define VERILATED_VSPU_TRIPLE_QUAD_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu_triple_quad_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu_triple_quad_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ spu_triple_quad_tb__DOT__tangent;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    IData/*31:0*/ spu_triple_quad_tb__DOT__Q1;
    IData/*31:0*/ spu_triple_quad_tb__DOT__Q2;
    IData/*31:0*/ spu_triple_quad_tb__DOT__Q3;
    IData/*31:0*/ spu_triple_quad_tb__DOT__fail;
    QData/*63:0*/ spu_triple_quad_tb__DOT__u_dut__DOT__lhs;
    QData/*63:0*/ spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;

    // INTERNAL VARIABLES
    Vspu_triple_quad_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu_triple_quad_tb___024root(Vspu_triple_quad_tb__Syms* symsp, const char* namep);
    ~Vspu_triple_quad_tb___024root();
    VL_UNCOPYABLE(Vspu_triple_quad_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
