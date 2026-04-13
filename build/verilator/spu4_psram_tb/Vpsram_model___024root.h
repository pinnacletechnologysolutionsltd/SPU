// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vpsram_model.h for the primary calling header

#ifndef VERILATED_VPSRAM_MODEL___024ROOT_H_
#define VERILATED_VPSRAM_MODEL___024ROOT_H_  // guard

#include "verilated.h"


class Vpsram_model__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vpsram_model___024root final {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(sck,0,0);
    VL_IN8(ce_n,0,0);
    VL_INOUT8(dq,3,0);
    CData/*3:0*/ psram_model__DOT__dq_r;
    CData/*0:0*/ psram_model__DOT__dq_oe;
    CData/*7:0*/ psram_model__DOT__cmd;
    CData/*3:0*/ psram_model__DOT__state;
    CData/*7:0*/ psram_model__DOT__bit_cnt;
    CData/*0:0*/ psram_model__DOT__qpi_mode;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__ce_n__0;
    CData/*0:0*/ __Vtrigprevexpr___TOP__sck__0;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    IData/*23:0*/ psram_model__DOT__addr_r;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<CData/*7:0*/, 256> psram_model__DOT__mem;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vpsram_model__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vpsram_model___024root(Vpsram_model__Syms* symsp, const char* namep);
    ~Vpsram_model___024root();
    VL_UNCOPYABLE(Vpsram_model___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
