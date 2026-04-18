// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vtb_spu_i2s.h for the primary calling header

#ifndef VERILATED_VTB_SPU_I2S___024ROOT_H_
#define VERILATED_VTB_SPU_I2S___024ROOT_H_  // guard

#include "verilated.h"


class Vtb_spu_i2s__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vtb_spu_i2s___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ tb_spu_i2s__DOT__clk;
    CData/*0:0*/ __Vtrigprevexpr___TOP__tb_spu_i2s__DOT__clk__0;
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
    Vtb_spu_i2s__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vtb_spu_i2s___024root(Vtb_spu_i2s__Syms* symsp, const char* namep);
    ~Vtb_spu_i2s___024root();
    VL_UNCOPYABLE(Vtb_spu_i2s___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
