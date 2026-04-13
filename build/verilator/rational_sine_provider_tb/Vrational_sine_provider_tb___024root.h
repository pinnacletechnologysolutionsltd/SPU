// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vrational_sine_provider_tb.h for the primary calling header

#ifndef VERILATED_VRATIONAL_SINE_PROVIDER_TB___024ROOT_H_
#define VERILATED_VRATIONAL_SINE_PROVIDER_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vrational_sine_provider_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vrational_sine_provider_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    SData/*11:0*/ rational_sine_provider_tb__DOT__addr;
    IData/*31:0*/ rational_sine_provider_tb__DOT__p32_out;
    IData/*31:0*/ rational_sine_provider_tb__DOT__q32_out;
    IData/*31:0*/ rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16;
    VlUnpacked<IData/*31:0*/, 4096> rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__rom16__DOT__rom;
    VlUnpacked<QData/*63:0*/, 4096> rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    double rational_sine_provider_tb__DOT____VlemCall_3__abs_r;
    double rational_sine_provider_tb__DOT____VlemCall_2__abs_r;
    double rational_sine_provider_tb__DOT____VlemCall_1__abs_r;
    double rational_sine_provider_tb__DOT____VlemCall_0__abs_r;
    double rational_sine_provider_tb__DOT__orig;
    double rational_sine_provider_tb__DOT__recon16;
    double rational_sine_provider_tb__DOT__recon32;
    double rational_sine_provider_tb__DOT__err16;
    double rational_sine_provider_tb__DOT__err32;
    double rational_sine_provider_tb__DOT__compute_s3__Vstatic__s;

    // INTERNAL VARIABLES
    Vrational_sine_provider_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vrational_sine_provider_tb___024root(Vrational_sine_provider_tb__Syms* symsp, const char* namep);
    ~Vrational_sine_provider_tb___024root();
    VL_UNCOPYABLE(Vrational_sine_provider_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
