// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu_ve_init_tb.h for the primary calling header

#ifndef VERILATED_VSPU_VE_INIT_TB___024ROOT_H_
#define VERILATED_VSPU_VE_INIT_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu_ve_init_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu_ve_init_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    IData/*31:0*/ spu_ve_init_tb__DOT__fail;

    // INTERNAL VARIABLES
    Vspu_ve_init_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu_ve_init_tb___024root(Vspu_ve_init_tb__Syms* symsp, const char* namep);
    ~Vspu_ve_init_tb___024root();
    VL_UNCOPYABLE(Vspu_ve_init_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
