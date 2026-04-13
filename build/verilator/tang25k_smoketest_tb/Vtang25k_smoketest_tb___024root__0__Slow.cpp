// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtang25k_smoketest_tb.h for the primary calling header

#include "Vtang25k_smoketest_tb__pch.h"

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_static(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_static\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.tang25k_smoketest_tb__DOT__clk = 0U;
    vlSelfRef.tang25k_smoketest_tb__DOT__rst_n = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0 = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__rst_n__0 = 0U;
}

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_static__TOP(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_static__TOP\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.tang25k_smoketest_tb__DOT__clk = 0U;
    vlSelfRef.tang25k_smoketest_tb__DOT__rst_n = 0U;
}

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_initial(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_initial\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSymsp->_vm_contextp__->dumpfile("tang25k_smoke.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v:21: $dumpvar ignored, as Verilated without --trace\n");
    vlSelfRef.tang25k_smoketest_tb__DOT__rst_n = 1U;
    if (vlSelfRef.tang25k_smoketest_tb__DOT__smoke_ok) {
        VL_WRITEF_NX("TEST RESULT: PASS\n",0);
    } else {
        VL_WRITEF_NX("TEST RESULT: FAIL\n",0);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v", 37, "");
}

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_initial__TOP(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_initial__TOP\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSymsp->_vm_contextp__->dumpfile("tang25k_smoke.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v:21: $dumpvar ignored, as Verilated without --trace\n");
    vlSelfRef.tang25k_smoketest_tb__DOT__rst_n = 1U;
    if (vlSelfRef.tang25k_smoketest_tb__DOT__smoke_ok) {
        VL_WRITEF_NX("TEST RESULT: PASS\n",0);
    } else {
        VL_WRITEF_NX("TEST RESULT: FAIL\n",0);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v", 37, "");
}

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_final(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_final\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vtang25k_smoketest_tb___024root___eval_phase__stl(Vtang25k_smoketest_tb___024root* vlSelf);

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_settle(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_settle\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vtang25k_smoketest_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vtang25k_smoketest_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_triggers_vec__stl(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_triggers_vec__stl\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.tang25k_smoketest_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0 
        = vlSelfRef.tang25k_smoketest_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vtang25k_smoketest_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vtang25k_smoketest_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] tang25k_smoketest_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vtang25k_smoketest_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___eval_stl(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_stl\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.tang25k_smoketest_tb__DOT__clk = 
            (1U & (~ (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vtang25k_smoketest_tb___024root___eval_phase__stl(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_phase__stl\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vtang25k_smoketest_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtang25k_smoketest_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vtang25k_smoketest_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vtang25k_smoketest_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vtang25k_smoketest_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vtang25k_smoketest_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] tang25k_smoketest_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge tang25k_smoketest_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge tang25k_smoketest_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___ctor_var_reset(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___ctor_var_reset\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->tang25k_smoketest_tb__DOT__smoke_ok = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7381362475340141197ull);
    vlSelf->tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12326375901207926499ull);
    vlSelf->tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11074756911449553187ull);
    vlSelf->tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 4259016011511443744ull);
    vlSelf->tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 771540593737021333ull);
    vlSelf->tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11497681250175444476ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
