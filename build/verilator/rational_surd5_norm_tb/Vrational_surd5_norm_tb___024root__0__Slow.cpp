// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrational_surd5_norm_tb.h for the primary calling header

#include "Vrational_surd5_norm_tb__pch.h"

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_static(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_static\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_initial__TOP(Vrational_surd5_norm_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_initial(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_initial\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vrational_surd5_norm_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_initial__TOP(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_initial__TOP\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((((0x0000000a00000014ULL == (((QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP)) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ)))) 
          & (~ (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift))) 
         & (~ ((VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                           (0x00000001ffffffffULL & 
                            (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                              ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                              : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext))) 
                | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                             (0x00000001ffffffffULL 
                              & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                  ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                  : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)))) 
               & (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift))))) {
        VL_WRITEF_NX("PASS case1\n",0);
    } else {
        VL_WRITEF_NX("FAIL case1: out=%h shift=%d of=%b\n",3
                     , '#',64,(((QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP)) 
                                << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ)))
                     , '#',4,(IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift)
                     , '#',1,((VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                                          (0x00000001ffffffffULL 
                                           & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                               ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                               : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext))) 
                               | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                                            (0x00000001ffffffffULL 
                                             & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                 ? 
                                                (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                 : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)))) 
                              & (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift)));
    }
    if (((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift) 
         & (~ ((VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                           (0x00000001ffffffffULL & 
                            (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                              ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                              : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext))) 
                | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                             (0x00000001ffffffffULL 
                              & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                  ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                  : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)))) 
               & (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift))))) {
        VL_WRITEF_NX("PASS case2 (shift)\n",0);
    } else {
        VL_WRITEF_NX("FAIL case2: out=%h shift=%d of=%b\n",3
                     , '#',64,(((QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP)) 
                                << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ)))
                     , '#',4,(IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift)
                     , '#',1,((VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                                          (0x00000001ffffffffULL 
                                           & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                               ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                               : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext))) 
                               | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                                            (0x00000001ffffffffULL 
                                             & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                 ? 
                                                (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                 : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)))) 
                              & (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift)));
    }
    vlSelfRef.rational_surd5_norm_tb__DOT__in_val = 0x8000000080000000ULL;
    if (((VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                 & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                                     ? 
                                                    (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                                     : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext))) 
          | VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                   & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                       ? 
                                                      (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                       : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)))) 
         & (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift))) {
        VL_WRITEF_NX("PASS case3 (overflow)\n",0);
    } else {
        VL_WRITEF_NX("FAIL case3: out=%h shift=%d of=%b\n",3
                     , '#',64,(((QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP)) 
                                << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ)))
                     , '#',4,(IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift)
                     , '#',1,((VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                                          (0x00000001ffffffffULL 
                                           & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                               ? (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext)
                                               : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext))) 
                               | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                                            (0x00000001ffffffffULL 
                                             & (VL_GTS_IQQ(33, 0ULL, vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                 ? 
                                                (- vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)
                                                 : vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext)))) 
                              & (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift)));
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_surd5_norm_tb.v", 28, "");
}

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_final(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_final\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vrational_surd5_norm_tb___024root___eval_phase__stl(Vrational_surd5_norm_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_settle(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_settle\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vrational_surd5_norm_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_surd5_norm_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vrational_surd5_norm_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_triggers_vec__stl(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_triggers_vec__stl\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool Vrational_surd5_norm_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vrational_surd5_norm_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vrational_surd5_norm_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___stl_sequent__TOP__0(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___stl_sequent__TOP__0\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*32:0*/ rational_surd5_norm_tb__DOT__uut__DOT__inP_ext;
    rational_surd5_norm_tb__DOT__uut__DOT__inP_ext = 0;
    QData/*32:0*/ rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext;
    rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext = 0;
    // Body
    rational_surd5_norm_tb__DOT__uut__DOT__inP_ext 
        = (((QData)((IData)((1U & (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                           >> 0x0000003fU))))) 
            << 0x00000020U) | (QData)((IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                               >> 0x00000020U))));
    rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext 
        = (((QData)((IData)((1U & (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                           >> 0x0000001fU))))) 
            << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__in_val)));
    vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift 
        = (VL_LTS_IQQ(33, 0x000000003fffffffULL, (0x00000001ffffffffULL 
                                                  & (VL_GTS_IQQ(33, 0ULL, rational_surd5_norm_tb__DOT__uut__DOT__inP_ext)
                                                      ? 
                                                     (- rational_surd5_norm_tb__DOT__uut__DOT__inP_ext)
                                                      : rational_surd5_norm_tb__DOT__uut__DOT__inP_ext))) 
           | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                        (0x00000001ffffffffULL & (VL_GTS_IQQ(33, 0ULL, rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext)
                                                   ? 
                                                  (- rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext)
                                                   : rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext))));
    if (vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift) {
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP 
            = VL_SHIFTRS_III(32,32,32, (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                                >> 0x00000020U)), 1U);
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ 
            = VL_SHIFTRS_III(32,32,32, (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__in_val), 1U);
    } else {
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP 
            = (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                       >> 0x00000020U));
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ 
            = (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__in_val);
    }
    vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext 
        = (((QData)((IData)((vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP)));
    vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext 
        = (((QData)((IData)((vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ 
                             >> 0x0000001fU))) << 0x00000020U) 
           | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ)));
}

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___eval_stl(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_stl\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*32:0*/ __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inP_ext;
    __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inP_ext = 0;
    QData/*32:0*/ __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext;
    __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext = 0;
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inP_ext 
            = (((QData)((IData)((1U & (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                               >> 0x0000003fU))))) 
                << 0x00000020U) | (QData)((IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                                   >> 0x00000020U))));
        __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext 
            = (((QData)((IData)((1U & (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                               >> 0x0000001fU))))) 
                << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__in_val)));
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift 
            = (VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                          (0x00000001ffffffffULL & 
                           (VL_GTS_IQQ(33, 0ULL, __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inP_ext)
                             ? (- __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inP_ext)
                             : __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inP_ext))) 
               | VL_LTS_IQQ(33, 0x000000003fffffffULL, 
                            (0x00000001ffffffffULL 
                             & (VL_GTS_IQQ(33, 0ULL, __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext)
                                 ? (- __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext)
                                 : __Vinline__stl_sequent__TOP__0_rational_surd5_norm_tb__DOT__uut__DOT__inQ_ext))));
        if (vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__need_shift) {
            vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP 
                = VL_SHIFTRS_III(32,32,32, (IData)(
                                                   (vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                                                    >> 0x00000020U)), 1U);
            vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ 
                = VL_SHIFTRS_III(32,32,32, (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__in_val), 1U);
        } else {
            vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP 
                = (IData)((vlSelfRef.rational_surd5_norm_tb__DOT__in_val 
                           >> 0x00000020U));
            vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ 
                = (IData)(vlSelfRef.rational_surd5_norm_tb__DOT__in_val);
        }
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP_ext 
            = (((QData)((IData)((vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP 
                                 >> 0x0000001fU))) 
                << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sP)));
        vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext 
            = (((QData)((IData)((vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ 
                                 >> 0x0000001fU))) 
                << 0x00000020U) | (QData)((IData)(vlSelfRef.rational_surd5_norm_tb__DOT__uut__DOT__sQ)));
    }
}

VL_ATTR_COLD bool Vrational_surd5_norm_tb___024root___eval_phase__stl(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___eval_phase__stl\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vrational_surd5_norm_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vrational_surd5_norm_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vrational_surd5_norm_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vrational_surd5_norm_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vrational_surd5_norm_tb___024root___ctor_var_reset(Vrational_surd5_norm_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_norm_tb___024root___ctor_var_reset\n"); );
    Vrational_surd5_norm_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->rational_surd5_norm_tb__DOT__in_val = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 12465455610078138529ull);
    vlSelf->rational_surd5_norm_tb__DOT__uut__DOT__need_shift = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12200121036004715628ull);
    vlSelf->rational_surd5_norm_tb__DOT__uut__DOT__sP = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7607182640852783821ull);
    vlSelf->rational_surd5_norm_tb__DOT__uut__DOT__sQ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11256021978098452743ull);
    vlSelf->rational_surd5_norm_tb__DOT__uut__DOT__sP_ext = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 15691327926507176527ull);
    vlSelf->rational_surd5_norm_tb__DOT__uut__DOT__sQ_ext = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 16234097388422278019ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
}
