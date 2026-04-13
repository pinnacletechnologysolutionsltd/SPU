// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu_ve_init_tb.h for the primary calling header

#include "Vspu_ve_init_tb__pch.h"

VL_ATTR_COLD void Vspu_ve_init_tb___024root___eval_static(Vspu_ve_init_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_ve_init_tb___024root___eval_static\n"); );
    Vspu_ve_init_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu_ve_init_tb__DOT__fail = 0U;
}

VL_ATTR_COLD void Vspu_ve_init_tb___024root___eval_static__TOP(Vspu_ve_init_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_ve_init_tb___024root___eval_static__TOP\n"); );
    Vspu_ve_init_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu_ve_init_tb__DOT__fail = 0U;
}

VL_ATTR_COLD void Vspu_ve_init_tb___024root___eval_initial(Vspu_ve_init_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_ve_init_tb___024root___eval_initial\n"); );
    Vspu_ve_init_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    VL_WRITEF_NX("T1 PASS: ve_valid=0 before boot\nT2 PASS: ve_valid=1 after boot_done\nT3 PASS: axis 0 = +unity\nT3 PASS: axis 1 = +unity\nT3 PASS: axis 2 = +unity\nT3 PASS: axis 3 = +unity\nT3 PASS: axis 4 = +unity\nT3 PASS: axis 5 = +unity\nT4 PASS: axis 6 = -unity\nT4 PASS: axis 7 = -unity\nT4 PASS: axis 8 = -unity\nT4 PASS: axis 9 = -unity\nT4 PASS: axis 10 = -unity\nT4 PASS: axis 11 = -unity\nT5 PASS: axis 12 centre = +unity\nT6 PASS: SIGMA outer-12 rational = 0 (VE equilibrium)\n",0);
    if ((0U == vlSelfRef.spu_ve_init_tb__DOT__fail)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL (%0d failures)\n",1, '~',32,vlSelfRef.spu_ve_init_tb__DOT__fail);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_ve_init_tb.v", 99, "");
}

VL_ATTR_COLD void Vspu_ve_init_tb___024root___eval_initial__TOP(Vspu_ve_init_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_ve_init_tb___024root___eval_initial__TOP\n"); );
    Vspu_ve_init_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    VL_WRITEF_NX("T1 PASS: ve_valid=0 before boot\nT2 PASS: ve_valid=1 after boot_done\nT3 PASS: axis 0 = +unity\nT3 PASS: axis 1 = +unity\nT3 PASS: axis 2 = +unity\nT3 PASS: axis 3 = +unity\nT3 PASS: axis 4 = +unity\nT3 PASS: axis 5 = +unity\nT4 PASS: axis 6 = -unity\nT4 PASS: axis 7 = -unity\nT4 PASS: axis 8 = -unity\nT4 PASS: axis 9 = -unity\nT4 PASS: axis 10 = -unity\nT4 PASS: axis 11 = -unity\nT5 PASS: axis 12 centre = +unity\nT6 PASS: SIGMA outer-12 rational = 0 (VE equilibrium)\n",0);
    if ((0U == vlSelfRef.spu_ve_init_tb__DOT__fail)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL (%0d failures)\n",1, '~',32,vlSelfRef.spu_ve_init_tb__DOT__fail);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_ve_init_tb.v", 99, "");
}

VL_ATTR_COLD void Vspu_ve_init_tb___024root___eval_final(Vspu_ve_init_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_ve_init_tb___024root___eval_final\n"); );
    Vspu_ve_init_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vspu_ve_init_tb___024root___eval_settle(Vspu_ve_init_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_ve_init_tb___024root___eval_settle\n"); );
    Vspu_ve_init_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
