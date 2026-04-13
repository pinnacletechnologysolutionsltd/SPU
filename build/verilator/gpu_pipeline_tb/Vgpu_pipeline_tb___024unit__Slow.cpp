// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vgpu_pipeline_tb.h for the primary calling header

#include "Vgpu_pipeline_tb__pch.h"

void Vgpu_pipeline_tb___024unit___ctor_var_reset(Vgpu_pipeline_tb___024unit* vlSelf);

Vgpu_pipeline_tb___024unit::Vgpu_pipeline_tb___024unit() = default;
Vgpu_pipeline_tb___024unit::~Vgpu_pipeline_tb___024unit() = default;

void Vgpu_pipeline_tb___024unit::ctor(Vgpu_pipeline_tb__Syms* symsp, const char* namep) {
    vlSymsp = symsp;
    vlNamep = strdup(Verilated::catName(vlSymsp->name(), namep));
    // Reset structure values
    Vgpu_pipeline_tb___024unit___ctor_var_reset(this);
}

void Vgpu_pipeline_tb___024unit::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

void Vgpu_pipeline_tb___024unit::dtor() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
