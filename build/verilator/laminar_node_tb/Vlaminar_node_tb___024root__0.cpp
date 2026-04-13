// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vlaminar_node_tb.h for the primary calling header

#include "Vlaminar_node_tb__pch.h"

void Vlaminar_node_tb___024root___eval_triggers_vec__act(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_triggers_vec__act\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((~ (IData)(vlSelfRef.laminar_node_tb__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__rst_n__0)) 
                                                      << 2U) 
                                                     | ((((IData)(vlSelfRef.laminar_node_tb__DOT__clk) 
                                                          & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0))) 
                                                         << 1U) 
                                                        | ((IData)(vlSelfRef.laminar_node_tb__DOT__clk) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0 
        = vlSelfRef.laminar_node_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__rst_n__0 
        = vlSelfRef.laminar_node_tb__DOT__rst_n;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VactDidInit)))))) {
        vlSelfRef.__VactDidInit = 1U;
        vlSelfRef.__VactTriggered[0U] = (1ULL | vlSelfRef.__VactTriggered[0U]);
    }
}

bool Vlaminar_node_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___trigger_anySet__act\n"); );
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

void Vlaminar_node_tb___024root___act_sequent__TOP__0(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___act_sequent__TOP__0\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.laminar_node_tb__DOT__clk = (1U & (~ (IData)(vlSelfRef.laminar_node_tb__DOT__clk)));
}

void Vlaminar_node_tb___024root___eval_act(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_act\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VactTriggered[0U])) {
        vlSelfRef.laminar_node_tb__DOT__clk = (1U & 
                                               (~ (IData)(vlSelfRef.laminar_node_tb__DOT__clk)));
    }
}

void Vlaminar_node_tb___024root___nba_sequent__TOP__0(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___nba_sequent__TOP__0\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.laminar_node_tb__DOT__surd_out = ((IData)(vlSelfRef.laminar_node_tb__DOT__rst_n)
                                                 ? 
                                                (((QData)((IData)(
                                                                  ((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift)
                                                                    ? 
                                                                   VL_SHIFTRS_III(32,32,32, vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP, 1U)
                                                                    : vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP))) 
                                                  << 0x00000020U) 
                                                 | (QData)((IData)(
                                                                   ((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift)
                                                                     ? 
                                                                    VL_SHIFTRS_III(32,32,32, vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ, 1U)
                                                                     : vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ))))
                                                 : 0ULL);
}

void Vlaminar_node_tb___024root___eval_nba(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_nba\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((6ULL & vlSelfRef.__VnbaTriggered[0U])) {
        vlSelfRef.laminar_node_tb__DOT__surd_out = 
            ((IData)(vlSelfRef.laminar_node_tb__DOT__rst_n)
              ? (((QData)((IData)(((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift)
                                    ? VL_SHIFTRS_III(32,32,32, vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP, 1U)
                                    : vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP))) 
                  << 0x00000020U) | (QData)((IData)(
                                                    ((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift)
                                                      ? 
                                                     VL_SHIFTRS_III(32,32,32, vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ, 1U)
                                                      : vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ))))
              : 0ULL);
    }
}

void Vlaminar_node_tb___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vlaminar_node_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vlaminar_node_tb___024root___eval_phase__act(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_phase__act\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VactExecute;
    // Body
    Vlaminar_node_tb___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vlaminar_node_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vlaminar_node_tb___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    __VactExecute = Vlaminar_node_tb___024root___trigger_anySet__act(vlSelfRef.__VactTriggered);
    if (__VactExecute) {
        Vlaminar_node_tb___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vlaminar_node_tb___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vlaminar_node_tb___024root___eval_phase__nba(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_phase__nba\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vlaminar_node_tb___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vlaminar_node_tb___024root___eval_nba(vlSelf);
        Vlaminar_node_tb___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vlaminar_node_tb___024root___eval(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vlaminar_node_tb___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/laminar_node_tb.v", 3, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vlaminar_node_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/laminar_node_tb.v", 3, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vlaminar_node_tb___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vlaminar_node_tb___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vlaminar_node_tb___024root___eval_debug_assertions(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_debug_assertions\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
