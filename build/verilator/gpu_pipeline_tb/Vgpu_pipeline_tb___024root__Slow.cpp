// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vgpu_pipeline_tb.h for the primary calling header

#include "Vgpu_pipeline_tb__pch.h"

void Vgpu_pipeline_tb___024root___ctor_var_reset(Vgpu_pipeline_tb___024root* vlSelf);

Vgpu_pipeline_tb___024root::Vgpu_pipeline_tb___024root(Vgpu_pipeline_tb__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vgpu_pipeline_tb___024root___ctor_var_reset(this);
}

void Vgpu_pipeline_tb___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vgpu_pipeline_tb___024root::~Vgpu_pipeline_tb___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
