// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vgpu_pipeline_tb.h for the primary calling header

#include "Vgpu_pipeline_tb__pch.h"

VL_ATTR_COLD void Vgpu_pipeline_tb___024unit___ctor_var_reset(Vgpu_pipeline_tb___024unit* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+      Vgpu_pipeline_tb___024unit___ctor_var_reset\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelf->__VmonitorNum = 0;
    vlSelf->__VmonitorOff = 0;
}
