// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu_triple_spread_tb.h for the primary calling header

#ifndef VERILATED_VSPU_TRIPLE_SPREAD_TB___024ROOT_H_
#define VERILATED_VSPU_TRIPLE_SPREAD_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu_triple_spread_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu_triple_spread_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ spu_triple_spread_tb__DOT__valid;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    SData/*15:0*/ spu_triple_spread_tb__DOT__s1_n;
    SData/*15:0*/ spu_triple_spread_tb__DOT__s2_n;
    SData/*15:0*/ spu_triple_spread_tb__DOT__s3_n;
    SData/*15:0*/ spu_triple_spread_tb__DOT__d;
    IData/*31:0*/ spu_triple_spread_tb__DOT__fail;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;

    // INTERNAL VARIABLES
    Vspu_triple_spread_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu_triple_spread_tb___024root(Vspu_triple_spread_tb__Syms* symsp, const char* namep);
    ~Vspu_triple_spread_tb___024root();
    VL_UNCOPYABLE(Vspu_triple_spread_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
