// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vlaminar_node_tb.h for the primary calling header

#include "Vlaminar_node_tb__pch.h"

void Vlaminar_node_tb___024root___ctor_var_reset(Vlaminar_node_tb___024root* vlSelf);

Vlaminar_node_tb___024root::Vlaminar_node_tb___024root(Vlaminar_node_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vlaminar_node_tb___024root___ctor_var_reset(this);
}

void Vlaminar_node_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vlaminar_node_tb___024root::~Vlaminar_node_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
