// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vrational_sine_tb.h for the primary calling header

#ifndef VERILATED_VRATIONAL_SINE_TB___024ROOT_H_
#define VERILATED_VRATIONAL_SINE_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vrational_sine_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vrational_sine_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    SData/*11:0*/ rational_sine_tb__DOT__addr;
    IData/*31:0*/ rational_sine_tb__DOT__dout;
    VlUnpacked<IData/*31:0*/, 4096> rational_sine_tb__DOT__UUT__DOT__rom;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;

    // INTERNAL VARIABLES
    Vrational_sine_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vrational_sine_tb___024root(Vrational_sine_tb__Syms* symsp, const char* namep);
    ~Vrational_sine_tb___024root();
    VL_UNCOPYABLE(Vrational_sine_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
