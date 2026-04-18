// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtb_spu_flow_control.h for the primary calling header

#include "Vtb_spu_flow_control__pch.h"

void Vtb_spu_flow_control___024root___eval_triggers_vec__act(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_triggers_vec__act\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((~ (IData)(vlSelfRef.tb_spu_flow_control__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__rst_n__0)) 
                                                      << 2U) 
                                                     | ((((IData)(vlSelfRef.tb_spu_flow_control__DOT__clk) 
                                                          & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0))) 
                                                         << 1U) 
                                                        | ((IData)(vlSelfRef.tb_spu_flow_control__DOT__clk) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0 
        = vlSelfRef.tb_spu_flow_control__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__rst_n__0 
        = vlSelfRef.tb_spu_flow_control__DOT__rst_n;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VactDidInit)))))) {
        vlSelfRef.__VactDidInit = 1U;
        vlSelfRef.__VactTriggered[0U] = (1ULL | vlSelfRef.__VactTriggered[0U]);
    }
}

bool Vtb_spu_flow_control___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___trigger_anySet__act\n"); );
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

void Vtb_spu_flow_control___024root___act_sequent__TOP__0(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___act_sequent__TOP__0\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.tb_spu_flow_control__DOT__clk = (1U & 
                                               (~ (IData)(vlSelfRef.tb_spu_flow_control__DOT__clk)));
}

void Vtb_spu_flow_control___024root___eval_act(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_act\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VactTriggered[0U])) {
        vlSelfRef.tb_spu_flow_control__DOT__clk = (1U 
                                                   & (~ (IData)(vlSelfRef.tb_spu_flow_control__DOT__clk)));
    }
}

void Vtb_spu_flow_control___024root___nba_sequent__TOP__0(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___nba_sequent__TOP__0\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*2:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__sck_r;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__sck_r = 0;
    CData/*2:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__cs_r;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__cs_r = 0;
    CData/*1:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__mosi_r;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__mosi_r = 0;
    CData/*2:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__state;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0;
    CData/*5:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits = 0;
    CData/*2:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 0;
    CData/*5:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx = 0;
    CData/*7:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out = 0;
    CData/*2:0*/ __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v0;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v0 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v4;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v4 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v0;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v0 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v4;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v4 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v4;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v4 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v5;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v5 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v8;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v8 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v9;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v9 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v12;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v12 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v13;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v13 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v16;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v16 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v17;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v17 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v20;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v20 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v21;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v21 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v24;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v24 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v25;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v25 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v28;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v28 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v29;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v29 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v34;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v34 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v37;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v37 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v38;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v38 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v39;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v39 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v40;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v40 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v41;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v41 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v42;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v42 = 0;
    CData/*7:0*/ __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v43;
    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v43 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v44;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v44 = 0;
    CData/*0:0*/ __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v45;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v45 = 0;
    // Body
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__sck_r 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__mosi_r 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__mosi_r;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__cs_r 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v0 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v4 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v0 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v4 = 0U;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__recv_bits;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_bit;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__byte_idx;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__shift_out;
    __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt 
        = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__bit_cnt;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v44 = 0U;
    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v45 = 0U;
    if (vlSelfRef.tb_spu_flow_control__DOT__rst_n) {
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__sck_r 
            = ((6U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r) 
                      << 1U)) | (IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_sck));
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__mosi_r 
            = ((2U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__mosi_r) 
                      << 1U)) | (IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_mosi));
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__cs_r 
            = ((6U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r) 
                      << 1U)) | (IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_cs_n));
        if ((4U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state))) {
            if ((2U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state))) {
                __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
            } else if ((1U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
                } else if ((1U == (3U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r) 
                                         >> 1U)))) {
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__data_shift 
                        = ((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__data_shift 
                            << 1U) | (QData)((IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__mosi_r) 
                                                         >> 1U)))));
                    if ((0x3fU == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__recv_bits))) {
                        __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits = 0U;
                        __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
                    } else {
                        __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits 
                            = (0x0000003fU & ((IData)(1U) 
                                              + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__recv_bits)));
                    }
                }
            } else if ((2U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r))) {
                __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
            } else if ((1U == (3U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r) 
                                     >> 1U)))) {
                vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__hdr_shift 
                    = ((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__hdr_shift 
                        << 1U) | (QData)((IData)((1U 
                                                  & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__mosi_r) 
                                                     >> 1U)))));
                if ((0x3fU == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__recv_bits))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits = 0U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 5U;
                } else {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits 
                        = (0x0000003fU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__recv_bits)));
                }
            }
        } else if ((2U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state))) {
            if ((1U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
                    vlSelfRef.tb_spu_flow_control__DOT__spi_miso = 0U;
                } else if ((2U == (3U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r) 
                                         >> 1U)))) {
                    if ((0U == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_bit))) {
                        __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 7U;
                        if (((0x0000003fU & ((IData)(1U) 
                                             + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__byte_idx))) 
                             < (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_len))) {
                            __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx 
                                = (0x0000003fU & ((IData)(1U) 
                                                  + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__byte_idx)));
                            __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out 
                                = vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf
                                [(0x0000001fU & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__byte_idx)))];
                            vlSelfRef.tb_spu_flow_control__DOT__spi_miso 
                                = (1U & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf
                                         [(0x0000001fU 
                                           & ((IData)(1U) 
                                              + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__byte_idx)))] 
                                         >> 7U));
                        } else {
                            vlSelfRef.tb_spu_flow_control__DOT__spi_miso = 0U;
                        }
                    } else {
                        __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit 
                            = (7U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_bit) 
                                     - (IData)(1U)));
                        vlSelfRef.tb_spu_flow_control__DOT__spi_miso 
                            = (1U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__shift_out) 
                                     >> (7U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_bit) 
                                               - (IData)(1U)))));
                    }
                }
            } else if ((2U == (3U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r) 
                                     >> 1U)))) {
                if ((0xa0U == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx = 0U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[0U] 
                                          >> 8U));
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0 = 1U;
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_len = 0x20U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[0U] 
                                          >> 8U));
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 7U;
                    vlSelfRef.tb_spu_flow_control__DOT__spi_miso 
                        = (1U & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[0U] 
                                 >> 0x0fU));
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 3U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[0U]);
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1 = 1U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v4 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[0U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v5 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[0U]);
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v8 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[1U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v9 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[1U]);
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v12 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[1U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v13 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[1U]);
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v16 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[2U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v17 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[2U]);
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v20 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[2U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v21 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[2U]);
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v24 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[3U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v25 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[3U]);
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v28 
                        = (0x000000ffU & (vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[3U] 
                                          >> 8U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v29 
                        = (0x000000ffU & vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[3U]);
                } else if ((0xacU == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx = 0U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32 
                        = (0x000000ffU & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__dissonance_lat) 
                                          >> 8U));
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32 = 1U;
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_len = 3U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out 
                        = (0x000000ffU & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__dissonance_lat) 
                                          >> 8U));
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 7U;
                    vlSelfRef.tb_spu_flow_control__DOT__spi_miso 
                        = (1U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__dissonance_lat) 
                                 >> 0x0fU));
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 3U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33 
                        = (0x000000ffU & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__dissonance_lat));
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33 = 1U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v34 
                        = ((((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__ratio_lat) 
                             << 5U) | ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__ratio_valid_lat) 
                                       << 4U)) | (((IData)(vlSelfRef.tb_spu_flow_control__DOT__fifo_full) 
                                                   << 3U) 
                                                  | (((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__janus_lat) 
                                                      << 1U) 
                                                     | (1U 
                                                        & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__snaps_lat)))));
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__ratio_valid_lat = 0U;
                } else if ((0xadU == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx = 0U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 0x2cU)));
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35 = 1U;
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_len = 9U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 0x2cU)));
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 7U;
                    vlSelfRef.tb_spu_flow_control__DOT__spi_miso 
                        = (1U & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                         >> 0x33U)));
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 3U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 0x24U)));
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36 = 1U;
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v37 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 0x1cU)));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v38 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 0x14U)));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v39 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 0x0cU)));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v40 
                        = (0x000000ffU & (IData)((vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat 
                                                  >> 4U)));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v41 
                        = (0x0000000fU & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v42 
                        = (0x000000ffU & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_overflow_lat) 
                                          >> 5U));
                    __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v43 
                        = (0x0000001fU & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_overflow_lat));
                } else if ((0xa5U == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits = 0U;
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__hdr_shift = 0ULL;
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__data_shift = 0ULL;
                    vlSelfRef.tb_spu_flow_control__DOT__spi_miso = 0U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 4U;
                } else {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx = 0U;
                    __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v44 = 1U;
                    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_len = 1U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out = 0U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 7U;
                    vlSelfRef.tb_spu_flow_control__DOT__spi_miso = 0U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state))) {
            if ((2U & (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r))) {
                __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
            } else if ((1U == (3U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r) 
                                     >> 1U)))) {
                vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte 
                    = ((0x000000feU & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte) 
                                       << 1U)) | (1U 
                                                  & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__mosi_r) 
                                                     >> 1U)));
                if ((7U == (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__bit_cnt))) {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 2U;
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt = 0U;
                } else {
                    __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt 
                        = (7U & ((IData)(1U) + (IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__bit_cnt)));
                }
            }
        } else {
            vlSelfRef.tb_spu_flow_control__DOT__spi_miso = 0U;
            if ((1U & (~ ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r) 
                          >> 1U)))) {
                __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt = 0U;
                vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte = 0U;
                __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 1U;
            }
        }
        if ((2U == (3U & ((IData)(vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r) 
                          >> 1U)))) {
            __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v0 = 1U;
            __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v0 = 1U;
            vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__dissonance_lat = 0x1234U;
            vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__janus_lat = 1U;
            vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__snaps_lat = 0U;
            vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat = 0ULL;
            vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_overflow_lat = 0U;
        }
    } else {
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__sck_r = 0U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__mosi_r = 0U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__cs_r = 7U;
        __VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v4 = 1U;
        __VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v4 = 1U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cmd_byte = 0U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__hdr_shift = 0ULL;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__data_shift = 0ULL;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits = 0U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__state = 0U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit = 7U;
        __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_len = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__spi_miso = 0U;
        __VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v45 = 1U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__dissonance_lat = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__janus_lat = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__snaps_lat = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat = 0ULL;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__scale_overflow_lat = 0U;
    }
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__state 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__state;
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__sck_r 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__sck_r;
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__mosi_r 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__mosi_r;
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__recv_bits 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__recv_bits;
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_bit 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__resp_bit;
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__byte_idx 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__byte_idx;
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__shift_out 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__shift_out;
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v0) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[0U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[1U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[2U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[3U] = 0U;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__p_axis__v4) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[0U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[1U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[2U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__p_axis[3U] = 0U;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v0) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[0U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[1U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[2U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[3U] = 0U;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__q_axis__v4) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[0U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[1U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[2U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__q_axis[3U] = 0U;
    }
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__bit_cnt 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__bit_cnt;
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[0U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v0;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[1U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v1;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[2U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[3U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[4U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v4;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[5U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v5;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[6U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[7U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[8U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v8;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[9U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v9;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[10U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[11U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[12U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v12;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[13U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v13;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[14U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[15U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[16U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v16;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[17U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v17;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[18U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[19U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[20U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v20;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[21U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v21;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[22U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[23U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[24U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v24;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[25U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v25;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[26U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[27U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[28U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v28;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[29U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v29;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[30U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[31U] = 0U;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[0U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v32;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[1U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v33;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[2U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v34;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[0U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v35;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[1U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v36;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[2U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v37;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[3U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v38;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[4U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v39;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[5U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v40;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[6U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v41;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[7U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v42;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[8U] 
            = __VdlyVal__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v43;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v44) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[0U] = 0U;
    }
    if (__VdlySet__tb_spu_flow_control__DOT__uut__DOT__resp_buf__v45) {
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[0U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[1U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[2U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[3U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[4U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[5U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[6U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[7U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[8U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[9U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[10U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[11U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[12U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[13U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[14U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[15U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[16U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[17U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[18U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[19U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[20U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[21U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[22U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[23U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[24U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[25U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[26U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[27U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[28U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[29U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[30U] = 0U;
        vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__resp_buf[31U] = 0U;
    }
    vlSelfRef.tb_spu_flow_control__DOT__uut__DOT__cs_r 
        = __Vdly__tb_spu_flow_control__DOT__uut__DOT__cs_r;
}

void Vtb_spu_flow_control___024root___eval_nba(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_nba\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((6ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtb_spu_flow_control___024root___nba_sequent__TOP__0(vlSelf);
    }
}

void Vtb_spu_flow_control___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vtb_spu_flow_control___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vtb_spu_flow_control___024root___eval_phase__act(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_phase__act\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VactExecute;
    // Body
    Vtb_spu_flow_control___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtb_spu_flow_control___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vtb_spu_flow_control___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    __VactExecute = Vtb_spu_flow_control___024root___trigger_anySet__act(vlSelfRef.__VactTriggered);
    if (__VactExecute) {
        Vtb_spu_flow_control___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vtb_spu_flow_control___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vtb_spu_flow_control___024root___eval_phase__nba(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_phase__nba\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vtb_spu_flow_control___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vtb_spu_flow_control___024root___eval_nba(vlSelf);
        Vtb_spu_flow_control___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vtb_spu_flow_control___024root___eval(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtb_spu_flow_control___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_flow_control.v", 4, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtb_spu_flow_control___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_flow_control.v", 4, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vtb_spu_flow_control___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vtb_spu_flow_control___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vtb_spu_flow_control___024root___eval_debug_assertions(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_debug_assertions\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
