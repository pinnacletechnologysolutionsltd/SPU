// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu4_precession_tb.h for the primary calling header

#include "Vspu4_precession_tb__pch.h"

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_static(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_static\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0 
        = vlSelfRef.spu4_precession_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__rst_n__0 
        = vlSelfRef.spu4_precession_tb__DOT__rst_n;
}

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_initial(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_initial\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i;
    __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i = 0;
    // Body
    __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000400U, __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i)) {
        vlSelfRef.spu4_precession_tb__DOT__prog_mem[(0x000003ffU 
                                                     & __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i)] = 0U;
        __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i 
            = ((IData)(1U) + __Vinline__eval_initial__TOP_spu4_precession_tb__DOT__i);
    }
    VL_READMEM_N(true, 24, 1024, 0, "hardware/spu4/tests/precession.hex"s
                 ,  &(vlSelfRef.spu4_precession_tb__DOT__prog_mem)
                 , 0, ~0ULL);
    vlSymsp->_vm_contextp__->dumpfile("precession_trace.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v:42: $dumpvar ignored, as Verilated without --trace\n");
    vlSelfRef.spu4_precession_tb__DOT__clk = 0U;
    vlSelfRef.spu4_precession_tb__DOT__rst_n = 1U;
    VL_WRITEF_NX("--- SPU-4 Precession Test Start ---\nR0 State Final: %h\nSnap Alert (Latch): %b, Whisper Tx (Latch): 0\nFAIL: Precession Kernel did not reach Whisper Tx.\n",2
                 , '#',64,(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rplu_data 
                           ^ vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[0U])
                 , '#',1,(0x80U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3)));
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v", 64, "");
}

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_initial__TOP(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_initial__TOP\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ spu4_precession_tb__DOT__i;
    spu4_precession_tb__DOT__i = 0;
    // Body
    spu4_precession_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000400U, spu4_precession_tb__DOT__i)) {
        vlSelfRef.spu4_precession_tb__DOT__prog_mem[(0x000003ffU 
                                                     & spu4_precession_tb__DOT__i)] = 0U;
        spu4_precession_tb__DOT__i = ((IData)(1U) + spu4_precession_tb__DOT__i);
    }
    VL_READMEM_N(true, 24, 1024, 0, "hardware/spu4/tests/precession.hex"s
                 ,  &(vlSelfRef.spu4_precession_tb__DOT__prog_mem)
                 , 0, ~0ULL);
    vlSymsp->_vm_contextp__->dumpfile("precession_trace.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v:42: $dumpvar ignored, as Verilated without --trace\n");
    vlSelfRef.spu4_precession_tb__DOT__clk = 0U;
    vlSelfRef.spu4_precession_tb__DOT__rst_n = 1U;
    VL_WRITEF_NX("--- SPU-4 Precession Test Start ---\nR0 State Final: %h\nSnap Alert (Latch): %b, Whisper Tx (Latch): 0\nFAIL: Precession Kernel did not reach Whisper Tx.\n",2
                 , '#',64,(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rplu_data 
                           ^ vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[0U])
                 , '#',1,(0x80U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3)));
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v", 64, "");
}

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_final(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_final\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_precession_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu4_precession_tb___024root___eval_phase__stl(Vspu4_precession_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_settle(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_settle\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu4_precession_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v", 3, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu4_precession_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_triggers_vec__stl(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.spu4_precession_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0 
        = vlSelfRef.spu4_precession_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vspu4_precession_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_precession_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu4_precession_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu4_precession_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu4_precession_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___trigger_anySet__stl\n"); );
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

extern const VlUnpacked<CData/*1:0*/, 128> Vspu4_precession_tb__ConstPool__TABLE_hdc210f6a_0;

VL_ATTR_COLD void Vspu4_precession_tb___024root___stl_sequent__TOP__1(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___stl_sequent__TOP__1\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*6:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    // Body
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum 
        = (0x0003ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                          + (0x0000ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                            >> 8U))));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3 = (0x000000ffU 
                                                & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                                                   [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                                                   >> 0x00000010U));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2 = (7U 
                                                & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                                                   [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                                                   >> 8U));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op 
        = ((1U & (- (IData)((0x10U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
           | ((2U & (- (IData)((0x40U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
              | (3U & (- (IData)((0x45U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3)))))));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__0__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (0U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__1__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (1U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__2__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (2U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__3__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (3U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__4__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (4U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__5__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (5U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__6__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (6U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__7__KET__ 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
           & (7U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_0 = (0x0000ffffU 
                                                & (IData)(
                                                          (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                                           [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2] 
                                                           >> 0x00000030U)));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_1 = (0x0000ffffU 
                                                & (IData)(
                                                          (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                                           [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2] 
                                                           >> 0x00000020U)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state_we 
        = (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done) 
            & (2U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))) 
           | ((3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
              & (1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))));
    __Vtableidx1 = ((((((1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)) 
                        << 3U) | ((3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                                  << 2U)) | (((3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                                              << 1U) 
                                             | (2U 
                                                == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)))) 
                     << 3U) | (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done) 
                                << 2U) | (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__next_state 
        = Vspu4_precession_tb__ConstPool__TABLE_hdc210f6a_0
        [__Vtableidx1];
}

VL_ATTR_COLD void Vspu4_precession_tb___024root___eval_stl(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_stl\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*6:0*/ __Vinline__stl_sequent__TOP__1___Vtableidx1;
    __Vinline__stl_sequent__TOP__1___Vtableidx1 = 0;
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu4_precession_tb__DOT__clk = (1U 
                                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__clk)));
    }
    if ((1ULL & vlSelfRef.__VstlTriggered[1U])) {
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum 
            = (0x0003ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                              + (0x0000ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                                >> 8U))));
        vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3 = 
            (0x000000ffU & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                            [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                            >> 0x00000010U));
        vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2 = 
            (7U & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                   [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                   >> 8U));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op 
            = ((1U & (- (IData)((0x10U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
               | ((2U & (- (IData)((0x40U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
                  | (3U & (- (IData)((0x45U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3)))))));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__0__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (0U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__1__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (1U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__2__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (2U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__3__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (3U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__4__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (4U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__5__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (5U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__6__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (6U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__7__KET__ 
            = ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we) 
               & (7U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2)));
        vlSelfRef.__VdfgRegularize_h6e95ff9d_0_0 = 
            (0x0000ffffU & (IData)((vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                    [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2] 
                                    >> 0x00000030U)));
        vlSelfRef.__VdfgRegularize_h6e95ff9d_0_1 = 
            (0x0000ffffU & (IData)((vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                    [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2] 
                                    >> 0x00000020U)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state_we 
            = (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done) 
                & (2U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))) 
               | ((3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                  & (1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))));
        __Vinline__stl_sequent__TOP__1___Vtableidx1 
            = ((((((1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)) 
                   << 3U) | ((3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                             << 2U)) | (((3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                                         << 1U) | (2U 
                                                   == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)))) 
                << 3U) | (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done) 
                           << 2U) | (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__next_state 
            = Vspu4_precession_tb__ConstPool__TABLE_hdc210f6a_0
            [__Vinline__stl_sequent__TOP__1___Vtableidx1];
    }
}

VL_ATTR_COLD bool Vspu4_precession_tb___024root___eval_phase__stl(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_phase__stl\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu4_precession_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu4_precession_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu4_precession_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu4_precession_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vspu4_precession_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_precession_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu4_precession_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu4_precession_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge spu4_precession_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge spu4_precession_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vspu4_precession_tb___024root___ctor_var_reset(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___ctor_var_reset\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->spu4_precession_tb__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1676493911920469961ull);
    vlSelf->spu4_precession_tb__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2753941925981920784ull);
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->spu4_precession_tb__DOT__prog_mem[__Vi0] = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 2053020086388047574ull);
    }
    vlSelf->spu4_precession_tb__DOT__uut__DOT__pc_reg = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 9301687973538268192ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__alu_op = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 15250512839465014707ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__rot_a = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13540998035619144215ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__rot_b = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5296619915741750283ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__rot_c = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3630520263512213656ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__rot_d = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4976373922550872827ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__rot_done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6400942054982384604ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 7524864942737178310ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__next_state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 3731456551561799848ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__state_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15841308758539416465ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__core_din = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 9945412547967305647ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__core_we = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5300891010875845770ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__core_rot_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10899396947877347744ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__rplu_data = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 18172737441162113717ull);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[__Vi0] = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 707321496817904206ull);
    }
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__7__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16367409354392807154ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__6__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2101285364485198033ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__5__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6025586793403542584ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__4__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14210000250521914802ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__3__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3497140344739625051ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__2__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15562096980232343152ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__1__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8473105151352128776ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__0__KET__ = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1387851342262719040ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mode_autonomous = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5973518601067490266ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4385393290111251696ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11373124771467026993ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9451362404205275682ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 619165176439621075ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11902265457657014375ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 10992920741589443336ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum = VL_SCOPED_RAND_RESET_I(18, __VscopeHash, 12048691072672115030ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7538438307902419547ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14240663934912698239ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11361682292761781921ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 7231208487042541929ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum = VL_SCOPED_RAND_RESET_I(18, __VscopeHash, 2441949852590919155ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6343624005063305144ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4058196258784530304ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 5475758767562325747ull);
    vlSelf->spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1446664243376771586ull);
    vlSelf->__VdfgRegularize_h6e95ff9d_0_0 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_1 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_2 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_3 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0 = 0;
    vlSelf->__VdlySet__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v1 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v2 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v3 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v4 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v5 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v6 = 0;
    vlSelf->__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v7 = 0;
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
