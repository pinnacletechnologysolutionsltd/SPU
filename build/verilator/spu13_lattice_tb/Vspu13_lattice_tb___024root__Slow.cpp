// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu13_lattice_tb.h for the primary calling header

#include "Vspu13_lattice_tb__pch.h"

void Vspu13_lattice_tb___024root___ctor_var_reset(Vspu13_lattice_tb___024root* vlSelf);

Vspu13_lattice_tb___024root::Vspu13_lattice_tb___024root(Vspu13_lattice_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vspu13_lattice_tb___024root___ctor_var_reset(this);
}

void Vspu13_lattice_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vspu13_lattice_tb___024root::~Vspu13_lattice_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
