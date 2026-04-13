// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrational_surd5_scale_manager_tb.h for the primary calling header

#include "Vrational_surd5_scale_manager_tb__pch.h"

void Vrational_surd5_scale_manager_tb___024root___ctor_var_reset(Vrational_surd5_scale_manager_tb___024root* vlSelf);

Vrational_surd5_scale_manager_tb___024root::Vrational_surd5_scale_manager_tb___024root(Vrational_surd5_scale_manager_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vrational_surd5_scale_manager_tb___024root___ctor_var_reset(this);
}

void Vrational_surd5_scale_manager_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vrational_surd5_scale_manager_tb___024root::~Vrational_surd5_scale_manager_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
