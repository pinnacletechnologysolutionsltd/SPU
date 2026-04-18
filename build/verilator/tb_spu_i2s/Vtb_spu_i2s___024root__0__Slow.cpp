// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtb_spu_i2s.h for the primary calling header

#include "Vtb_spu_i2s__pch.h"

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_static(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_static\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_i2s__DOT__clk__0 
        = vlSelfRef.tb_spu_i2s__DOT__clk;
}

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_initial(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_initial\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.tb_spu_i2s__DOT__clk = 0U;
    VL_WRITEF_NX("PASS: I2S timing verified\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_i2s.v", 36, "");
    vlSymsp->_vm_contextp__->dumpfile("i2s_trace.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_i2s.v:41: $dumpvar ignored, as Verilated without --trace\n");
}

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_initial__TOP(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_initial__TOP\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.tb_spu_i2s__DOT__clk = 0U;
    VL_WRITEF_NX("PASS: I2S timing verified\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_i2s.v", 36, "");
    vlSymsp->_vm_contextp__->dumpfile("i2s_trace.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_i2s.v:41: $dumpvar ignored, as Verilated without --trace\n");
}

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_final(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_final\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_spu_i2s___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vtb_spu_i2s___024root___eval_phase__stl(Vtb_spu_i2s___024root* vlSelf);

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_settle(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_settle\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vtb_spu_i2s___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_i2s.v", 4, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vtb_spu_i2s___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_triggers_vec__stl(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_triggers_vec__stl\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.tb_spu_i2s__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_i2s__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_i2s__DOT__clk__0 
        = vlSelfRef.tb_spu_i2s__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vtb_spu_i2s___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_spu_i2s___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vtb_spu_i2s___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] tb_spu_i2s.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vtb_spu_i2s___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vtb_spu_i2s___024root___eval_stl(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_stl\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.tb_spu_i2s__DOT__clk = (1U & (~ (IData)(vlSelfRef.tb_spu_i2s__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vtb_spu_i2s___024root___eval_phase__stl(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___eval_phase__stl\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vtb_spu_i2s___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtb_spu_i2s___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vtb_spu_i2s___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vtb_spu_i2s___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vtb_spu_i2s___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_spu_i2s___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vtb_spu_i2s___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] tb_spu_i2s.clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vtb_spu_i2s___024root___ctor_var_reset(Vtb_spu_i2s___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_i2s___024root___ctor_var_reset\n"); );
    Vtb_spu_i2s__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->tb_spu_i2s__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6849120681022647523ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__tb_spu_i2s__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
