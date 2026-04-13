// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu4_precession_tb.h for the primary calling header

#include "Vspu4_precession_tb__pch.h"

void Vspu4_precession_tb___024root___eval_triggers_vec__act(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_triggers_vec__act\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((~ (IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__rst_n__0)) 
                                                      << 2U) 
                                                     | ((((IData)(vlSelfRef.spu4_precession_tb__DOT__clk) 
                                                          & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0))) 
                                                         << 1U) 
                                                        | ((IData)(vlSelfRef.spu4_precession_tb__DOT__clk) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0 
        = vlSelfRef.spu4_precession_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_precession_tb__DOT__rst_n__0 
        = vlSelfRef.spu4_precession_tb__DOT__rst_n;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VactDidInit)))))) {
        vlSelfRef.__VactDidInit = 1U;
        vlSelfRef.__VactTriggered[0U] = (1ULL | vlSelfRef.__VactTriggered[0U]);
    }
}

bool Vspu4_precession_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___trigger_anySet__act\n"); );
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

void Vspu4_precession_tb___024root___act_sequent__TOP__0(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___act_sequent__TOP__0\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu4_precession_tb__DOT__clk = (1U & 
                                              (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__clk)));
}

void Vspu4_precession_tb___024root___eval_act(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_act\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VactTriggered[0U])) {
        vlSelfRef.spu4_precession_tb__DOT__clk = (1U 
                                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__clk)));
    }
}

void Vspu4_precession_tb___024root___nba_sequent__TOP__0(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___nba_sequent__TOP__0\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    SData/*9:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__pc_reg;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__pc_reg = 0;
    // Body
    __Vdly__spu4_precession_tb__DOT__uut__DOT__pc_reg 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg;
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0 
        = (((0x0100000000000000ULL & (- (QData)((IData)(
                                                        (1U 
                                                         & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n))))))) 
            | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                   & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__0__KET__))))) 
               & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din)) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__0__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[0U]));
    vlSelfRef.__VdlySet__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0 = 1U;
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v1 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__1__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__1__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[1U]));
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v2 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__2__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__2__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[2U]));
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v3 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__3__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__3__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[3U]));
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v4 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__4__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__4__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[4U]));
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v5 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__5__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__5__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[5U]));
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v6 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__6__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__6__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[6U]));
    vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v7 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__7__KET__))))) 
            & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__7__KET__)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[7U]));
    __Vdly__spu4_precession_tb__DOT__uut__DOT__pc_reg 
        = (0x000003ffU & (((- (IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                       & (3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))))) 
                           & ((IData)(1U) + (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg))) 
                          | ((- (IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                         & (3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))))) 
                             & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg))));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din 
        = (((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state_we))))) 
            & (((- (QData)((IData)((1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op))))) 
                & ((QData)((IData)((0x000000ffU & vlSelfRef.spu4_precession_tb__DOT__prog_mem
                                    [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg]))) 
                   << 0x00000030U)) | (((- (QData)((IData)(
                                                           (2U 
                                                            == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))))) 
                                        & (((QData)((IData)(
                                                            (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_a) 
                                                              << 0x00000010U) 
                                                             | (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_b)))) 
                                            << 0x00000020U) 
                                           | (QData)((IData)(
                                                             (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_c) 
                                                               << 0x00000010U) 
                                                              | (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_d)))))) 
                                       | ((vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                           [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2] 
                                           + vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                           [(7U & vlSelfRef.spu4_precession_tb__DOT__prog_mem
                                             [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg])]) 
                                          & (- (QData)((IData)(
                                                               (2U 
                                                                == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op))))))))) 
           | ((- (QData)((IData)(((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                                  & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state_we)))))) 
              & vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_din));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rplu_data = 0ULL;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_we 
        = ((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
           & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state_we));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__pc_reg;
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3 = (0x000000ffU 
                                                & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                                                   [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                                                   >> 0x00000010U));
}

void Vspu4_precession_tb___024root___nba_sequent__TOP__1(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___nba_sequent__TOP__1\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__0__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__0__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__Vfuncout = 0;
    IData/*17:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__Vfuncout = 0;
    IData/*17:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val = 0;
    SData/*15:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__Vfuncout;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__Vfuncout = 0;
    IData/*17:0*/ __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val;
    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val = 0;
    SData/*15:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s = 0;
    SData/*15:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s = 0;
    SData/*15:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s = 0;
    CData/*3:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 0;
    CData/*3:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 0;
    IData/*17:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum = 0;
    IData/*31:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted = 0;
    SData/*15:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg = 0;
    IData/*31:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod = 0;
    CData/*4:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count = 0;
    CData/*0:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy = 0;
    CData/*0:0*/ __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done = 0;
    // Body
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done;
    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod;
    if (vlSelfRef.spu4_precession_tb__DOT__rst_n) {
        if (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start) 
             & (~ (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy)))) {
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted 
                = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a;
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg 
                = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b;
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod = 0U;
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count = 0x10U;
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy = 1U;
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done = 0U;
        } else if (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy) {
            if ((0U < (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count))) {
                if ((1U & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg))) {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                        = (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                           + vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted);
                }
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count 
                    = (0x0000001fU & ((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count) 
                                      - (IData)(1U)));
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted 
                    = VL_SHIFTL_III(32,32,32, vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted, 1U);
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg 
                    = VL_SHIFTR_III(16,16,32, (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg), 1U);
            } else {
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done = 1U;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy = 0U;
            }
        } else {
            __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done = 0U;
        }
        if ((0U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state))) {
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done = 0U;
            if (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_rot_start) {
                if (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mode_autonomous) {
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__0__val 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_a;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__val 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_b;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__val 
                        = (0x0000ffffU & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_c));
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__val 
                        = (0x0000ffffU & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_d));
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__val 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_b;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__val 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_a;
                } else {
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__0__val 
                        = vlSelfRef.__VdfgRegularize_h6e95ff9d_0_0;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__val 
                        = vlSelfRef.__VdfgRegularize_h6e95ff9d_0_1;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__val 
                        = (0x0000ffffU & (IData)((vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                                  [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2] 
                                                  >> 0x00000010U)));
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__val 
                        = (0x0000ffffU & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf
                                                 [vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2]));
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__val 
                        = vlSelfRef.__VdfgRegularize_h6e95ff9d_0_1;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__val 
                        = vlSelfRef.__VdfgRegularize_h6e95ff9d_0_0;
                }
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__Vfuncout 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__val;
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__Vfuncout 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__val;
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__Vfuncout 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__val;
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__Vfuncout 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__val;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__1__Vfuncout;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__2__Vfuncout;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__3__Vfuncout;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 0U;
                vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__5__Vfuncout;
                vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x00ccU;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__Vfuncout 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__val;
                vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_a 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__scale_flow__4__Vfuncout;
            }
        } else if ((1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state))) {
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 0U;
            if (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done) {
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state))) {
            if (((((((((0U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state)) 
                       | (1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) 
                      | (2U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) 
                     | (3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) 
                    | (4U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) 
                   | (5U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) 
                  | (6U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) 
                 | (7U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state)))) {
                if ((0U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                        = (0x0000ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                          >> 8U));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x0019U;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else if ((1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                        = (0x0003ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                                          + (0x0000ffffU 
                                             & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                                >> 8U))));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x0019U;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 2U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else if ((2U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__Vfuncout 
                        = (0x0000ffffU & ((0x00020000U 
                                           & __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val)
                                           ? (__Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val 
                                              >> 2U)
                                           : ((0x00010000U 
                                               & __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val)
                                               ? (__Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val 
                                                  >> 1U)
                                               : __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__val)));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_b 
                        = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__6__Vfuncout;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x0019U;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 3U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else if ((3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                        = (0x0000ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                          >> 8U));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x00ccU;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 4U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else if ((4U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                        = (0x0003ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                                          + (0x0000ffffU 
                                             & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                                >> 8U))));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x0019U;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 5U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else if ((5U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum;
                    __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__Vfuncout 
                        = (0x0000ffffU & ((0x00020000U 
                                           & __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val)
                                           ? (__Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val 
                                              >> 2U)
                                           : ((0x00010000U 
                                               & __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val)
                                               ? (__Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val 
                                                  >> 1U)
                                               : __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__val)));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_c 
                        = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__7__Vfuncout;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x0019U;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 6U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else if ((6U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                        = (0x0000ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                          >> 8U));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x0019U;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 7U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                } else {
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                        = (0x0003ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                                          + (0x0000ffffU 
                                             & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                                >> 8U))));
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a 
                        = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b = 0x00ccU;
                    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 1U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 8U;
                    __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 1U;
                }
            } else if ((8U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state))) {
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val 
                    = vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum;
                __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__Vfuncout 
                    = (0x0000ffffU & ((0x00020000U 
                                       & __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val)
                                       ? (__Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val 
                                          >> 2U) : 
                                      ((0x00010000U 
                                        & __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val)
                                        ? (__Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val 
                                           >> 1U) : __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__val)));
                vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_d 
                    = __Vfunc_spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__phi_fold__8__Vfuncout;
                vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done = 1U;
                __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 0U;
            }
        }
    } else {
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state = 0U;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_a = 0U;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_b = 0U;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_c = 0U;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_d = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s = 0U;
        __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum = 0U;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done = 0U;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start = 0U;
    }
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
        = __Vdly__spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum;
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum 
        = (0x0003ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum 
                          + (0x0000ffffU & (vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod 
                                            >> 8U))));
}

void Vspu4_precession_tb___024root___nba_sequent__TOP__2(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___nba_sequent__TOP__2\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (vlSelfRef.__VdlySet__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0) {
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[0U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[1U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v1;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[2U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v2;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[3U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v3;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[4U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v4;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[5U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v5;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[6U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v6;
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[7U] 
            = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v7;
    }
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2 = (7U 
                                                & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                                                   [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                                                   >> 8U));
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
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_rot_start 
        = (((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
            & (1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))) 
           & (3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op 
        = ((1U & (- (IData)((0x10U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
           | ((2U & (- (IData)((0x40U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
              | (3U & (- (IData)((0x45U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3)))))));
    vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state 
        = ((- (IData)((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n))) 
           & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__next_state));
}

extern const VlUnpacked<CData/*1:0*/, 128> Vspu4_precession_tb__ConstPool__TABLE_hdc210f6a_0;

void Vspu4_precession_tb___024root___nba_comb__TOP__0(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___nba_comb__TOP__0\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*6:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    // Body
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

void Vspu4_precession_tb___024root___eval_nba(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_nba\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*6:0*/ __Vinline__nba_comb__TOP__0___Vtableidx1;
    __Vinline__nba_comb__TOP__0___Vtableidx1 = 0;
    // Body
    if ((2ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vspu4_precession_tb___024root___nba_sequent__TOP__0(vlSelf);
    }
    if ((6ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vspu4_precession_tb___024root___nba_sequent__TOP__1(vlSelf);
    }
    if ((2ULL & vlSelfRef.__VnbaTriggered[0U])) {
        if (vlSelfRef.__VdlySet__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0) {
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[0U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[1U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v1;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[2U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v2;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[3U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v3;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[4U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v4;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[5U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v5;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[6U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v6;
            vlSelfRef.spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf[7U] 
                = vlSelfRef.__VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v7;
        }
        vlSelfRef.__VdfgRegularize_h6e95ff9d_0_2 = 
            (7U & (vlSelfRef.spu4_precession_tb__DOT__prog_mem
                   [vlSelfRef.spu4_precession_tb__DOT__uut__DOT__pc_reg] 
                   >> 8U));
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
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__core_rot_start 
            = (((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n) 
                & (1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))) 
               & (3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op 
            = ((1U & (- (IData)((0x10U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
               | ((2U & (- (IData)((0x40U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))) 
                  | (3U & (- (IData)((0x45U == (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3)))))));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state 
            = ((- (IData)((IData)(vlSelfRef.spu4_precession_tb__DOT__rst_n))) 
               & (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__next_state));
    }
    if ((6ULL & vlSelfRef.__VnbaTriggered[0U])) {
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state_we 
            = (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done) 
                & (2U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))) 
               | ((3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                  & (1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state))));
        __Vinline__nba_comb__TOP__0___Vtableidx1 = 
            ((((((1U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)) 
                 << 3U) | ((3U != (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                           << 2U)) | (((3U == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__alu_op)) 
                                       << 1U) | (2U 
                                                 == (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)))) 
              << 3U) | (((IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__rot_done) 
                         << 2U) | (IData)(vlSelfRef.spu4_precession_tb__DOT__uut__DOT__state)));
        vlSelfRef.spu4_precession_tb__DOT__uut__DOT__next_state 
            = Vspu4_precession_tb__ConstPool__TABLE_hdc210f6a_0
            [__Vinline__nba_comb__TOP__0___Vtableidx1];
    }
}

void Vspu4_precession_tb___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vspu4_precession_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vspu4_precession_tb___024root___eval_phase__act(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_phase__act\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VactExecute;
    // Body
    Vspu4_precession_tb___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu4_precession_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vspu4_precession_tb___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    __VactExecute = Vspu4_precession_tb___024root___trigger_anySet__act(vlSelfRef.__VactTriggered);
    if (__VactExecute) {
        Vspu4_precession_tb___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vspu4_precession_tb___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vspu4_precession_tb___024root___eval_phase__nba(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_phase__nba\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vspu4_precession_tb___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vspu4_precession_tb___024root___eval_nba(vlSelf);
        Vspu4_precession_tb___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vspu4_precession_tb___024root___eval(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vspu4_precession_tb___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v", 3, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vspu4_precession_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/spu4_precession_tb.v", 3, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vspu4_precession_tb___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vspu4_precession_tb___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vspu4_precession_tb___024root___eval_debug_assertions(Vspu4_precession_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_precession_tb___024root___eval_debug_assertions\n"); );
    Vspu4_precession_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
