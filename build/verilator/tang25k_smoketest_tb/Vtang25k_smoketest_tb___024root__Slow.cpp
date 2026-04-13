// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtang25k_smoketest_tb.h for the primary calling header

#include "Vtang25k_smoketest_tb__pch.h"

void Vtang25k_smoketest_tb___024root___ctor_var_reset(Vtang25k_smoketest_tb___024root* vlSelf);

Vtang25k_smoketest_tb___024root::Vtang25k_smoketest_tb___024root(Vtang25k_smoketest_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vtang25k_smoketest_tb___024root___ctor_var_reset(this);
}

void Vtang25k_smoketest_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vtang25k_smoketest_tb___024root::~Vtang25k_smoketest_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
