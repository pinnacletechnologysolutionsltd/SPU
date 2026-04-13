// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspi_flash_model.h for the primary calling header

#include "Vspi_flash_model__pch.h"

VL_ATTR_COLD void Vspi_flash_model___024root___eval_static(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_static\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__sck__0 = vlSelfRef.sck;
}

VL_ATTR_COLD void Vspi_flash_model___024root___eval_initial(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_initial\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.miso = 0U;
    vlSelfRef.spi_flash_model__DOT__state = 0U;
    vlSelfRef.spi_flash_model__DOT__bit_cnt = 0U;
    vlSelfRef.spi_flash_model__DOT__data[16U] = 0x20U;
    vlSelfRef.spi_flash_model__DOT__data[17U] = 0U;
    vlSelfRef.spi_flash_model__DOT__data[18U] = 0x30U;
    vlSelfRef.spi_flash_model__DOT__data[19U] = 0U;
}

VL_ATTR_COLD void Vspi_flash_model___024root___eval_initial__TOP(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_initial__TOP\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.miso = 0U;
    vlSelfRef.spi_flash_model__DOT__state = 0U;
    vlSelfRef.spi_flash_model__DOT__bit_cnt = 0U;
    vlSelfRef.spi_flash_model__DOT__data[16U] = 0x20U;
    vlSelfRef.spi_flash_model__DOT__data[17U] = 0U;
    vlSelfRef.spi_flash_model__DOT__data[18U] = 0x30U;
    vlSelfRef.spi_flash_model__DOT__data[19U] = 0U;
}

VL_ATTR_COLD void Vspi_flash_model___024root___eval_final(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_final\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vspi_flash_model___024root___eval_settle(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_settle\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

bool Vspi_flash_model___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspi_flash_model___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vspi_flash_model___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge sck)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vspi_flash_model___024root___ctor_var_reset(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___ctor_var_reset\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->sck = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16398479871736858182ull);
    vlSelf->cs_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7862198864114561069ull);
    vlSelf->mosi = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11760532154298914343ull);
    vlSelf->miso = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4240847957141628474ull);
    for (int __Vi0 = 0; __Vi0 < 256; ++__Vi0) {
        vlSelf->spi_flash_model__DOT__data[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 1502596607488760644ull);
    }
    vlSelf->spi_flash_model__DOT__cmd = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 10913196109766677198ull);
    vlSelf->spi_flash_model__DOT__addr = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 9403424637799773691ull);
    vlSelf->spi_flash_model__DOT__state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 2887631789139595413ull);
    vlSelf->spi_flash_model__DOT__bit_cnt = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 8878328080527175565ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__sck__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
