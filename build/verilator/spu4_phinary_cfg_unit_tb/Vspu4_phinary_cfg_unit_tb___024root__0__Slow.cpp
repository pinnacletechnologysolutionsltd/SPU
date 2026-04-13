// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu4_phinary_cfg_unit_tb.h for the primary calling header

#include "Vspu4_phinary_cfg_unit_tb__pch.h"

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_static(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_static\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_phinary_cfg_unit_tb__DOT__clk__0 
        = vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk;
}

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_initial(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_initial\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__eval_initial__TOP_spu4_phinary_cfg_unit_tb__DOT__pass;
    __Vinline__eval_initial__TOP_spu4_phinary_cfg_unit_tb__DOT__pass = 0;
    // Body
    vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk = 0U;
    __Vinline__eval_initial__TOP_spu4_phinary_cfg_unit_tb__DOT__pass = 1U;
    if ((0U != __Vinline__eval_initial__TOP_spu4_phinary_cfg_unit_tb__DOT__pass)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL\n",0);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_phinary_cfg_unit_tb.v", 68, "");
}

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_initial__TOP(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_initial__TOP\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ spu4_phinary_cfg_unit_tb__DOT__pass;
    spu4_phinary_cfg_unit_tb__DOT__pass = 0;
    // Body
    vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk = 0U;
    spu4_phinary_cfg_unit_tb__DOT__pass = 1U;
    if ((0U != spu4_phinary_cfg_unit_tb__DOT__pass)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL\n",0);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_phinary_cfg_unit_tb.v", 68, "");
}

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_final(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_final\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu4_phinary_cfg_unit_tb___024root___eval_phase__stl(Vspu4_phinary_cfg_unit_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_settle(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_settle\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_phinary_cfg_unit_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu4_phinary_cfg_unit_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_triggers_vec__stl(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_phinary_cfg_unit_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_phinary_cfg_unit_tb__DOT__clk__0 
        = vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu4_phinary_cfg_unit_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__stl\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((2U > n));
    return (0U);
}

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___eval_stl(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_stl\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk 
            = (1U & (~ (IData)(vlSelfRef.spu4_phinary_cfg_unit_tb__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vspu4_phinary_cfg_unit_tb___024root___eval_phase__stl(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___eval_phase__stl\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu4_phinary_cfg_unit_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu4_phinary_cfg_unit_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu4_phinary_cfg_unit_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu4_phinary_cfg_unit_tb.clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vspu4_phinary_cfg_unit_tb___024root___ctor_var_reset(Vspu4_phinary_cfg_unit_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_phinary_cfg_unit_tb___024root___ctor_var_reset\n"); );
    Vspu4_phinary_cfg_unit_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->spu4_phinary_cfg_unit_tb__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13397203691250446118ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu4_phinary_cfg_unit_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
