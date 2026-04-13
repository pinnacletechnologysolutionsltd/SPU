// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vpsram_model.h for the primary calling header

#include "Vpsram_model__pch.h"

VL_ATTR_COLD void Vpsram_model___024root___eval_static(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_static\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__ce_n__0 = vlSelfRef.ce_n;
    vlSelfRef.__Vtrigprevexpr___TOP__sck__0 = vlSelfRef.sck;
}

VL_ATTR_COLD void Vpsram_model___024root___eval_initial(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_initial\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__eval_initial__TOP_psram_model__DOT__i;
    __Vinline__eval_initial__TOP_psram_model__DOT__i = 0;
    // Body
    vlSelfRef.psram_model__DOT__dq_oe = 0U;
    vlSelfRef.psram_model__DOT__qpi_mode = 0U;
    vlSelfRef.psram_model__DOT__state = 0U;
    vlSelfRef.psram_model__DOT__bit_cnt = 0U;
    __Vinline__eval_initial__TOP_psram_model__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000100U, __Vinline__eval_initial__TOP_psram_model__DOT__i)) {
        vlSelfRef.psram_model__DOT__mem[(0x000000ffU 
                                         & __Vinline__eval_initial__TOP_psram_model__DOT__i)] 
            = (0x000000ffU & __Vinline__eval_initial__TOP_psram_model__DOT__i);
        __Vinline__eval_initial__TOP_psram_model__DOT__i 
            = ((IData)(1U) + __Vinline__eval_initial__TOP_psram_model__DOT__i);
    }
}

VL_ATTR_COLD void Vpsram_model___024root___eval_initial__TOP(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_initial__TOP\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ psram_model__DOT__i;
    psram_model__DOT__i = 0;
    // Body
    vlSelfRef.psram_model__DOT__dq_oe = 0U;
    vlSelfRef.psram_model__DOT__qpi_mode = 0U;
    vlSelfRef.psram_model__DOT__state = 0U;
    vlSelfRef.psram_model__DOT__bit_cnt = 0U;
    psram_model__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000100U, psram_model__DOT__i)) {
        vlSelfRef.psram_model__DOT__mem[(0x000000ffU 
                                         & psram_model__DOT__i)] 
            = (0x000000ffU & psram_model__DOT__i);
        psram_model__DOT__i = ((IData)(1U) + psram_model__DOT__i);
    }
}

VL_ATTR_COLD void Vpsram_model___024root___eval_final(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_final\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vpsram_model___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vpsram_model___024root___eval_phase__stl(Vpsram_model___024root* vlSelf);

VL_ATTR_COLD void Vpsram_model___024root___eval_settle(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_settle\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vpsram_model___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_psram_tb.v", 4, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vpsram_model___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vpsram_model___024root___eval_triggers_vec__stl(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_triggers_vec__stl\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool Vpsram_model___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vpsram_model___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vpsram_model___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vpsram_model___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___trigger_anySet__stl\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

VL_ATTR_COLD void Vpsram_model___024root___stl_sequent__TOP__0(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___stl_sequent__TOP__0\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dq = (((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                      ? 0x0fU : 0U) & (((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                                         ? (IData)(vlSelfRef.psram_model__DOT__dq_r)
                                         : 0U) & ((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                                                   ? 0x0fU
                                                   : 0U)));
}

VL_ATTR_COLD void Vpsram_model___024root___eval_stl(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_stl\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.dq = (((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                          ? 0x0fU : 0U) & (((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                                             ? (IData)(vlSelfRef.psram_model__DOT__dq_r)
                                             : 0U) 
                                           & ((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                                               ? 0x0fU
                                               : 0U)));
    }
}

VL_ATTR_COLD bool Vpsram_model___024root___eval_phase__stl(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_phase__stl\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vpsram_model___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vpsram_model___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vpsram_model___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vpsram_model___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vpsram_model___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vpsram_model___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vpsram_model___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge ce_n)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge sck)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vpsram_model___024root___ctor_var_reset(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___ctor_var_reset\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->sck = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16398479871736858182ull);
    vlSelf->ce_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5616457500941497657ull);
    vlSelf->dq = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 5194084716458346210ull);
    for (int __Vi0 = 0; __Vi0 < 256; ++__Vi0) {
        vlSelf->psram_model__DOT__mem[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 12476600347011849952ull);
    }
    vlSelf->psram_model__DOT__dq_r = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 994024125582089057ull);
    vlSelf->psram_model__DOT__dq_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3085742133430655515ull);
    vlSelf->psram_model__DOT__cmd = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 12820897022311110104ull);
    vlSelf->psram_model__DOT__addr_r = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 12345119307454308814ull);
    vlSelf->psram_model__DOT__state = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6920129218407865150ull);
    vlSelf->psram_model__DOT__bit_cnt = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 38478830993253427ull);
    vlSelf->psram_model__DOT__qpi_mode = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4558765540927265326ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__ce_n__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__sck__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
