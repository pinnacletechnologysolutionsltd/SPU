// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu_spread_mul_tb.h for the primary calling header

#ifndef VERILATED_VSPU_SPREAD_MUL_TB___024ROOT_H_
#define VERILATED_VSPU_SPREAD_MUL_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu_spread_mul_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu_spread_mul_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    SData/*15:0*/ spu_spread_mul_tb__DOT__n_a;
    SData/*15:0*/ spu_spread_mul_tb__DOT__n_b;
    SData/*15:0*/ spu_spread_mul_tb__DOT__n_c;
    SData/*15:0*/ spu_spread_mul_tb__DOT__n_d;
    SData/*15:0*/ spu_spread_mul_tb__DOT__l_a;
    SData/*15:0*/ spu_spread_mul_tb__DOT__l_b;
    SData/*15:0*/ spu_spread_mul_tb__DOT__l_c;
    SData/*15:0*/ spu_spread_mul_tb__DOT__l_d;
    IData/*31:0*/ spu_spread_mul_tb__DOT__fail;
    QData/*63:0*/ spu_spread_mul_tb__DOT__spread_denom;
    QData/*63:0*/ spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;

    // INTERNAL VARIABLES
    Vspu_spread_mul_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu_spread_mul_tb___024root(Vspu_spread_mul_tb__Syms* symsp, const char* namep);
    ~Vspu_spread_mul_tb___024root();
    VL_UNCOPYABLE(Vspu_spread_mul_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
