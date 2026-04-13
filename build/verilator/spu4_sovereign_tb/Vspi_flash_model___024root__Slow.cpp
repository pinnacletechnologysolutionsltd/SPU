// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspi_flash_model.h for the primary calling header

#include "Vspi_flash_model__pch.h"

void Vspi_flash_model___024root___ctor_var_reset(Vspi_flash_model___024root* vlSelf);

Vspi_flash_model___024root::Vspi_flash_model___024root(Vspi_flash_model__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vspi_flash_model___024root___ctor_var_reset(this);
}

void Vspi_flash_model___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vspi_flash_model___024root::~Vspi_flash_model___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
