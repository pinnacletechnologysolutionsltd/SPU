// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrational_surd5_scale_manager_tb.h for the primary calling header

#include "Vrational_surd5_scale_manager_tb__pch.h"

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_static(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_static\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__clk = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__rst_n = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_en = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_idx = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_shift = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_overflow = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__clk__0 = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__rst_n__0 = 0U;
}

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_static__TOP(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_static__TOP\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__clk = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__rst_n = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_en = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_idx = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_shift = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_overflow = 0U;
}

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_initial__TOP(Vrational_surd5_scale_manager_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_initial(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_initial\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vrational_surd5_scale_manager_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_initial__TOP(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_initial__TOP\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ rational_surd5_scale_manager_tb__DOT__errors;
    rational_surd5_scale_manager_tb__DOT__errors = 0;
    // Body
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__rst_n = 1U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_idx = 0x0cU;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_shift = 0x0cU;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_overflow = 0U;
    vlSelfRef.rational_surd5_scale_manager_tb__DOT__write_en = 0U;
    rational_surd5_scale_manager_tb__DOT__errors = 0U;
    if (VL_UNLIKELY(((0U != (0x0000000fU & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table)))))) {
        VL_WRITEF_NX("ERR shift idx 0: got %0d expected 0\n",1
                     , '#',4,(0x0000000fU & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 0: got %0d expected 0\n",1
                     , '#',1,(1U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 4U))))))) {
        VL_WRITEF_NX("ERR shift idx 1: got %0d expected 1\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 4U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (~ ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                               >> 1U)))))) {
        VL_WRITEF_NX("ERR overflow idx 1: got %0d expected 1\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 1U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((2U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 8U))))))) {
        VL_WRITEF_NX("ERR shift idx 2: got %0d expected 2\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 8U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((4U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 2: got %0d expected 0\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 2U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((3U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x0cU))))))) {
        VL_WRITEF_NX("ERR shift idx 3: got %0d expected 3\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x0cU))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (~ ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                               >> 3U)))))) {
        VL_WRITEF_NX("ERR overflow idx 3: got %0d expected 1\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 3U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((4U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x10U))))))) {
        VL_WRITEF_NX("ERR shift idx 4: got %0d expected 4\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x10U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x00000010U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 4: got %0d expected 0\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 4U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((5U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x14U))))))) {
        VL_WRITEF_NX("ERR shift idx 5: got %0d expected 5\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x14U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (~ ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                               >> 5U)))))) {
        VL_WRITEF_NX("ERR overflow idx 5: got %0d expected 1\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 5U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((6U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x18U))))))) {
        VL_WRITEF_NX("ERR shift idx 6: got %0d expected 6\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x18U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x00000040U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 6: got %0d expected 0\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 6U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((7U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x1cU))))))) {
        VL_WRITEF_NX("ERR shift idx 7: got %0d expected 7\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x1cU))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (~ ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                               >> 7U)))))) {
        VL_WRITEF_NX("ERR overflow idx 7: got %0d expected 1\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 7U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((8U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x20U))))))) {
        VL_WRITEF_NX("ERR shift idx 8: got %0d expected 8\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x20U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x00000100U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 8: got %0d expected 0\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 8U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((9U != (0x0000000fU & (IData)(
                                                   (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                    >> 0x24U))))))) {
        VL_WRITEF_NX("ERR shift idx 9: got %0d expected 9\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x24U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (~ ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                               >> 9U)))))) {
        VL_WRITEF_NX("ERR overflow idx 9: got %0d expected 1\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 9U)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x0aU != (0x0000000fU & (IData)(
                                                      (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                       >> 0x28U))))))) {
        VL_WRITEF_NX("ERR shift idx 10: got %0d expected 10\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x28U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x00000400U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 10: got %0d expected 0\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 0x0aU)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x0bU != (0x0000000fU & (IData)(
                                                      (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                       >> 0x2cU))))))) {
        VL_WRITEF_NX("ERR shift idx 11: got %0d expected 11\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x2cU))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((1U & (~ ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                               >> 0x0bU)))))) {
        VL_WRITEF_NX("ERR overflow idx 11: got %0d expected 1\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 0x0bU)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x0cU != (0x0000000fU & (IData)(
                                                      (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                       >> 0x30U))))))) {
        VL_WRITEF_NX("ERR shift idx 12: got %0d expected 12\n",1
                     , '#',4,(0x0000000fU & (IData)(
                                                    (vlSelfRef.rational_surd5_scale_manager_tb__DOT__scale_table 
                                                     >> 0x30U))));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if (VL_UNLIKELY(((0x00001000U & (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table))))) {
        VL_WRITEF_NX("ERR overflow idx 12: got %0d expected 0\n",1
                     , '#',1,(1U & ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__overflow_table) 
                                    >> 0x0cU)));
        rational_surd5_scale_manager_tb__DOT__errors 
            = ((IData)(1U) + rational_surd5_scale_manager_tb__DOT__errors);
    }
    if ((0U == rational_surd5_scale_manager_tb__DOT__errors)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL: %0d errors\n",1, '~',32,rational_surd5_scale_manager_tb__DOT__errors);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_surd5_scale_manager_tb.v", 63, "");
}

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_final(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_final\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vrational_surd5_scale_manager_tb___024root___eval_phase__stl(Vrational_surd5_scale_manager_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_settle(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_settle\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vrational_surd5_scale_manager_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_surd5_scale_manager_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vrational_surd5_scale_manager_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_triggers_vec__stl(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_triggers_vec__stl\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__clk__0 
        = vlSelfRef.rational_surd5_scale_manager_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vrational_surd5_scale_manager_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vrational_surd5_scale_manager_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] rational_surd5_scale_manager_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vrational_surd5_scale_manager_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___eval_stl(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_stl\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.rational_surd5_scale_manager_tb__DOT__clk 
            = (1U & (~ (IData)(vlSelfRef.rational_surd5_scale_manager_tb__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vrational_surd5_scale_manager_tb___024root___eval_phase__stl(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___eval_phase__stl\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vrational_surd5_scale_manager_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vrational_surd5_scale_manager_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vrational_surd5_scale_manager_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vrational_surd5_scale_manager_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vrational_surd5_scale_manager_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vrational_surd5_scale_manager_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] rational_surd5_scale_manager_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge rational_surd5_scale_manager_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge rational_surd5_scale_manager_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vrational_surd5_scale_manager_tb___024root___ctor_var_reset(Vrational_surd5_scale_manager_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_surd5_scale_manager_tb___024root___ctor_var_reset\n"); );
    Vrational_surd5_scale_manager_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->rational_surd5_scale_manager_tb__DOT__scale_table = VL_SCOPED_RAND_RESET_Q(52, __VscopeHash, 7790290977293010109ull);
    vlSelf->rational_surd5_scale_manager_tb__DOT__overflow_table = VL_SCOPED_RAND_RESET_I(13, __VscopeHash, 15107905881874322781ull);
    vlSelf->rational_surd5_scale_manager_tb__DOT__uut__DOT____Vlvbound_h95ca7be9__0 = 0;
    vlSelf->rational_surd5_scale_manager_tb__DOT__uut__DOT____Vlvbound_h161fecb4__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__rational_surd5_scale_manager_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
