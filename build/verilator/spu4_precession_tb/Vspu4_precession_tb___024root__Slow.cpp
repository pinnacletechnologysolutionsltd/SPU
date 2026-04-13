// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu4_precession_tb.h for the primary calling header

#include "Vspu4_precession_tb__pch.h"

void Vspu4_precession_tb___024root___ctor_var_reset(Vspu4_precession_tb___024root* vlSelf);

Vspu4_precession_tb___024root::Vspu4_precession_tb___024root(Vspu4_precession_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vspu4_precession_tb___024root___ctor_var_reset(this);
}

void Vspu4_precession_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vspu4_precession_tb___024root::~Vspu4_precession_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
