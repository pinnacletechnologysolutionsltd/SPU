// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu_ve_init_tb.h for the primary calling header

#include "Vspu_ve_init_tb__pch.h"


Vspu_ve_init_tb___024root::Vspu_ve_init_tb___024root(Vspu_ve_init_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
}

void Vspu_ve_init_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vspu_ve_init_tb___024root::~Vspu_ve_init_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
