// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vpsram_model.h for the primary calling header

#include "Vpsram_model__pch.h"

void Vpsram_model___024root___ctor_var_reset(Vpsram_model___024root* vlSelf);

Vpsram_model___024root::Vpsram_model___024root(Vpsram_model__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vpsram_model___024root___ctor_var_reset(this);
}

void Vpsram_model___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vpsram_model___024root::~Vpsram_model___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
