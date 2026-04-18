// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtb_spu_i2s.h for the primary calling header

#include "Vtb_spu_i2s__pch.h"

void Vtb_spu_i2s___024root___ctor_var_reset(Vtb_spu_i2s___024root* vlSelf);

Vtb_spu_i2s___024root::Vtb_spu_i2s___024root(Vtb_spu_i2s__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vtb_spu_i2s___024root___ctor_var_reset(this);
}

void Vtb_spu_i2s___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vtb_spu_i2s___024root::~Vtb_spu_i2s___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
