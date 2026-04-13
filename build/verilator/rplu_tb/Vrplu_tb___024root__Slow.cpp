// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrplu_tb.h for the primary calling header

#include "Vrplu_tb__pch.h"

void Vrplu_tb___024root___ctor_var_reset(Vrplu_tb___024root* vlSelf);

Vrplu_tb___024root::Vrplu_tb___024root(Vrplu_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vrplu_tb___024root___ctor_var_reset(this);
}

void Vrplu_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vrplu_tb___024root::~Vrplu_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
