// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu_spi_slave_tb.h for the primary calling header

#include "Vspu_spi_slave_tb__pch.h"

void Vspu_spi_slave_tb___024root___ctor_var_reset(Vspu_spi_slave_tb___024root* vlSelf);

Vspu_spi_slave_tb___024root::Vspu_spi_slave_tb___024root(Vspu_spi_slave_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vspu_spi_slave_tb___024root___ctor_var_reset(this);
}

void Vspu_spi_slave_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vspu_spi_slave_tb___024root::~Vspu_spi_slave_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
