// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu_spread_mul_tb.h for the primary calling header

#include "Vspu_spread_mul_tb__pch.h"

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_static(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_static\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu_spread_mul_tb__DOT__fail = 0U;
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_static__TOP(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_static__TOP\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu_spread_mul_tb__DOT__fail = 0U;
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_initial__TOP(Vspu_spread_mul_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_initial(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_initial\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vspu_spread_mul_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_initial__TOP(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_initial__TOP\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    VlWide<4>/*127:0*/ __Vtask_spu_spread_mul_tb__DOT__check__0__label;
    VL_ZERO_W(128, __Vtask_spu_spread_mul_tb__DOT__check__0__label);
    VlWide<4>/*127:0*/ __Vtask_spu_spread_mul_tb__DOT__check__1__label;
    VL_ZERO_W(128, __Vtask_spu_spread_mul_tb__DOT__check__1__label);
    VlWide<4>/*127:0*/ __Vtask_spu_spread_mul_tb__DOT__check__2__label;
    VL_ZERO_W(128, __Vtask_spu_spread_mul_tb__DOT__check__2__label);
    VlWide<4>/*127:0*/ __Vtask_spu_spread_mul_tb__DOT__check__3__label;
    VL_ZERO_W(128, __Vtask_spu_spread_mul_tb__DOT__check__3__label);
    // Body
    __Vtask_spu_spread_mul_tb__DOT__check__0__label[0U] = 0x5f733d31U;
    __Vtask_spu_spread_mul_tb__DOT__check__0__label[1U] = 0x70657270U;
    __Vtask_spu_spread_mul_tb__DOT__check__0__label[2U] = 0U;
    __Vtask_spu_spread_mul_tb__DOT__check__0__label[3U] = 0U;
    if (VL_UNLIKELY(((((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                        >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                        ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                           - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                        : 0ULL) != vlSelfRef.spu_spread_mul_tb__DOT__spread_denom)))) {
        VL_WRITEF_NX("FAIL (case %0s): expected full spread (numer==denom), got numer=%0d denom=%0d\n",3
                     , '#',128,__Vtask_spu_spread_mul_tb__DOT__check__0__label.data()
                     , '#',64,((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL), '#',64,vlSelfRef.spu_spread_mul_tb__DOT__spread_denom);
        vlSelfRef.spu_spread_mul_tb__DOT__fail = ((IData)(1U) 
                                                  + vlSelfRef.spu_spread_mul_tb__DOT__fail);
    }
    __Vtask_spu_spread_mul_tb__DOT__check__1__label[0U] = 0x5f733d30U;
    __Vtask_spu_spread_mul_tb__DOT__check__1__label[1U] = 0x6e656172U;
    __Vtask_spu_spread_mul_tb__DOT__check__1__label[2U] = 0x6f6c6c69U;
    __Vtask_spu_spread_mul_tb__DOT__check__1__label[3U] = 0x00000063U;
    __Vtask_spu_spread_mul_tb__DOT__check__2__label[0U] = 0x6e676c65U;
    __Vtask_spu_spread_mul_tb__DOT__check__2__label[1U] = 0x69645f61U;
    __Vtask_spu_spread_mul_tb__DOT__check__2__label[2U] = 0x0000006dU;
    __Vtask_spu_spread_mul_tb__DOT__check__2__label[3U] = 0U;
    if (VL_UNLIKELY(((0ULL != ((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL))))) {
        VL_WRITEF_NX("FAIL (case %0s): expected zero spread, got numer=%0d denom=%0d\n",3
                     , '#',128,__Vtask_spu_spread_mul_tb__DOT__check__1__label.data()
                     , '#',64,((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL), '#',64,vlSelfRef.spu_spread_mul_tb__DOT__spread_denom);
        vlSelfRef.spu_spread_mul_tb__DOT__fail = ((IData)(1U) 
                                                  + vlSelfRef.spu_spread_mul_tb__DOT__fail);
    }
    if (VL_UNLIKELY((((0ULL == ((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                 >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                 ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                    - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                 : 0ULL)) | (((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                               >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                               ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                                  - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                               : 0ULL) 
                                             > vlSelfRef.spu_spread_mul_tb__DOT__spread_denom))))) {
        VL_WRITEF_NX("FAIL (case %0s): expected 0 < numer < denom, got numer=%0d denom=%0d\n",3
                     , '#',128,__Vtask_spu_spread_mul_tb__DOT__check__2__label.data()
                     , '#',64,((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL), '#',64,vlSelfRef.spu_spread_mul_tb__DOT__spread_denom);
        vlSelfRef.spu_spread_mul_tb__DOT__fail = ((IData)(1U) 
                                                  + vlSelfRef.spu_spread_mul_tb__DOT__fail);
    }
    __Vtask_spu_spread_mul_tb__DOT__check__3__label[0U] = 0x73656c66U;
    __Vtask_spu_spread_mul_tb__DOT__check__3__label[1U] = 0x656c6c5fU;
    __Vtask_spu_spread_mul_tb__DOT__check__3__label[2U] = 0x00000070U;
    __Vtask_spu_spread_mul_tb__DOT__check__3__label[3U] = 0U;
    if (VL_UNLIKELY(((0ULL != ((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL))))) {
        VL_WRITEF_NX("FAIL (case %0s): expected zero spread, got numer=%0d denom=%0d\n",3
                     , '#',128,__Vtask_spu_spread_mul_tb__DOT__check__3__label.data()
                     , '#',64,((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL), '#',64,vlSelfRef.spu_spread_mul_tb__DOT__spread_denom);
        vlSelfRef.spu_spread_mul_tb__DOT__fail = ((IData)(1U) 
                                                  + vlSelfRef.spu_spread_mul_tb__DOT__fail);
    }
    vlSelfRef.spu_spread_mul_tb__DOT__n_a = 4U;
    vlSelfRef.spu_spread_mul_tb__DOT__n_b = 0U;
    vlSelfRef.spu_spread_mul_tb__DOT__n_c = 0U;
    vlSelfRef.spu_spread_mul_tb__DOT__n_d = 0U;
    vlSelfRef.spu_spread_mul_tb__DOT__l_a = 1U;
    vlSelfRef.spu_spread_mul_tb__DOT__l_b = 4U;
    vlSelfRef.spu_spread_mul_tb__DOT__l_c = 0U;
    vlSelfRef.spu_spread_mul_tb__DOT__l_d = 0U;
    if (VL_UNLIKELY(((((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                        >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                        ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                           - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                        : 0ULL) > vlSelfRef.spu_spread_mul_tb__DOT__spread_denom)))) {
        VL_WRITEF_NX("FAIL: spread > 1 (numer=%0d > denom=%0d)\n",2
                     , '#',64,((vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                >= vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                ? (vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
                                   - vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0)
                                : 0ULL), '#',64,vlSelfRef.spu_spread_mul_tb__DOT__spread_denom);
        vlSelfRef.spu_spread_mul_tb__DOT__fail = ((IData)(1U) 
                                                  + vlSelfRef.spu_spread_mul_tb__DOT__fail);
    }
    if ((0U == vlSelfRef.spu_spread_mul_tb__DOT__fail)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL: %0d error(s)\n",1, '~',32,vlSelfRef.spu_spread_mul_tb__DOT__fail);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_spread_mul_tb.v", 140, "");
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_final(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_final\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_spread_mul_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu_spread_mul_tb___024root___eval_phase__stl(Vspu_spread_mul_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_settle(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_settle\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu_spread_mul_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_spread_mul_tb.v", 14, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu_spread_mul_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_triggers_vec__stl(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool Vspu_spread_mul_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_spread_mul_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu_spread_mul_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu_spread_mul_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___stl_sequent__TOP__0(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___stl_sequent__TOP__0\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*63:0*/ spu_spread_mul_tb__DOT__uut__DOT__dot;
    spu_spread_mul_tb__DOT__uut__DOT__dot = 0;
    // Body
    vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
        = (((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a))))) 
            + ((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b))))) 
               + ((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c))))) 
                  + (QData)((IData)((0x0000ffffU & 
                                     VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d)))))))) 
           * ((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a))))) 
              + ((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b))))) 
                 + ((QData)((IData)((0x0000ffffU & 
                                     VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c))))) 
                    + (QData)((IData)((0x0000ffffU 
                                       & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d)))))))));
    spu_spread_mul_tb__DOT__uut__DOT__dot = (VL_MULS_QQQ(64, 
                                                         (((- (QData)((IData)(
                                                                              (1U 
                                                                               & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a) 
                                                                                >> 0x0000000fU))))) 
                                                           << 0x00000010U) 
                                                          | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a))), 
                                                         (((- (QData)((IData)(
                                                                              (1U 
                                                                               & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a) 
                                                                                >> 0x0000000fU))))) 
                                                           << 0x00000010U) 
                                                          | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a)))) 
                                             + (VL_MULS_QQQ(64, 
                                                            (((- (QData)((IData)(
                                                                                (1U 
                                                                                & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b) 
                                                                                >> 0x0000000fU))))) 
                                                              << 0x00000010U) 
                                                             | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b))), 
                                                            (((- (QData)((IData)(
                                                                                (1U 
                                                                                & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b) 
                                                                                >> 0x0000000fU))))) 
                                                              << 0x00000010U) 
                                                             | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b)))) 
                                                + (
                                                   VL_MULS_QQQ(64, 
                                                               (((- (QData)((IData)(
                                                                                (1U 
                                                                                & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c) 
                                                                                >> 0x0000000fU))))) 
                                                                 << 0x00000010U) 
                                                                | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c))), 
                                                               (((- (QData)((IData)(
                                                                                (1U 
                                                                                & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c) 
                                                                                >> 0x0000000fU))))) 
                                                                 << 0x00000010U) 
                                                                | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c)))) 
                                                   + 
                                                   VL_MULS_QQQ(64, 
                                                               (((- (QData)((IData)(
                                                                                (1U 
                                                                                & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d) 
                                                                                >> 0x0000000fU))))) 
                                                                 << 0x00000010U) 
                                                                | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d))), 
                                                               (((- (QData)((IData)(
                                                                                (1U 
                                                                                & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d) 
                                                                                >> 0x0000000fU))))) 
                                                                 << 0x00000010U) 
                                                                | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d)))))));
    vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0 
        = VL_SHIFTL_QQI(64,64,32, VL_MULS_QQQ(64, spu_spread_mul_tb__DOT__uut__DOT__dot, spu_spread_mul_tb__DOT__uut__DOT__dot), 2U);
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___eval_stl(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_stl\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*63:0*/ __Vinline__stl_sequent__TOP__0_spu_spread_mul_tb__DOT__uut__DOT__dot;
    __Vinline__stl_sequent__TOP__0_spu_spread_mul_tb__DOT__uut__DOT__dot = 0;
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu_spread_mul_tb__DOT__spread_denom 
            = (((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a))))) 
                + ((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b))))) 
                   + ((QData)((IData)((0x0000ffffU 
                                       & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c))))) 
                      + (QData)((IData)((0x0000ffffU 
                                         & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d)))))))) 
               * ((QData)((IData)((0x0000ffffU & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a))))) 
                  + ((QData)((IData)((0x0000ffffU & 
                                      VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b))))) 
                     + ((QData)((IData)((0x0000ffffU 
                                         & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c))))) 
                        + (QData)((IData)((0x0000ffffU 
                                           & VL_MULS_III(16, (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d), (IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d)))))))));
        __Vinline__stl_sequent__TOP__0_spu_spread_mul_tb__DOT__uut__DOT__dot 
            = (VL_MULS_QQQ(64, (((- (QData)((IData)(
                                                    (1U 
                                                     & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a) 
                                                        >> 0x0000000fU))))) 
                                 << 0x00000010U) | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_a))), 
                           (((- (QData)((IData)((1U 
                                                 & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a) 
                                                    >> 0x0000000fU))))) 
                             << 0x00000010U) | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_a)))) 
               + (VL_MULS_QQQ(64, (((- (QData)((IData)(
                                                       (1U 
                                                        & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b) 
                                                           >> 0x0000000fU))))) 
                                    << 0x00000010U) 
                                   | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_b))), 
                              (((- (QData)((IData)(
                                                   (1U 
                                                    & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b) 
                                                       >> 0x0000000fU))))) 
                                << 0x00000010U) | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_b)))) 
                  + (VL_MULS_QQQ(64, (((- (QData)((IData)(
                                                          (1U 
                                                           & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c) 
                                                              >> 0x0000000fU))))) 
                                       << 0x00000010U) 
                                      | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_c))), 
                                 (((- (QData)((IData)(
                                                      (1U 
                                                       & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c) 
                                                          >> 0x0000000fU))))) 
                                   << 0x00000010U) 
                                  | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_c)))) 
                     + VL_MULS_QQQ(64, (((- (QData)((IData)(
                                                            (1U 
                                                             & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d) 
                                                                >> 0x0000000fU))))) 
                                         << 0x00000010U) 
                                        | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__n_d))), 
                                   (((- (QData)((IData)(
                                                        (1U 
                                                         & ((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d) 
                                                            >> 0x0000000fU))))) 
                                     << 0x00000010U) 
                                    | (QData)((IData)(vlSelfRef.spu_spread_mul_tb__DOT__l_d)))))));
        vlSelfRef.spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0 
            = VL_SHIFTL_QQI(64,64,32, VL_MULS_QQQ(64, __Vinline__stl_sequent__TOP__0_spu_spread_mul_tb__DOT__uut__DOT__dot, __Vinline__stl_sequent__TOP__0_spu_spread_mul_tb__DOT__uut__DOT__dot), 2U);
    }
}

VL_ATTR_COLD bool Vspu_spread_mul_tb___024root___eval_phase__stl(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___eval_phase__stl\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu_spread_mul_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu_spread_mul_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu_spread_mul_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu_spread_mul_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vspu_spread_mul_tb___024root___ctor_var_reset(Vspu_spread_mul_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spread_mul_tb___024root___ctor_var_reset\n"); );
    Vspu_spread_mul_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->spu_spread_mul_tb__DOT__n_a = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12324721307869177170ull);
    vlSelf->spu_spread_mul_tb__DOT__n_b = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4809871275526654098ull);
    vlSelf->spu_spread_mul_tb__DOT__n_c = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15320800882630408674ull);
    vlSelf->spu_spread_mul_tb__DOT__n_d = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7805950850287841794ull);
    vlSelf->spu_spread_mul_tb__DOT__l_a = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 17871850509119436907ull);
    vlSelf->spu_spread_mul_tb__DOT__l_b = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16843078062745998353ull);
    vlSelf->spu_spread_mul_tb__DOT__l_c = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5195233723726813951ull);
    vlSelf->spu_spread_mul_tb__DOT__l_d = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 2962867149482499237ull);
    vlSelf->spu_spread_mul_tb__DOT__spread_denom = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 5064691279662108219ull);
    vlSelf->spu_spread_mul_tb__DOT__uut__DOT____VdfgRegularize_h83e7d37b_0_0 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
}
