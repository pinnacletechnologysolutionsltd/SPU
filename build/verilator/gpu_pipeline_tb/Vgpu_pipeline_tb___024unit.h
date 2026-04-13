// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vgpu_pipeline_tb.h for the primary calling header

#ifndef VERILATED_VGPU_PIPELINE_TB___024UNIT_H_
#define VERILATED_VGPU_PIPELINE_TB___024UNIT_H_  // guard

#include "verilated.h"


class Vgpu_pipeline_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vgpu_pipeline_tb___024unit final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ __VmonitorOff;
    QData/*63:0*/ __VmonitorNum;

    // INTERNAL VARIABLES
    Vgpu_pipeline_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vgpu_pipeline_tb___024unit();
    ~Vgpu_pipeline_tb___024unit();
    void ctor(Vgpu_pipeline_tb__Syms* symsp, const char* namep);
    void dtor();
    VL_UNCOPYABLE(Vgpu_pipeline_tb___024unit);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
