// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vlaminar_node_tb.h for the primary calling header

#include "Vlaminar_node_tb__pch.h"

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_static(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_static\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.laminar_node_tb__DOT__clk = 0U;
    vlSelfRef.laminar_node_tb__DOT__rst_n = 0U;
    vlSelfRef.laminar_node_tb__DOT__surd_in = 0ULL;
    vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0 = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__rst_n__0 = 0U;
}

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_static__TOP(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_static__TOP\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.laminar_node_tb__DOT__clk = 0U;
    vlSelfRef.laminar_node_tb__DOT__rst_n = 0U;
    vlSelfRef.laminar_node_tb__DOT__surd_in = 0ULL;
}

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_initial(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_initial\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.laminar_node_tb__DOT__rst_n = 1U;
    vlSelfRef.laminar_node_tb__DOT__surd_in = 0x0002000300040005ULL;
    if ((0x0000005300000016ULL == vlSelfRef.laminar_node_tb__DOT__surd_out)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL: got %h\n",1, '#',64,vlSelfRef.laminar_node_tb__DOT__surd_out);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/laminar_node_tb.v", 36, "");
}

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_initial__TOP(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_initial__TOP\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.laminar_node_tb__DOT__rst_n = 1U;
    vlSelfRef.laminar_node_tb__DOT__surd_in = 0x0002000300040005ULL;
    if ((0x0000005300000016ULL == vlSelfRef.laminar_node_tb__DOT__surd_out)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL: got %h\n",1, '#',64,vlSelfRef.laminar_node_tb__DOT__surd_out);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/laminar_node_tb.v", 36, "");
}

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_final(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_final\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vlaminar_node_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vlaminar_node_tb___024root___eval_phase__stl(Vlaminar_node_tb___024root* vlSelf);

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_settle(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_settle\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vlaminar_node_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/laminar_node_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vlaminar_node_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_triggers_vec__stl(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_triggers_vec__stl\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.laminar_node_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0 
        = vlSelfRef.laminar_node_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vlaminar_node_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vlaminar_node_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vlaminar_node_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] laminar_node_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vlaminar_node_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vlaminar_node_tb___024root___stl_sequent__TOP__1(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___stl_sequent__TOP__1\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*33:0*/ laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp;
    laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp;
    laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext;
    laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext;
    laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext = 0;
    // Body
    laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
        = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000030U)))), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000010U)))))) 
                                    + VL_MULS_QQQ(34, 5ULL, 
                                                  (0x00000003ffffffffULL 
                                                   & VL_EXTENDS_QI(34,32, 
                                                                   VL_MULS_III(32, 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000020U)))), 
                                                                               VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(vlSelfRef.laminar_node_tb__DOT__surd_in)))))))));
    laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
        = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                  VL_MULS_III(32, 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000030U)))), 
                                                              VL_EXTENDS_II(32,16, 
                                                                            (0x0000ffffU 
                                                                             & (IData)(vlSelfRef.laminar_node_tb__DOT__surd_in))))) 
                                    + VL_EXTENDS_QI(33,32, 
                                                    VL_MULS_III(32, 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000010U)))), 
                                                                VL_EXTENDS_II(32,16, 
                                                                              (0x0000ffffU 
                                                                               & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000020U))))))));
    vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP 
        = (((7U & (IData)((laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
                           >> 0x0000001fU))) == (7U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp)
            : ((1U & (IData)((laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
                              >> 0x00000021U))) ? 0x80000000U
                : 0x7fffffffU));
    vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ 
        = (((3U & (IData)((laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
                           >> 0x0000001fU))) == (3U 
                                                 & (- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
                                                                          >> 0x0000001fU)))))))
            ? (IData)(laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp)
            : ((1U & (IData)((laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
                              >> 0x00000020U))) ? 0x80000000U
                : 0x7fffffffU));
    laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext 
        = (((QData)((IData)((vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP)));
    laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext 
        = (((QData)((IData)((vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ)));
    vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext)
                                                      ? 
                                                     (- laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext)
                                                      : laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext)
                                                   ? 
                                                  (- laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext)
                                                   : laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext))));
}

VL_ATTR_COLD void Vlaminar_node_tb___024root___eval_stl(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_stl\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*33:0*/ __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp;
    __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp = 0;
    QData/*32:0*/ __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp;
    __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp = 0;
    QData/*32:0*/ __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext;
    __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext = 0;
    QData/*32:0*/ __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext;
    __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext = 0;
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.laminar_node_tb__DOT__clk = (1U & 
                                               (~ (IData)(vlSelfRef.laminar_node_tb__DOT__clk)));
    }
    if ((1ULL & vlSelfRef.__VstlTriggered[1U])) {
        __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
            = (0x00000003ffffffffULL & (VL_EXTENDS_QI(34,32, 
                                                      VL_MULS_III(32, 
                                                                  VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000030U)))), 
                                                                  VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000010U)))))) 
                                        + VL_MULS_QQQ(34, 5ULL, 
                                                      (0x00000003ffffffffULL 
                                                       & VL_EXTENDS_QI(34,32, 
                                                                       VL_MULS_III(32, 
                                                                                VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000020U)))), 
                                                                                VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(vlSelfRef.laminar_node_tb__DOT__surd_in)))))))));
        __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
            = (0x00000001ffffffffULL & (VL_EXTENDS_QI(33,32, 
                                                      VL_MULS_III(32, 
                                                                  VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000030U)))), 
                                                                  VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(vlSelfRef.laminar_node_tb__DOT__surd_in))))) 
                                        + VL_EXTENDS_QI(33,32, 
                                                        VL_MULS_III(32, 
                                                                    VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000010U)))), 
                                                                    VL_EXTENDS_II(32,16, 
                                                                                (0x0000ffffU 
                                                                                & (IData)(
                                                                                (vlSelfRef.laminar_node_tb__DOT__surd_in 
                                                                                >> 0x00000020U))))))));
        vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP 
            = (((7U & (IData)((__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
                               >> 0x0000001fU))) == 
                (7U & (- (IData)((1U & (IData)((__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
                                                >> 0x0000001fU)))))))
                ? (IData)(__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp)
                : ((1U & (IData)((__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__p_tmp 
                                  >> 0x00000021U)))
                    ? 0x80000000U : 0x7fffffffU));
        vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ 
            = (((3U & (IData)((__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
                               >> 0x0000001fU))) == 
                (3U & (- (IData)((1U & (IData)((__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
                                                >> 0x0000001fU)))))))
                ? (IData)(__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp)
                : ((1U & (IData)((__Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_mul__DOT__q_tmp 
                                  >> 0x00000020U)))
                    ? 0x80000000U : 0x7fffffffU));
        __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext 
            = (((QData)((IData)((vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP 
                                 >> 0x0000001fU))) 
                << 0x00000020U) | (QData)((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP)));
        __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext 
            = (((QData)((IData)((vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ 
                                 >> 0x0000001fU))) 
                << 0x00000020U) | (QData)((IData)(vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ)));
        vlSelfRef.laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift 
            = (VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                          (0x00000001ffffffffULL & 
                           (VL_GTS_IQQ(33, 0ULL, __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext)
                             ? (- __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext)
                             : __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP_ext))) 
               | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                            (0x00000001ffffffffULL 
                             & (VL_GTS_IQQ(33, 0ULL, __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext)
                                 ? (- __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext)
                                 : __Vinline__stl_sequent__TOP__1_laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ_ext))));
    }
}

VL_ATTR_COLD bool Vlaminar_node_tb___024root___eval_phase__stl(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___eval_phase__stl\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vlaminar_node_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vlaminar_node_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vlaminar_node_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vlaminar_node_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vlaminar_node_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vlaminar_node_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vlaminar_node_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] laminar_node_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge laminar_node_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge laminar_node_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vlaminar_node_tb___024root___ctor_var_reset(Vlaminar_node_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vlaminar_node_tb___024root___ctor_var_reset\n"); );
    Vlaminar_node_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->laminar_node_tb__DOT__surd_out = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 17779027400857041972ull);
    vlSelf->laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 491965658490117920ull);
    vlSelf->laminar_node_tb__DOT__uut__DOT__u_norm__DOT__inQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8606366121681183219ull);
    vlSelf->laminar_node_tb__DOT__uut__DOT__u_norm__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4189904645261314035ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__laminar_node_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__laminar_node_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
