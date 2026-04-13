// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu13_lattice_tb.h for the primary calling header

#include "Vspu13_lattice_tb__pch.h"

extern const VlWide<26>/*831:0*/ Vspu13_lattice_tb__ConstPool__CONST_h571eb658_0;

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_static(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_static\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu13_lattice_tb__DOT__clk = 0U;
    vlSelfRef.spu13_lattice_tb__DOT__rst_n = 0U;
    VL_ASSIGN_W(832, vlSelfRef.spu13_lattice_tb__DOT__manifold_in, Vspu13_lattice_tb__ConstPool__CONST_h571eb658_0);
    vlSelfRef.__Vtrigprevexpr___TOP__spu13_lattice_tb__DOT__clk__0 = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__spu13_lattice_tb__DOT__rst_n__0 = 0U;
}

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_static__TOP(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_static__TOP\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu13_lattice_tb__DOT__clk = 0U;
    vlSelfRef.spu13_lattice_tb__DOT__rst_n = 0U;
    VL_ASSIGN_W(832, vlSelfRef.spu13_lattice_tb__DOT__manifold_in, Vspu13_lattice_tb__ConstPool__CONST_h571eb658_0);
}

extern const VlWide<26>/*831:0*/ Vspu13_lattice_tb__ConstPool__CONST_h349cd1ba_0;

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_initial(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_initial\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu13_lattice_tb__DOT__rst_n = 1U;
    VL_ASSIGN_W(832, vlSelfRef.spu13_lattice_tb__DOT__manifold_in, Vspu13_lattice_tb__ConstPool__CONST_h349cd1ba_0);
    VL_WRITEF_NX("manifold_out[0] = %h\nmanifold_out[1] = %h\n",2
                 , '#',64,(((QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[1U])) 
                            << 0x00000020U) | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[0U])))
                 , '#',64,(((QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[3U])) 
                            << 0x00000020U) | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[2U]))));
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu13_lattice_tb.v", 31, "");
}

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_initial__TOP(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_initial__TOP\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu13_lattice_tb__DOT__rst_n = 1U;
    VL_ASSIGN_W(832, vlSelfRef.spu13_lattice_tb__DOT__manifold_in, Vspu13_lattice_tb__ConstPool__CONST_h349cd1ba_0);
    VL_WRITEF_NX("manifold_out[0] = %h\nmanifold_out[1] = %h\n",2
                 , '#',64,(((QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[1U])) 
                            << 0x00000020U) | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[0U])))
                 , '#',64,(((QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[3U])) 
                            << 0x00000020U) | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__manifold_out[2U]))));
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu13_lattice_tb.v", 31, "");
}

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_final(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_final\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu13_lattice_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu13_lattice_tb___024root___eval_phase__stl(Vspu13_lattice_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_settle(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_settle\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu13_lattice_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu13_lattice_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu13_lattice_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_triggers_vec__stl(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.spu13_lattice_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu13_lattice_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu13_lattice_tb__DOT__clk__0 
        = vlSelfRef.spu13_lattice_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vspu13_lattice_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu13_lattice_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu13_lattice_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu13_lattice_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu13_lattice_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vspu13_lattice_tb___024root___stl_sequent__TOP__1(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___stl_sequent__TOP__1\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ_ext = 0;
    QData/*33:0*/ spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ_ext = 0;
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp);
    VlWide<3>/*66:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp;
    VL_ZERO_W(67, spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp);
    VlWide<3>/*65:0*/ spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp;
    VL_ZERO_W(66, spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp);
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__q_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__p_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__p_tmp = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__q_tmp;
    spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__q_tmp = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP = 0;
    IData/*31:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP_ext = 0;
    QData/*32:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ_ext;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ_ext = 0;
    CData/*0:0*/ spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift;
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_0;
    __VdfgRegularize_he50b618e_0_0 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_1;
    __VdfgRegularize_he50b618e_0_1 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_6;
    __VdfgRegularize_he50b618e_0_6 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_7;
    __VdfgRegularize_he50b618e_0_7 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_10;
    __VdfgRegularize_he50b618e_0_10 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_11;
    __VdfgRegularize_he50b618e_0_11 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_14;
    __VdfgRegularize_he50b618e_0_14 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_15;
    __VdfgRegularize_he50b618e_0_15 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_18;
    __VdfgRegularize_he50b618e_0_18 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_19;
    __VdfgRegularize_he50b618e_0_19 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_22;
    __VdfgRegularize_he50b618e_0_22 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_23;
    __VdfgRegularize_he50b618e_0_23 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_26;
    __VdfgRegularize_he50b618e_0_26 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_27;
    __VdfgRegularize_he50b618e_0_27 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_30;
    __VdfgRegularize_he50b618e_0_30 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_31;
    __VdfgRegularize_he50b618e_0_31 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_34;
    __VdfgRegularize_he50b618e_0_34 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_35;
    __VdfgRegularize_he50b618e_0_35 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_38;
    __VdfgRegularize_he50b618e_0_38 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_39;
    __VdfgRegularize_he50b618e_0_39 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_42;
    __VdfgRegularize_he50b618e_0_42 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_43;
    __VdfgRegularize_he50b618e_0_43 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_46;
    __VdfgRegularize_he50b618e_0_46 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_47;
    __VdfgRegularize_he50b618e_0_47 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_50;
    __VdfgRegularize_he50b618e_0_50 = 0;
    IData/*31:0*/ __VdfgRegularize_he50b618e_0_51;
    __VdfgRegularize_he50b618e_0_51 = 0;
    VlWide<3>/*95:0*/ __Vtemp_2;
    VlWide<3>/*95:0*/ __Vtemp_3;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_7;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_11;
    VlWide<3>/*95:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_15;
    VlWide<3>/*95:0*/ __Vtemp_17;
    VlWide<3>/*95:0*/ __Vtemp_18;
    VlWide<3>/*95:0*/ __Vtemp_19;
    VlWide<3>/*95:0*/ __Vtemp_20;
    VlWide<3>/*95:0*/ __Vtemp_22;
    VlWide<3>/*95:0*/ __Vtemp_23;
    VlWide<3>/*95:0*/ __Vtemp_24;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_27;
    VlWide<3>/*95:0*/ __Vtemp_29;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_32;
    VlWide<3>/*95:0*/ __Vtemp_34;
    VlWide<3>/*95:0*/ __Vtemp_35;
    VlWide<3>/*95:0*/ __Vtemp_36;
    VlWide<3>/*95:0*/ __Vtemp_38;
    VlWide<3>/*95:0*/ __Vtemp_39;
    VlWide<3>/*95:0*/ __Vtemp_41;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_44;
    VlWide<3>/*95:0*/ __Vtemp_46;
    VlWide<3>/*95:0*/ __Vtemp_47;
    VlWide<3>/*95:0*/ __Vtemp_48;
    VlWide<3>/*95:0*/ __Vtemp_50;
    VlWide<3>/*95:0*/ __Vtemp_51;
    VlWide<3>/*95:0*/ __Vtemp_53;
    VlWide<3>/*95:0*/ __Vtemp_54;
    VlWide<3>/*95:0*/ __Vtemp_55;
    VlWide<3>/*95:0*/ __Vtemp_56;
    VlWide<3>/*95:0*/ __Vtemp_58;
    VlWide<3>/*95:0*/ __Vtemp_59;
    VlWide<3>/*95:0*/ __Vtemp_60;
    VlWide<3>/*95:0*/ __Vtemp_62;
    VlWide<3>/*95:0*/ __Vtemp_63;
    VlWide<3>/*95:0*/ __Vtemp_65;
    VlWide<3>/*95:0*/ __Vtemp_66;
    VlWide<3>/*95:0*/ __Vtemp_67;
    VlWide<3>/*95:0*/ __Vtemp_68;
    VlWide<3>/*95:0*/ __Vtemp_70;
    VlWide<3>/*95:0*/ __Vtemp_71;
    VlWide<3>/*95:0*/ __Vtemp_72;
    VlWide<3>/*95:0*/ __Vtemp_74;
    VlWide<3>/*95:0*/ __Vtemp_75;
    VlWide<3>/*95:0*/ __Vtemp_77;
    VlWide<3>/*95:0*/ __Vtemp_78;
    VlWide<3>/*95:0*/ __Vtemp_79;
    VlWide<3>/*95:0*/ __Vtemp_80;
    VlWide<3>/*95:0*/ __Vtemp_82;
    VlWide<3>/*95:0*/ __Vtemp_83;
    VlWide<3>/*95:0*/ __Vtemp_84;
    VlWide<3>/*95:0*/ __Vtemp_86;
    VlWide<3>/*95:0*/ __Vtemp_87;
    VlWide<3>/*95:0*/ __Vtemp_89;
    VlWide<3>/*95:0*/ __Vtemp_90;
    VlWide<3>/*95:0*/ __Vtemp_91;
    VlWide<3>/*95:0*/ __Vtemp_92;
    VlWide<3>/*95:0*/ __Vtemp_94;
    VlWide<3>/*95:0*/ __Vtemp_95;
    VlWide<3>/*95:0*/ __Vtemp_96;
    VlWide<3>/*95:0*/ __Vtemp_98;
    VlWide<3>/*95:0*/ __Vtemp_99;
    VlWide<3>/*95:0*/ __Vtemp_101;
    VlWide<3>/*95:0*/ __Vtemp_102;
    VlWide<3>/*95:0*/ __Vtemp_103;
    VlWide<3>/*95:0*/ __Vtemp_104;
    VlWide<3>/*95:0*/ __Vtemp_106;
    VlWide<3>/*95:0*/ __Vtemp_107;
    VlWide<3>/*95:0*/ __Vtemp_108;
    VlWide<3>/*95:0*/ __Vtemp_110;
    VlWide<3>/*95:0*/ __Vtemp_111;
    VlWide<3>/*95:0*/ __Vtemp_113;
    VlWide<3>/*95:0*/ __Vtemp_114;
    VlWide<3>/*95:0*/ __Vtemp_115;
    VlWide<3>/*95:0*/ __Vtemp_116;
    VlWide<3>/*95:0*/ __Vtemp_118;
    VlWide<3>/*95:0*/ __Vtemp_119;
    VlWide<3>/*95:0*/ __Vtemp_120;
    VlWide<3>/*95:0*/ __Vtemp_122;
    VlWide<3>/*95:0*/ __Vtemp_123;
    VlWide<3>/*95:0*/ __Vtemp_125;
    VlWide<3>/*95:0*/ __Vtemp_126;
    VlWide<3>/*95:0*/ __Vtemp_127;
    VlWide<3>/*95:0*/ __Vtemp_128;
    VlWide<3>/*95:0*/ __Vtemp_130;
    VlWide<3>/*95:0*/ __Vtemp_131;
    VlWide<3>/*95:0*/ __Vtemp_132;
    VlWide<3>/*95:0*/ __Vtemp_134;
    VlWide<3>/*95:0*/ __Vtemp_135;
    VlWide<3>/*95:0*/ __Vtemp_137;
    VlWide<3>/*95:0*/ __Vtemp_138;
    VlWide<3>/*95:0*/ __Vtemp_139;
    VlWide<3>/*95:0*/ __Vtemp_140;
    VlWide<3>/*95:0*/ __Vtemp_142;
    VlWide<3>/*95:0*/ __Vtemp_143;
    VlWide<3>/*95:0*/ __Vtemp_144;
    VlWide<3>/*95:0*/ __Vtemp_146;
    VlWide<3>/*95:0*/ __Vtemp_147;
    VlWide<3>/*95:0*/ __Vtemp_149;
    VlWide<3>/*95:0*/ __Vtemp_150;
    VlWide<3>/*95:0*/ __Vtemp_151;
    VlWide<3>/*95:0*/ __Vtemp_152;
    VlWide<3>/*95:0*/ __Vtemp_154;
    VlWide<3>/*95:0*/ __Vtemp_155;
    VlWide<3>/*95:0*/ __Vtemp_156;
    VlWide<3>/*95:0*/ __Vtemp_157;
    VlWide<3>/*95:0*/ __Vtemp_158;
    VlWide<3>/*95:0*/ __Vtemp_159;
    VlWide<3>/*95:0*/ __Vtemp_160;
    VlWide<3>/*95:0*/ __Vtemp_161;
    VlWide<3>/*95:0*/ __Vtemp_162;
    VlWide<3>/*95:0*/ __Vtemp_163;
    VlWide<3>/*95:0*/ __Vtemp_164;
    VlWide<3>/*95:0*/ __Vtemp_165;
    VlWide<3>/*95:0*/ __Vtemp_166;
    VlWide<3>/*95:0*/ __Vtemp_167;
    VlWide<3>/*95:0*/ __Vtemp_168;
    VlWide<3>/*95:0*/ __Vtemp_169;
    VlWide<3>/*95:0*/ __Vtemp_170;
    VlWide<3>/*95:0*/ __Vtemp_171;
    VlWide<3>/*95:0*/ __Vtemp_172;
    VlWide<3>/*95:0*/ __Vtemp_173;
    VlWide<3>/*95:0*/ __Vtemp_174;
    VlWide<3>/*95:0*/ __Vtemp_175;
    VlWide<3>/*95:0*/ __Vtemp_176;
    VlWide<3>/*95:0*/ __Vtemp_177;
    VlWide<3>/*95:0*/ __Vtemp_178;
    VlWide<3>/*95:0*/ __Vtemp_179;
    VlWide<3>/*95:0*/ __Vtemp_180;
    VlWide<3>/*95:0*/ __Vtemp_181;
    VlWide<3>/*95:0*/ __Vtemp_182;
    VlWide<3>/*95:0*/ __Vtemp_183;
    VlWide<3>/*95:0*/ __Vtemp_184;
    VlWide<3>/*95:0*/ __Vtemp_185;
    VlWide<3>/*95:0*/ __Vtemp_186;
    VlWide<3>/*95:0*/ __Vtemp_187;
    VlWide<3>/*95:0*/ __Vtemp_188;
    VlWide<3>/*95:0*/ __Vtemp_189;
    VlWide<3>/*95:0*/ __Vtemp_190;
    VlWide<3>/*95:0*/ __Vtemp_191;
    VlWide<3>/*95:0*/ __Vtemp_192;
    VlWide<3>/*95:0*/ __Vtemp_193;
    VlWide<3>/*95:0*/ __Vtemp_194;
    VlWide<3>/*95:0*/ __Vtemp_195;
    VlWide<3>/*95:0*/ __Vtemp_196;
    VlWide<3>/*95:0*/ __Vtemp_197;
    VlWide<3>/*95:0*/ __Vtemp_198;
    VlWide<3>/*95:0*/ __Vtemp_199;
    VlWide<3>/*95:0*/ __Vtemp_200;
    VlWide<3>/*95:0*/ __Vtemp_201;
    VlWide<3>/*95:0*/ __Vtemp_202;
    VlWide<3>/*95:0*/ __Vtemp_203;
    VlWide<3>/*95:0*/ __Vtemp_204;
    VlWide<3>/*95:0*/ __Vtemp_205;
    VlWide<3>/*95:0*/ __Vtemp_206;
    VlWide<3>/*95:0*/ __Vtemp_207;
    VlWide<3>/*95:0*/ __Vtemp_208;
    // Body
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[1U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[0U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[1U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[0U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[1U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[0U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[0U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[1U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[3U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[2U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[3U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[2U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[3U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[2U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[2U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[3U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[5U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[4U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[5U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[4U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[5U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[4U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[4U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[5U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[7U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[6U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[7U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[6U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[7U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[6U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[6U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[7U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[9U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[8U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[9U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[8U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[9U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[8U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[8U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[9U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[11U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[10U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[11U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[10U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[11U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[10U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[10U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[11U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[13U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[12U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[13U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[12U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[13U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[12U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[12U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[13U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[15U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[14U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[15U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[14U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[15U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[14U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[14U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[15U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[17U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[16U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[17U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[16U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[17U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[16U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[16U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[17U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[19U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[18U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[19U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[18U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[19U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[18U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[18U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[19U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[21U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[20U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[21U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[20U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[21U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[20U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[20U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[21U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[23U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[22U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[23U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[22U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[23U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[22U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[22U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[23U]))))));
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[25U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[24U] 
                                                                             >> 0x00000010U)))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[25U])), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[24U]))))))));
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[25U] 
                                                                             >> 0x00000010U)), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[24U])))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__manifold_in[24U] 
                                                                               >> 0x00000010U)), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & vlSelfRef.spu13_lattice_tb__DOT__manifold_in[25U]))))));
    VL_EXTENDS_WQ(67,64, __Vtemp_2, VL_MULS_QQQ(64, 
                                                VL_EXTENDS_QI(64,32, (IData)(
                                                                             (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                                              >> 0x00000020U))), 
                                                VL_EXTENDS_QI(64,32, (IData)(
                                                                             (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                                              >> 0x00000020U)))));
    __Vtemp_3[0U] = 5U;
    __Vtemp_3[1U] = 0U;
    __Vtemp_3[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_5, VL_MULS_QQQ(64, 
                                                VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0)), 
                                                VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1))));
    __Vtemp_6[0U] = __Vtemp_5[0U];
    __Vtemp_6[1U] = __Vtemp_5[1U];
    __Vtemp_6[2U] = (7U & __Vtemp_5[2U]);
    VL_MULS_WWW(67, __Vtemp_7, __Vtemp_3, __Vtemp_6);
    VL_ADD_W(3, __Vtemp_8, __Vtemp_2, __Vtemp_7);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp[0U] 
        = __Vtemp_8[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp[1U] 
        = __Vtemp_8[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp[2U] 
        = (7U & __Vtemp_8[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_10, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1))));
    VL_EXTENDS_WQ(66,64, __Vtemp_11, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_12, __Vtemp_10, __Vtemp_11);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp[0U] 
        = __Vtemp_12[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp[1U] 
        = __Vtemp_12[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp[2U] 
        = (3U & __Vtemp_12[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_14, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                                               >> 0x00000020U)))));
    __Vtemp_15[0U] = 5U;
    __Vtemp_15[1U] = 0U;
    __Vtemp_15[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_17, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2))));
    __Vtemp_18[0U] = __Vtemp_17[0U];
    __Vtemp_18[1U] = __Vtemp_17[1U];
    __Vtemp_18[2U] = (7U & __Vtemp_17[2U]);
    VL_MULS_WWW(67, __Vtemp_19, __Vtemp_15, __Vtemp_18);
    VL_ADD_W(3, __Vtemp_20, __Vtemp_14, __Vtemp_19);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp[0U] 
        = __Vtemp_20[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp[1U] 
        = __Vtemp_20[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp[2U] 
        = (7U & __Vtemp_20[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_22, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2))));
    VL_EXTENDS_WQ(66,64, __Vtemp_23, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_24, __Vtemp_22, __Vtemp_23);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp[0U] 
        = __Vtemp_24[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp[1U] 
        = __Vtemp_24[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp[2U] 
        = (3U & __Vtemp_24[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_26, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                                               >> 0x00000020U)))));
    __Vtemp_27[0U] = 5U;
    __Vtemp_27[1U] = 0U;
    __Vtemp_27[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_29, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3))));
    __Vtemp_30[0U] = __Vtemp_29[0U];
    __Vtemp_30[1U] = __Vtemp_29[1U];
    __Vtemp_30[2U] = (7U & __Vtemp_29[2U]);
    VL_MULS_WWW(67, __Vtemp_31, __Vtemp_27, __Vtemp_30);
    VL_ADD_W(3, __Vtemp_32, __Vtemp_26, __Vtemp_31);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp[0U] 
        = __Vtemp_32[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp[1U] 
        = __Vtemp_32[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp[2U] 
        = (7U & __Vtemp_32[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_34, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3))));
    VL_EXTENDS_WQ(66,64, __Vtemp_35, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_36, __Vtemp_34, __Vtemp_35);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp[0U] 
        = __Vtemp_36[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp[1U] 
        = __Vtemp_36[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp[2U] 
        = (3U & __Vtemp_36[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_38, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                                               >> 0x00000020U)))));
    __Vtemp_39[0U] = 5U;
    __Vtemp_39[1U] = 0U;
    __Vtemp_39[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_41, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4))));
    __Vtemp_42[0U] = __Vtemp_41[0U];
    __Vtemp_42[1U] = __Vtemp_41[1U];
    __Vtemp_42[2U] = (7U & __Vtemp_41[2U]);
    VL_MULS_WWW(67, __Vtemp_43, __Vtemp_39, __Vtemp_42);
    VL_ADD_W(3, __Vtemp_44, __Vtemp_38, __Vtemp_43);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp[0U] 
        = __Vtemp_44[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp[1U] 
        = __Vtemp_44[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp[2U] 
        = (7U & __Vtemp_44[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_46, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4))));
    VL_EXTENDS_WQ(66,64, __Vtemp_47, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_48, __Vtemp_46, __Vtemp_47);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp[0U] 
        = __Vtemp_48[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp[1U] 
        = __Vtemp_48[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp[2U] 
        = (3U & __Vtemp_48[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_50, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                                               >> 0x00000020U)))));
    __Vtemp_51[0U] = 5U;
    __Vtemp_51[1U] = 0U;
    __Vtemp_51[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_53, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5))));
    __Vtemp_54[0U] = __Vtemp_53[0U];
    __Vtemp_54[1U] = __Vtemp_53[1U];
    __Vtemp_54[2U] = (7U & __Vtemp_53[2U]);
    VL_MULS_WWW(67, __Vtemp_55, __Vtemp_51, __Vtemp_54);
    VL_ADD_W(3, __Vtemp_56, __Vtemp_50, __Vtemp_55);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp[0U] 
        = __Vtemp_56[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp[1U] 
        = __Vtemp_56[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp[2U] 
        = (7U & __Vtemp_56[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_58, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5))));
    VL_EXTENDS_WQ(66,64, __Vtemp_59, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_60, __Vtemp_58, __Vtemp_59);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp[0U] 
        = __Vtemp_60[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp[1U] 
        = __Vtemp_60[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp[2U] 
        = (3U & __Vtemp_60[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_62, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                                               >> 0x00000020U)))));
    __Vtemp_63[0U] = 5U;
    __Vtemp_63[1U] = 0U;
    __Vtemp_63[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_65, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6))));
    __Vtemp_66[0U] = __Vtemp_65[0U];
    __Vtemp_66[1U] = __Vtemp_65[1U];
    __Vtemp_66[2U] = (7U & __Vtemp_65[2U]);
    VL_MULS_WWW(67, __Vtemp_67, __Vtemp_63, __Vtemp_66);
    VL_ADD_W(3, __Vtemp_68, __Vtemp_62, __Vtemp_67);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp[0U] 
        = __Vtemp_68[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp[1U] 
        = __Vtemp_68[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp[2U] 
        = (7U & __Vtemp_68[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_70, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6))));
    VL_EXTENDS_WQ(66,64, __Vtemp_71, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_72, __Vtemp_70, __Vtemp_71);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp[0U] 
        = __Vtemp_72[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp[1U] 
        = __Vtemp_72[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp[2U] 
        = (3U & __Vtemp_72[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_74, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                                               >> 0x00000020U)))));
    __Vtemp_75[0U] = 5U;
    __Vtemp_75[1U] = 0U;
    __Vtemp_75[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_77, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7))));
    __Vtemp_78[0U] = __Vtemp_77[0U];
    __Vtemp_78[1U] = __Vtemp_77[1U];
    __Vtemp_78[2U] = (7U & __Vtemp_77[2U]);
    VL_MULS_WWW(67, __Vtemp_79, __Vtemp_75, __Vtemp_78);
    VL_ADD_W(3, __Vtemp_80, __Vtemp_74, __Vtemp_79);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp[0U] 
        = __Vtemp_80[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp[1U] 
        = __Vtemp_80[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp[2U] 
        = (7U & __Vtemp_80[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_82, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7))));
    VL_EXTENDS_WQ(66,64, __Vtemp_83, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_84, __Vtemp_82, __Vtemp_83);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp[0U] 
        = __Vtemp_84[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp[1U] 
        = __Vtemp_84[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp[2U] 
        = (3U & __Vtemp_84[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_86, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                                               >> 0x00000020U)))));
    __Vtemp_87[0U] = 5U;
    __Vtemp_87[1U] = 0U;
    __Vtemp_87[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_89, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8))));
    __Vtemp_90[0U] = __Vtemp_89[0U];
    __Vtemp_90[1U] = __Vtemp_89[1U];
    __Vtemp_90[2U] = (7U & __Vtemp_89[2U]);
    VL_MULS_WWW(67, __Vtemp_91, __Vtemp_87, __Vtemp_90);
    VL_ADD_W(3, __Vtemp_92, __Vtemp_86, __Vtemp_91);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp[0U] 
        = __Vtemp_92[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp[1U] 
        = __Vtemp_92[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp[2U] 
        = (7U & __Vtemp_92[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_94, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8))));
    VL_EXTENDS_WQ(66,64, __Vtemp_95, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7)), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                                               >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_96, __Vtemp_94, __Vtemp_95);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp[0U] 
        = __Vtemp_96[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp[1U] 
        = __Vtemp_96[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp[2U] 
        = (3U & __Vtemp_96[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_98, VL_MULS_QQQ(64, 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                                               >> 0x00000020U))), 
                                                 VL_EXTENDS_QI(64,32, (IData)(
                                                                              (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                                               >> 0x00000020U)))));
    __Vtemp_99[0U] = 5U;
    __Vtemp_99[1U] = 0U;
    __Vtemp_99[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_101, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9))));
    __Vtemp_102[0U] = __Vtemp_101[0U];
    __Vtemp_102[1U] = __Vtemp_101[1U];
    __Vtemp_102[2U] = (7U & __Vtemp_101[2U]);
    VL_MULS_WWW(67, __Vtemp_103, __Vtemp_99, __Vtemp_102);
    VL_ADD_W(3, __Vtemp_104, __Vtemp_98, __Vtemp_103);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp[0U] 
        = __Vtemp_104[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp[1U] 
        = __Vtemp_104[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp[2U] 
        = (7U & __Vtemp_104[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_106, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9))));
    VL_EXTENDS_WQ(66,64, __Vtemp_107, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                                                >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_108, __Vtemp_106, __Vtemp_107);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp[0U] 
        = __Vtemp_108[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp[1U] 
        = __Vtemp_108[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp[2U] 
        = (3U & __Vtemp_108[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_110, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                                                >> 0x00000020U)))));
    __Vtemp_111[0U] = 5U;
    __Vtemp_111[1U] = 0U;
    __Vtemp_111[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_113, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10))));
    __Vtemp_114[0U] = __Vtemp_113[0U];
    __Vtemp_114[1U] = __Vtemp_113[1U];
    __Vtemp_114[2U] = (7U & __Vtemp_113[2U]);
    VL_MULS_WWW(67, __Vtemp_115, __Vtemp_111, __Vtemp_114);
    VL_ADD_W(3, __Vtemp_116, __Vtemp_110, __Vtemp_115);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp[0U] 
        = __Vtemp_116[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp[1U] 
        = __Vtemp_116[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp[2U] 
        = (7U & __Vtemp_116[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_118, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10))));
    VL_EXTENDS_WQ(66,64, __Vtemp_119, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                                                >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_120, __Vtemp_118, __Vtemp_119);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp[0U] 
        = __Vtemp_120[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp[1U] 
        = __Vtemp_120[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp[2U] 
        = (3U & __Vtemp_120[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_122, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                                                >> 0x00000020U)))));
    __Vtemp_123[0U] = 5U;
    __Vtemp_123[1U] = 0U;
    __Vtemp_123[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_125, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11))));
    __Vtemp_126[0U] = __Vtemp_125[0U];
    __Vtemp_126[1U] = __Vtemp_125[1U];
    __Vtemp_126[2U] = (7U & __Vtemp_125[2U]);
    VL_MULS_WWW(67, __Vtemp_127, __Vtemp_123, __Vtemp_126);
    VL_ADD_W(3, __Vtemp_128, __Vtemp_122, __Vtemp_127);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp[0U] 
        = __Vtemp_128[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp[1U] 
        = __Vtemp_128[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp[2U] 
        = (7U & __Vtemp_128[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_130, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11))));
    VL_EXTENDS_WQ(66,64, __Vtemp_131, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                                                >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_132, __Vtemp_130, __Vtemp_131);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp[0U] 
        = __Vtemp_132[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp[1U] 
        = __Vtemp_132[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp[2U] 
        = (3U & __Vtemp_132[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_134, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                                                >> 0x00000020U)))));
    __Vtemp_135[0U] = 5U;
    __Vtemp_135[1U] = 0U;
    __Vtemp_135[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_137, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12))));
    __Vtemp_138[0U] = __Vtemp_137[0U];
    __Vtemp_138[1U] = __Vtemp_137[1U];
    __Vtemp_138[2U] = (7U & __Vtemp_137[2U]);
    VL_MULS_WWW(67, __Vtemp_139, __Vtemp_135, __Vtemp_138);
    VL_ADD_W(3, __Vtemp_140, __Vtemp_134, __Vtemp_139);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp[0U] 
        = __Vtemp_140[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp[1U] 
        = __Vtemp_140[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp[2U] 
        = (7U & __Vtemp_140[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_142, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12))));
    VL_EXTENDS_WQ(66,64, __Vtemp_143, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                                                >> 0x00000020U)))));
    VL_ADD_W(3, __Vtemp_144, __Vtemp_142, __Vtemp_143);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp[0U] 
        = __Vtemp_144[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp[1U] 
        = __Vtemp_144[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp[2U] 
        = (3U & __Vtemp_144[2U]);
    VL_EXTENDS_WQ(67,64, __Vtemp_146, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                                                >> 0x00000020U)))));
    __Vtemp_147[0U] = 5U;
    __Vtemp_147[1U] = 0U;
    __Vtemp_147[2U] = 0U;
    VL_EXTENDS_WQ(67,64, __Vtemp_149, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12))));
    __Vtemp_150[0U] = __Vtemp_149[0U];
    __Vtemp_150[1U] = __Vtemp_149[1U];
    __Vtemp_150[2U] = (7U & __Vtemp_149[2U]);
    VL_MULS_WWW(67, __Vtemp_151, __Vtemp_147, __Vtemp_150);
    VL_ADD_W(3, __Vtemp_152, __Vtemp_146, __Vtemp_151);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp[0U] 
        = __Vtemp_152[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp[1U] 
        = __Vtemp_152[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp[2U] 
        = (7U & __Vtemp_152[2U]);
    VL_EXTENDS_WQ(66,64, __Vtemp_154, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0)), 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                                                >> 0x00000020U)))));
    VL_EXTENDS_WQ(66,64, __Vtemp_155, VL_MULS_QQQ(64, 
                                                  VL_EXTENDS_QI(64,32, (IData)(
                                                                               (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                                                >> 0x00000020U))), 
                                                  VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12))));
    VL_ADD_W(3, __Vtemp_156, __Vtemp_154, __Vtemp_155);
    spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp[0U] 
        = __Vtemp_156[0U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp[1U] 
        = __Vtemp_156[1U];
    spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp[2U] 
        = (3U & __Vtemp_156[2U]);
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    __Vtemp_157[0U] = 0x7fffffffU;
    __Vtemp_157[1U] = 0U;
    __Vtemp_157[2U] = 0U;
    __Vtemp_158[0U] = 0x80000000U;
    __Vtemp_158[1U] = 0xffffffffU;
    __Vtemp_158[2U] = 7U;
    __VdfgRegularize_he50b618e_0_0 = (VL_LTS_IWW(67, __Vtemp_157, spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp)
                                       ? 0x7fffffffU
                                       : (VL_GTS_IWW(67, __Vtemp_158, spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp)
                                           ? 0x80000000U
                                           : spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__p_tmp[0U]));
    __Vtemp_159[0U] = 0x7fffffffU;
    __Vtemp_159[1U] = 0U;
    __Vtemp_159[2U] = 0U;
    __Vtemp_160[0U] = 0x80000000U;
    __Vtemp_160[1U] = 0xffffffffU;
    __Vtemp_160[2U] = 3U;
    __VdfgRegularize_he50b618e_0_1 = (VL_LTS_IWW(66, __Vtemp_159, spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp)
                                       ? 0x7fffffffU
                                       : (VL_GTS_IWW(66, __Vtemp_160, spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp)
                                           ? 0x80000000U
                                           : spu13_lattice_tb__DOT__uut__DOT__u_mul_01__DOT__q_tmp[0U]));
    __Vtemp_161[0U] = 0x7fffffffU;
    __Vtemp_161[1U] = 0U;
    __Vtemp_161[2U] = 0U;
    __Vtemp_162[0U] = 0x80000000U;
    __Vtemp_162[1U] = 0xffffffffU;
    __Vtemp_162[2U] = 7U;
    __VdfgRegularize_he50b618e_0_6 = (VL_LTS_IWW(67, __Vtemp_161, spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp)
                                       ? 0x7fffffffU
                                       : (VL_GTS_IWW(67, __Vtemp_162, spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp)
                                           ? 0x80000000U
                                           : spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__p_tmp[0U]));
    __Vtemp_163[0U] = 0x7fffffffU;
    __Vtemp_163[1U] = 0U;
    __Vtemp_163[2U] = 0U;
    __Vtemp_164[0U] = 0x80000000U;
    __Vtemp_164[1U] = 0xffffffffU;
    __Vtemp_164[2U] = 3U;
    __VdfgRegularize_he50b618e_0_7 = (VL_LTS_IWW(66, __Vtemp_163, spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp)
                                       ? 0x7fffffffU
                                       : (VL_GTS_IWW(66, __Vtemp_164, spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp)
                                           ? 0x80000000U
                                           : spu13_lattice_tb__DOT__uut__DOT__u_mul_12__DOT__q_tmp[0U]));
    __Vtemp_165[0U] = 0x7fffffffU;
    __Vtemp_165[1U] = 0U;
    __Vtemp_165[2U] = 0U;
    __Vtemp_166[0U] = 0x80000000U;
    __Vtemp_166[1U] = 0xffffffffU;
    __Vtemp_166[2U] = 7U;
    __VdfgRegularize_he50b618e_0_10 = (VL_LTS_IWW(67, __Vtemp_165, spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_166, spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__p_tmp[0U]));
    __Vtemp_167[0U] = 0x7fffffffU;
    __Vtemp_167[1U] = 0U;
    __Vtemp_167[2U] = 0U;
    __Vtemp_168[0U] = 0x80000000U;
    __Vtemp_168[1U] = 0xffffffffU;
    __Vtemp_168[2U] = 3U;
    __VdfgRegularize_he50b618e_0_11 = (VL_LTS_IWW(66, __Vtemp_167, spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_168, spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_23__DOT__q_tmp[0U]));
    __Vtemp_169[0U] = 0x7fffffffU;
    __Vtemp_169[1U] = 0U;
    __Vtemp_169[2U] = 0U;
    __Vtemp_170[0U] = 0x80000000U;
    __Vtemp_170[1U] = 0xffffffffU;
    __Vtemp_170[2U] = 7U;
    __VdfgRegularize_he50b618e_0_14 = (VL_LTS_IWW(67, __Vtemp_169, spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_170, spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__p_tmp[0U]));
    __Vtemp_171[0U] = 0x7fffffffU;
    __Vtemp_171[1U] = 0U;
    __Vtemp_171[2U] = 0U;
    __Vtemp_172[0U] = 0x80000000U;
    __Vtemp_172[1U] = 0xffffffffU;
    __Vtemp_172[2U] = 3U;
    __VdfgRegularize_he50b618e_0_15 = (VL_LTS_IWW(66, __Vtemp_171, spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_172, spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_34__DOT__q_tmp[0U]));
    __Vtemp_173[0U] = 0x7fffffffU;
    __Vtemp_173[1U] = 0U;
    __Vtemp_173[2U] = 0U;
    __Vtemp_174[0U] = 0x80000000U;
    __Vtemp_174[1U] = 0xffffffffU;
    __Vtemp_174[2U] = 7U;
    __VdfgRegularize_he50b618e_0_18 = (VL_LTS_IWW(67, __Vtemp_173, spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_174, spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__p_tmp[0U]));
    __Vtemp_175[0U] = 0x7fffffffU;
    __Vtemp_175[1U] = 0U;
    __Vtemp_175[2U] = 0U;
    __Vtemp_176[0U] = 0x80000000U;
    __Vtemp_176[1U] = 0xffffffffU;
    __Vtemp_176[2U] = 3U;
    __VdfgRegularize_he50b618e_0_19 = (VL_LTS_IWW(66, __Vtemp_175, spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_176, spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_45__DOT__q_tmp[0U]));
    __Vtemp_177[0U] = 0x7fffffffU;
    __Vtemp_177[1U] = 0U;
    __Vtemp_177[2U] = 0U;
    __Vtemp_178[0U] = 0x80000000U;
    __Vtemp_178[1U] = 0xffffffffU;
    __Vtemp_178[2U] = 7U;
    __VdfgRegularize_he50b618e_0_22 = (VL_LTS_IWW(67, __Vtemp_177, spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_178, spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__p_tmp[0U]));
    __Vtemp_179[0U] = 0x7fffffffU;
    __Vtemp_179[1U] = 0U;
    __Vtemp_179[2U] = 0U;
    __Vtemp_180[0U] = 0x80000000U;
    __Vtemp_180[1U] = 0xffffffffU;
    __Vtemp_180[2U] = 3U;
    __VdfgRegularize_he50b618e_0_23 = (VL_LTS_IWW(66, __Vtemp_179, spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_180, spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_56__DOT__q_tmp[0U]));
    __Vtemp_181[0U] = 0x7fffffffU;
    __Vtemp_181[1U] = 0U;
    __Vtemp_181[2U] = 0U;
    __Vtemp_182[0U] = 0x80000000U;
    __Vtemp_182[1U] = 0xffffffffU;
    __Vtemp_182[2U] = 7U;
    __VdfgRegularize_he50b618e_0_26 = (VL_LTS_IWW(67, __Vtemp_181, spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_182, spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__p_tmp[0U]));
    __Vtemp_183[0U] = 0x7fffffffU;
    __Vtemp_183[1U] = 0U;
    __Vtemp_183[2U] = 0U;
    __Vtemp_184[0U] = 0x80000000U;
    __Vtemp_184[1U] = 0xffffffffU;
    __Vtemp_184[2U] = 3U;
    __VdfgRegularize_he50b618e_0_27 = (VL_LTS_IWW(66, __Vtemp_183, spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_184, spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_67__DOT__q_tmp[0U]));
    __Vtemp_185[0U] = 0x7fffffffU;
    __Vtemp_185[1U] = 0U;
    __Vtemp_185[2U] = 0U;
    __Vtemp_186[0U] = 0x80000000U;
    __Vtemp_186[1U] = 0xffffffffU;
    __Vtemp_186[2U] = 7U;
    __VdfgRegularize_he50b618e_0_30 = (VL_LTS_IWW(67, __Vtemp_185, spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_186, spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__p_tmp[0U]));
    __Vtemp_187[0U] = 0x7fffffffU;
    __Vtemp_187[1U] = 0U;
    __Vtemp_187[2U] = 0U;
    __Vtemp_188[0U] = 0x80000000U;
    __Vtemp_188[1U] = 0xffffffffU;
    __Vtemp_188[2U] = 3U;
    __VdfgRegularize_he50b618e_0_31 = (VL_LTS_IWW(66, __Vtemp_187, spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_188, spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_78__DOT__q_tmp[0U]));
    __Vtemp_189[0U] = 0x7fffffffU;
    __Vtemp_189[1U] = 0U;
    __Vtemp_189[2U] = 0U;
    __Vtemp_190[0U] = 0x80000000U;
    __Vtemp_190[1U] = 0xffffffffU;
    __Vtemp_190[2U] = 7U;
    __VdfgRegularize_he50b618e_0_34 = (VL_LTS_IWW(67, __Vtemp_189, spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_190, spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__p_tmp[0U]));
    __Vtemp_191[0U] = 0x7fffffffU;
    __Vtemp_191[1U] = 0U;
    __Vtemp_191[2U] = 0U;
    __Vtemp_192[0U] = 0x80000000U;
    __Vtemp_192[1U] = 0xffffffffU;
    __Vtemp_192[2U] = 3U;
    __VdfgRegularize_he50b618e_0_35 = (VL_LTS_IWW(66, __Vtemp_191, spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_192, spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_89__DOT__q_tmp[0U]));
    __Vtemp_193[0U] = 0x7fffffffU;
    __Vtemp_193[1U] = 0U;
    __Vtemp_193[2U] = 0U;
    __Vtemp_194[0U] = 0x80000000U;
    __Vtemp_194[1U] = 0xffffffffU;
    __Vtemp_194[2U] = 7U;
    __VdfgRegularize_he50b618e_0_38 = (VL_LTS_IWW(67, __Vtemp_193, spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_194, spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__p_tmp[0U]));
    __Vtemp_195[0U] = 0x7fffffffU;
    __Vtemp_195[1U] = 0U;
    __Vtemp_195[2U] = 0U;
    __Vtemp_196[0U] = 0x80000000U;
    __Vtemp_196[1U] = 0xffffffffU;
    __Vtemp_196[2U] = 3U;
    __VdfgRegularize_he50b618e_0_39 = (VL_LTS_IWW(66, __Vtemp_195, spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_196, spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_9a__DOT__q_tmp[0U]));
    __Vtemp_197[0U] = 0x7fffffffU;
    __Vtemp_197[1U] = 0U;
    __Vtemp_197[2U] = 0U;
    __Vtemp_198[0U] = 0x80000000U;
    __Vtemp_198[1U] = 0xffffffffU;
    __Vtemp_198[2U] = 7U;
    __VdfgRegularize_he50b618e_0_42 = (VL_LTS_IWW(67, __Vtemp_197, spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_198, spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__p_tmp[0U]));
    __Vtemp_199[0U] = 0x7fffffffU;
    __Vtemp_199[1U] = 0U;
    __Vtemp_199[2U] = 0U;
    __Vtemp_200[0U] = 0x80000000U;
    __Vtemp_200[1U] = 0xffffffffU;
    __Vtemp_200[2U] = 3U;
    __VdfgRegularize_he50b618e_0_43 = (VL_LTS_IWW(66, __Vtemp_199, spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_200, spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_ab__DOT__q_tmp[0U]));
    __Vtemp_201[0U] = 0x7fffffffU;
    __Vtemp_201[1U] = 0U;
    __Vtemp_201[2U] = 0U;
    __Vtemp_202[0U] = 0x80000000U;
    __Vtemp_202[1U] = 0xffffffffU;
    __Vtemp_202[2U] = 7U;
    __VdfgRegularize_he50b618e_0_46 = (VL_LTS_IWW(67, __Vtemp_201, spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_202, spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__p_tmp[0U]));
    __Vtemp_203[0U] = 0x7fffffffU;
    __Vtemp_203[1U] = 0U;
    __Vtemp_203[2U] = 0U;
    __Vtemp_204[0U] = 0x80000000U;
    __Vtemp_204[1U] = 0xffffffffU;
    __Vtemp_204[2U] = 3U;
    __VdfgRegularize_he50b618e_0_47 = (VL_LTS_IWW(66, __Vtemp_203, spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_204, spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_bc__DOT__q_tmp[0U]));
    __Vtemp_205[0U] = 0x7fffffffU;
    __Vtemp_205[1U] = 0U;
    __Vtemp_205[2U] = 0U;
    __Vtemp_206[0U] = 0x80000000U;
    __Vtemp_206[1U] = 0xffffffffU;
    __Vtemp_206[2U] = 7U;
    __VdfgRegularize_he50b618e_0_50 = (VL_LTS_IWW(67, __Vtemp_205, spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(67, __Vtemp_206, spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__p_tmp[0U]));
    __Vtemp_207[0U] = 0x7fffffffU;
    __Vtemp_207[1U] = 0U;
    __Vtemp_207[2U] = 0U;
    __Vtemp_208[0U] = 0x80000000U;
    __Vtemp_208[1U] = 0xffffffffU;
    __Vtemp_208[2U] = 3U;
    __VdfgRegularize_he50b618e_0_51 = (VL_LTS_IWW(66, __Vtemp_207, spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(66, __Vtemp_208, spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp)
                                            ? 0x80000000U
                                            : spu13_lattice_tb__DOT__uut__DOT__u_mul_c0__DOT__q_tmp[0U]));
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_0 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_0)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out0))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_1 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_1)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_6 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_6)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out1))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_7 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_7)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_10 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_10)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out2))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_11 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_11)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_14 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_14)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out3))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_15 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_15)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_18 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_18)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out4))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_19 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_19)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_22 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_22)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out5))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_23 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_23)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_26 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_26)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out6))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_27 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_27)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_30 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_30)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out7))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_31 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_31)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_34 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_34)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out8))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_35 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_35)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_38 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_38)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out9))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_39 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_39)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_42 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_42)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out10))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_43 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_43)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_46 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_46)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out11))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_47 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_47)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__p_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                                  >> 0x0000003fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(
                                                       (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                        >> 0x00000020U)))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_50 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_50)))));
    spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__q_tmp 
        = (0x00000001ffffffffULL & ((((QData)((IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12 
                                                                  >> 0x0000001fU))))) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_out12))) 
                                    + (((QData)((IData)(
                                                        (__VdfgRegularize_he50b618e_0_51 
                                                         >> 0x0000001fU))) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(__VdfgRegularize_he50b618e_0_51)))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_0__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_1__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_2__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_3__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_4__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_5__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_6__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_7__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_8__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_9__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_10__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_11__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__p_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__p_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__p_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ 
        = (VL_LTS_IQQ(33, 0x000000007fffffffULL, spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__q_tmp)
            ? 0x7fffffffU : (VL_GTS_IQQ(33, 0x0000000180000000ULL, spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__q_tmp)
                              ? 0x80000000U : (IData)(spu13_lattice_tb__DOT__uut__DOT__u_add_12__DOT__q_tmp)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ_ext 
        = (((QData)((IData)((spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ)));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ_ext))));
    spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP_ext)
                                                      ? 
                                                     (- spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP_ext)
                                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ_ext)
                                                   ? 
                                                  (- spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ_ext)
                                                   : spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ_ext))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[0U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[1U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_0__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[2U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[3U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_1__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[4U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[5U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_2__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[6U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[7U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_3__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[8U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[9U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_4__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[10U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[11U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_5__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[12U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[13U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_6__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[14U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[15U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_7__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[16U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[17U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_8__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[18U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[19U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_9__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[20U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[21U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_10__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[22U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[23U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_11__DOT__inQ)))) 
                   >> 0x00000020U));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[24U] 
        = (IData)((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift)
                                      ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP, 1U)
                                      : spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP))) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift)
                                                        ? 
                                                       VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ, 1U)
                                                        : spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ)))));
    vlSelfRef.spu13_lattice_tb__DOT__manifold_out[25U] 
        = (IData)(((((QData)((IData)(((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift)
                                       ? VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP, 1U)
                                       : spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inP))) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((IData)(spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__need_shift)
                                                         ? 
                                                        VL_SHIFTRS_III(32,32,32, spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ, 1U)
                                                         : spu13_lattice_tb__DOT__uut__DOT__u_norm_12__DOT__inQ)))) 
                   >> 0x00000020U));
}

VL_ATTR_COLD void Vspu13_lattice_tb___024root___eval_stl(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_stl\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu13_lattice_tb__DOT__clk = (1U 
                                                & (~ (IData)(vlSelfRef.spu13_lattice_tb__DOT__clk)));
    }
    if ((1ULL & vlSelfRef.__VstlTriggered[1U])) {
        Vspu13_lattice_tb___024root___stl_sequent__TOP__1(vlSelf);
    }
}

VL_ATTR_COLD bool Vspu13_lattice_tb___024root___eval_phase__stl(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___eval_phase__stl\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu13_lattice_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu13_lattice_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu13_lattice_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu13_lattice_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vspu13_lattice_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu13_lattice_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu13_lattice_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu13_lattice_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge spu13_lattice_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge spu13_lattice_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vspu13_lattice_tb___024root___ctor_var_reset(Vspu13_lattice_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu13_lattice_tb___024root___ctor_var_reset\n"); );
    Vspu13_lattice_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    VL_SCOPED_RAND_RESET_W(832, vlSelf->spu13_lattice_tb__DOT__manifold_out, __VscopeHash, 960356871066967577ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out0 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 16112438828928446028ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out1 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 4580035347816976813ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out2 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 4446042677008730120ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out3 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 2940879640951343136ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out4 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 13016769610401481404ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out5 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 11874579031345837004ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out6 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 11379946445119970672ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out7 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 16835188052537572857ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out8 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 5018679006261527709ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out9 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 6000712715907712002ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out10 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 5025826357807763382ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out11 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 18205614237938446052ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_out12 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 10011855418770577078ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16849052991234633458ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15041666218853676513ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_0__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4450687714395839086ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2227665536605341701ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4098629984511635092ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_1__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4110694966674869142ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14833006705587374314ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2577448324422261262ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_2__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3946456901817422295ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1286733247419344820ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11034631507781711126ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_3__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2738298212727850681ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10395656071083349307ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6152385625377146832ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_4__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13038616931902499909ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5912559921277606688ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13789158947092813193ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_5__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11840190576178355762ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15152619470900155842ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10294441128814849248ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_6__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17496132089535333512ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5480567052622436880ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1315467646930134800ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_7__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3577014160448490329ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11202562679576757922ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6076862138605344706ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_8__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13628594713133908874ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9878337258296013721ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10275360204840824663ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_9__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6205391159642162249ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 519791007922463845ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11596028185244847808ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_10__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6066228811428474601ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12851113078379100249ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8737356665266816713ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_11__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17521382054016659167ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16726598330970972815ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13363383147717288616ull);
    vlSelf->spu13_lattice_tb__DOT__uut__DOT__node_12__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4886629625601919015ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu13_lattice_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu13_lattice_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
