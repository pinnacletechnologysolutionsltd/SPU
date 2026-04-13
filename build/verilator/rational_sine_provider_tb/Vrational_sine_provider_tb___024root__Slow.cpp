// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrational_sine_provider_tb.h for the primary calling header

#include "Vrational_sine_provider_tb__pch.h"

void Vrational_sine_provider_tb___024root___ctor_var_reset(Vrational_sine_provider_tb___024root* vlSelf);

Vrational_sine_provider_tb___024root::Vrational_sine_provider_tb___024root(Vrational_sine_provider_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vrational_sine_provider_tb___024root___ctor_var_reset(this);
}

void Vrational_sine_provider_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vrational_sine_provider_tb___024root::~Vrational_sine_provider_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
