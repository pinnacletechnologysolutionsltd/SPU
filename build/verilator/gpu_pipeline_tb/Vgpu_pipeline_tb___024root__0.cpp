// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vgpu_pipeline_tb.h for the primary calling header

#include "Vgpu_pipeline_tb__pch.h"

void Vgpu_pipeline_tb___024root___eval_triggers_vec__act(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_triggers_vec__act\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    (((((IData)(vlSelfRef.gpu_pipeline_tb__DOT__reset) 
                                                        & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__reset__0))) 
                                                       << 5U) 
                                                      | (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk) 
                                                          & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0))) 
                                                         << 4U)) 
                                                     | (((((IData)(vlSelfRef.gpu_pipeline_tb__DOT__reset) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__reset__0)) 
                                                          << 3U) 
                                                         | (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__display_ready) 
                                                             != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__display_ready__0)) 
                                                            << 2U)) 
                                                        | ((((IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk) 
                                                             != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0)) 
                                                            << 1U) 
                                                           | ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk) 
                                                              != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0)))))));
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0 
        = vlSelfRef.gpu_pipeline_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__display_ready__0 
        = vlSelfRef.gpu_pipeline_tb__DOT__display_ready;
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__reset__0 
        = vlSelfRef.gpu_pipeline_tb__DOT__reset;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VactDidInit)))))) {
        vlSelfRef.__VactDidInit = 1U;
        vlSelfRef.__VactTriggered[0U] = (1ULL | vlSelfRef.__VactTriggered[0U]);
        vlSelfRef.__VactTriggered[0U] = (2ULL | vlSelfRef.__VactTriggered[0U]);
        vlSelfRef.__VactTriggered[0U] = (4ULL | vlSelfRef.__VactTriggered[0U]);
        vlSelfRef.__VactTriggered[0U] = (8ULL | vlSelfRef.__VactTriggered[0U]);
    }
}

bool Vgpu_pipeline_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___trigger_anySet__act\n"); );
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

void Vgpu_pipeline_tb___024root___act_sequent__TOP__0(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___act_sequent__TOP__0\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.gpu_pipeline_tb__DOT__clk = (1U & (~ (IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk)));
}

void Vgpu_pipeline_tb___024root___eval_act(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_act\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VactTriggered[0U])) {
        vlSelfRef.gpu_pipeline_tb__DOT__clk = (1U & 
                                               (~ (IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk)));
    }
}

extern const VlUnpacked<IData/*23:0*/, 256> Vgpu_pipeline_tb__ConstPool__TABLE_h39ac75e8_0;

void Vgpu_pipeline_tb___024root___nba_sequent__TOP__0(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___nba_sequent__TOP__0\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__Vfuncout;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__a;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__a = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__b;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__b = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__Vfuncout;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__a;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__a = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__b;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__b = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__a;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__a = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__b;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__b = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__c;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__c = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__Vfuncout;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__a;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__a = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__b;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__b = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__Vfuncout;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__a;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__a = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__b;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__b = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__Vfuncout;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__a;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__a = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__b;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__b = 0;
    IData/*31:0*/ __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c;
    __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c = 0;
    CData/*7:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    CData/*2:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state = 0;
    QData/*63:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 = 0;
    QData/*63:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 = 0;
    QData/*63:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 = 0;
    IData/*31:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x = 0;
    IData/*31:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x = 0;
    IData/*31:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y = 0;
    IData/*31:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x = 0;
    IData/*31:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y = 0;
    CData/*5:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt = 0;
    CData/*3:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = 0;
    SData/*12:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt = 0;
    CData/*1:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = 0;
    CData/*0:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en = 0;
    CData/*1:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane = 0;
    CData/*3:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 0;
    SData/*15:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer = 0;
    CData/*0:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = 0;
    CData/*3:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out = 0;
    IData/*31:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg = 0;
    CData/*5:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt = 0;
    CData/*1:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state = 0;
    // Body
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck 
        = vlSelfRef.gpu_pipeline_tb__DOT__spi_sck;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe;
    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x;
    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y 
        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y;
    if (vlSelfRef.gpu_pipeline_tb__DOT__reset) {
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer = 0x2710U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_ready = 0U;
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_valid = 0U;
    } else {
        if (vlSelfRef.gpu_pipeline_tb__DOT__clk) {
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt 
                = (0x0000003fU & ((IData)(1U) + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt)));
        }
        if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 1U;
            } else {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer 
                    = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer) 
                                      - (IData)(1U)));
            }
        } else if ((1U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = 1U;
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out 
                = (0x0eU & (IData)(__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out));
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg = 0x66990000U;
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt = 0x10U;
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 2U;
        } else if ((2U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt))) {
                if ((0U == (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                            >> 0x18U))) {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 3U;
                    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready = 1U;
                } else {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg = 0x35000000U;
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt = 8U;
                }
            } else {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt 
                    = (0x0000003fU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt) 
                                      - (IData)(1U)));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out 
                    = ((0x0eU & (IData)(__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out)) 
                       | (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                          >> 0x1fU));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                    = (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                       << 1U);
            }
        } else if ((3U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = 0U;
            if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = 1U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                    = (0xeb000000U | (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en)
                                        ? vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_addr
                                        : vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pour_psram_addr) 
                                      << 1U));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt = 8U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 4U;
            }
        } else if ((4U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 6U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer = 6U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = 0U;
            } else {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt 
                    = (0x0000003fU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt) 
                                      - (IData)(1U)));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out 
                    = (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                       >> 0x1cU);
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                    = (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
                       << 4U);
            }
        } else if ((6U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 7U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt = 2U;
            } else {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer 
                    = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer) 
                                      - (IData)(1U)));
            }
        } else if ((7U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state))) {
            if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 3U;
            } else {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt 
                    = (0x0000003fU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt) 
                                      - (IData)(1U)));
                vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_data 
                    = ((0x000000f0U & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_data) 
                                       << 4U)) | ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__psram_dq__en1) 
                                                  & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe)
                                                      ? (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out)
                                                      : 0U)));
            }
        } else {
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = 3U;
        }
        if ((0U != (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state))) {
            if ((1U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 = 0ULL;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 = 0ULL;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 = 0ULL;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state = 2U;
            } else if ((2U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state))) {
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__b 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__a 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0);
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state = 3U;
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__Vfuncout 
                    = ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__a 
                        < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__b)
                        ? ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__a 
                            < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__a
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c)
                        : ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__b 
                            < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__b
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__c));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x 
                    = __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__0__Vfuncout;
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__b 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__a 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__Vfuncout 
                    = ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__a 
                        > __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__b)
                        ? ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__a 
                            > __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__a
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c)
                        : ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__b 
                            > __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__b
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__c));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x 
                    = __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__1__Vfuncout;
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__c 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__b 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__2__a 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__b 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__a 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__Vfuncout 
                    = ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__a 
                        > __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__b)
                        ? ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__a 
                            > __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__a
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c)
                        : ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__b 
                            > __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__b
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__c));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y 
                    = __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max3__3__Vfuncout;
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__b 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__a 
                    = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0);
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__Vfuncout 
                    = ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__a 
                        < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__b)
                        ? ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__a 
                            < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__a
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c)
                        : ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__b 
                            < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__b
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__c));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x 
                    = __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__4__Vfuncout;
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__b 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__a 
                    = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                               >> 0x20U));
                __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__Vfuncout 
                    = ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__a 
                        < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__b)
                        ? ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__a 
                            < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__a
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c)
                        : ((__Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__b 
                            < __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c)
                            ? __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__b
                            : __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__c));
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y 
                    = __Vfunc_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min3__5__Vfuncout;
            } else if ((3U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state))) {
                if (((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x 
                      >= vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x) 
                     | (0x0000000fU <= vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x))) {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x 
                        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x;
                    if (((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y 
                          >= vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y) 
                         | (0x0000000fU <= vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y))) {
                        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state = 0U;
                    } else {
                        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y 
                            = ((IData)(1U) + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y);
                    }
                } else {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x 
                        = ((IData)(1U) + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x);
                }
            }
        }
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en = 0U;
        if ((0U != (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state))) {
            if ((1U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state))) {
                if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready) {
                    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en = 1U;
                    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_addr 
                        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__current_addr;
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state = 2U;
                }
            } else if ((2U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state))) {
                if ((1U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__rem_len))) {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state = 0U;
                } else {
                    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__rem_len 
                        = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__rem_len) 
                                          - (IData)(1U)));
                    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__current_addr 
                        = (0x007fffffU & ((IData)(1U) 
                                          + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__current_addr));
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state = 1U;
                }
            }
        }
        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en = 0U;
        if ((0U != (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state))) {
            if ((1U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state))) {
                if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_ready) {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en = 1U;
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = 2U;
                }
            } else if ((2U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state))) {
                if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_valid) {
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = 3U;
                    __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane = 0U;
                }
            } else if ((3U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state))) {
                if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready) {
                    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pour_psram_addr 
                        = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_psram_addr;
                    if ((3U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane))) {
                        if ((1U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__rem_quadrays))) {
                            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = 0U;
                        } else {
                            vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__rem_quadrays 
                                = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__rem_quadrays) 
                                                  - (IData)(1U)));
                            vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_storage_addr 
                                = ((IData)(1U) + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_storage_addr);
                            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = 1U;
                        }
                    } else {
                        __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane 
                            = (3U & ((IData)(1U) + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane)));
                    }
                    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_psram_addr 
                        = (0x007fffffU & ((IData)(1U) 
                                          + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_psram_addr));
                }
            }
        }
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_valid = 0U;
        if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state))) {
            vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_ready = 1U;
            if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en) {
                vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_ready = 0U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = 4U;
            }
        } else if ((4U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state))) {
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt = 0U;
            __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = 5U;
        } else if ((5U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state))) {
            if ((1U & (~ (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_miso)))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = 6U;
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt = 0U;
            }
        } else if ((6U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state))) {
            if ((0x0200U > (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt))) {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt 
                    = (0x00001fffU & ((IData)(0x0010U) 
                                      + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt)));
                vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_valid = 1U;
            } else {
                __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = 0U;
            }
        }
    }
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y;
    vlSelfRef.gpu_pipeline_tb__DOT__psram_dq__en1 = 
        ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe)
          ? 0x0fU : 0U);
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
        = (VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x) 
                            - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1))), 
                       (VL_EXTENDS_QI(64,32, (IData)(
                                                     (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                                                      >> 0x00000020U))) 
                        - VL_EXTENDS_QI(64,32, (IData)(
                                                       (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                                                        >> 0x00000020U))))) 
           - VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y) 
                              - VL_EXTENDS_QI(64,32, (IData)(
                                                             (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                                                              >> 0x00000020U)))), 
                         (VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2)) 
                          - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1)))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
        = (VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x) 
                            - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0))), 
                       (VL_EXTENDS_QI(64,32, (IData)(
                                                     (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                                                      >> 0x00000020U))) 
                        - VL_EXTENDS_QI(64,32, (IData)(
                                                       (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                                                        >> 0x00000020U))))) 
           - VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y) 
                              - VL_EXTENDS_QI(64,32, (IData)(
                                                             (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                                                              >> 0x00000020U)))), 
                         (VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1)) 
                          - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0)))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 
        = (VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x) 
                            - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2))), 
                       (VL_EXTENDS_QI(64,32, (IData)(
                                                     (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                                                      >> 0x00000020U))) 
                        - VL_EXTENDS_QI(64,32, (IData)(
                                                       (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                                                        >> 0x00000020U))))) 
           - VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y) 
                              - VL_EXTENDS_QI(64,32, (IData)(
                                                             (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                                                              >> 0x00000020U)))), 
                         (VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0)) 
                          - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2)))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
        = (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
           + (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
              + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2));
    __Vtableidx1 = (0x000000ffU & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                                           >> 0x00000038U)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal 
        = Vgpu_pipeline_tb__ConstPool__TABLE_h39ac75e8_0
        [__Vtableidx1];
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt 
        = __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt;
}

void Vgpu_pipeline_tb___024root___nba_sequent__TOP__1(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___nba_sequent__TOP__1\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY((((~ (IData)(vlSymsp->TOP____024unit.__VmonitorOff)) 
                      & (1U == vlSymsp->TOP____024unit.__VmonitorNum))))) {
        VL_WRITEF_NX("Time=%t | clk=%b reset=%b | pix_in=%b | l0=%h l1=%h l2=%h | frag_E=%h | spi_mosi=%b | disp_ready=%b\n",11, 'T',-9
                     , '#',64,VL_TIME_UNITED_Q(1000)
                     , '#',1,(IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk)
                     , '#',1,vlSelfRef.gpu_pipeline_tb__DOT__reset
                     , '#',1,(IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside)
                     , '#',32,vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0
                     , '#',32,vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1
                     , '#',32,vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2
                     , '#',64,(((QData)((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[3U])) 
                                << 0x00000020U) | (QData)((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[2U])))
                     , '#',1,(IData)(vlSelfRef.gpu_pipeline_tb__DOT__spi_mosi)
                     , '#',1,((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready) 
                              & (0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state))));
    }
}

void Vgpu_pipeline_tb___024root___nba_sequent__TOP__2(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___nba_sequent__TOP__2\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 = 0;
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 = 0;
    SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 = 0;
    SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3 = 0;
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0 = 0;
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 = 0;
    // Body
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa 
        = (0x0000ffffU & vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0);
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb 
        = (0x0000ffffU & vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1);
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc 
        = (0x0000ffffU & vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2);
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[0U] = 0U;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[1U] = 0U;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[2U] = 0U;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[3U] = 0U;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 
        = VL_MULS_III(32, (IData)(0x000000deU), VL_EXTENDS_II(32,16, 
                                                              (0x0000ffffU 
                                                               & (VL_EXTENDS_II(16,16, 
                                                                                (0x0000ffffU 
                                                                                & ((IData)(8U) 
                                                                                + 
                                                                                (0x00001fffU 
                                                                                & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa) 
                                                                                - 
                                                                                VL_SHIFTRS_III(17,17,32, 
                                                                                (0x0001ffffU 
                                                                                & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc) 
                                                                                + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb))), 1U)) 
                                                                                >> 4U))))) 
                                                                  - (IData)(8U)))));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0 
        = VL_EXTENDS_II(32,16, (0x0000ffffU & (VL_EXTENDS_II(16,16, 
                                                             (0x0000ffffU 
                                                              & ((IData)(8U) 
                                                                 + 
                                                                 (0x00001fffU 
                                                                  & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb) 
                                                                      - (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc)) 
                                                                     >> 4U))))) 
                                               - (IData)(8U))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1 
        = (0x0000ffffU & ((VL_MULS_III(32, (IData)(0x00000100U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                           >> 0x0000001fU) ? ((IData)(1U) 
                                              + (~ 
                                                 (VL_MULS_III(32, (IData)(0x00000100U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                                                  >> 8U)))
                           : (VL_MULS_III(32, (IData)(0x00000100U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                              >> 8U)));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
        = (VL_MULS_III(32, (IData)(0x00000080U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
           + gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1);
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
        = (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 
           + VL_MULS_III(32, (IData)(0xffffff80U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 
        = (0x0000ffffU & ((gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                           >> 0x0000001fU) ? ((IData)(1U) 
                                              + (~ 
                                                 (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                                                  >> 8U)))
                           : (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                              >> 8U)));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3 
        = (0x0000ffffU & ((gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                           >> 0x0000001fU) ? ((IData)(1U) 
                                              + (~ 
                                                 (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                                                  >> 8U)))
                           : (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                              >> 8U)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2 
        = (((IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2) 
            < (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3))
            ? (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2)
            : (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3));
}

void Vgpu_pipeline_tb___024root___nba_sequent__TOP__3(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___nba_sequent__TOP__3\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    VlWide<3>/*95:0*/ __Vtemp_1;
    VlWide<3>/*95:0*/ __Vtemp_2;
    VlWide<3>/*95:0*/ __Vtemp_3;
    VlWide<3>/*95:0*/ __Vtemp_4;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_7;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_9;
    // Body
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready 
        = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside 
        = (((1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
                           >> 0x0000003fU))) == (1U 
                                                 & (IData)(
                                                           (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                                                            >> 0x0000003fU)))) 
           & (((1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
                              >> 0x0000003fU))) == 
               (1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                              >> 0x0000003fU)))) & 
              ((1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 
                              >> 0x0000003fU))) == 
               (1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                              >> 0x0000003fU))))));
    if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside) {
        __Vtemp_1[0U] = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        __Vtemp_1[1U] = 0U;
        __Vtemp_1[2U] = 0U;
        __Vtemp_2[0U] = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0);
        __Vtemp_2[1U] = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
                                 >> 0x00000020U));
        __Vtemp_2[2U] = 0U;
        VL_MUL_W(3, __Vtemp_3, __Vtemp_1, __Vtemp_2);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0 
            = ((__Vtemp_3[1U] << 0x00000019U) | (__Vtemp_3[0U] 
                                                 >> 7U));
        __Vtemp_4[0U] = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        __Vtemp_4[1U] = 0U;
        __Vtemp_4[2U] = 0U;
        __Vtemp_5[0U] = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1);
        __Vtemp_5[1U] = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
                                 >> 0x00000020U));
        __Vtemp_5[2U] = 0U;
        VL_MUL_W(3, __Vtemp_6, __Vtemp_4, __Vtemp_5);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1 
            = ((__Vtemp_6[1U] << 0x00000019U) | (__Vtemp_6[0U] 
                                                 >> 7U));
        __Vtemp_7[0U] = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        __Vtemp_7[1U] = 0U;
        __Vtemp_7[2U] = 0U;
        __Vtemp_8[0U] = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2);
        __Vtemp_8[1U] = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 
                                 >> 0x00000020U));
        __Vtemp_8[2U] = 0U;
        VL_MUL_W(3, __Vtemp_9, __Vtemp_7, __Vtemp_8);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2 
            = ((__Vtemp_9[1U] << 0x00000019U) | (__Vtemp_9[0U] 
                                                 >> 7U));
    } else {
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0 = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1 = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2 = 0U;
    }
    if (vlSelfRef.gpu_pipeline_tb__DOT__reset) {
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__spi_mosi = 0U;
    } else if ((2U & (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state))) {
        if ((1U & (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state))) {
            vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck = 0U;
            vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = 0U;
        } else {
            vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt 
                = (7U & ((IData)(1U) + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt)));
            if ((3U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt))) {
                vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck 
                    = (1U & (~ (IData)(vlSelfRef.gpu_pipeline_tb__DOT__spi_sck)));
                vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt = 0U;
                if (vlSelfRef.gpu_pipeline_tb__DOT__spi_sck) {
                    if ((0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt))) {
                        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = 3U;
                    } else {
                        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt 
                            = (0x0000000fU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt) 
                                              - (IData)(1U)));
                    }
                } else {
                    vlSelfRef.gpu_pipeline_tb__DOT__spi_mosi 
                        = (1U & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg) 
                                 >> 0x0fU));
                    vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg 
                        = (0x0000fffeU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg) 
                                          << 1U));
                }
            }
        }
    } else if ((1U & (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state))) {
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg 
            = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt = 0x0fU;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck = 0U;
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = 2U;
    } else {
        vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck = 0U;
        if (vlSelfRef.gpu_pipeline_tb__DOT__clk) {
            vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch 
                = ((0x0000f800U & (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 7U) 
                                   + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5))) 
                   | ((0x000007e0U & ((VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 3U) 
                                       + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5)) 
                                      >> 5U)) | (0x0000001fU 
                                                 & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6) 
                                                    >> 0x0000000bU))));
            vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = 1U;
        }
    }
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch 
        = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg 
        = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt 
        = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt 
        = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt;
    vlSelfRef.gpu_pipeline_tb__DOT__spi_sck = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__spi_sck;
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state 
        = vlSelfRef.__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state;
    vlSelfRef.gpu_pipeline_tb__DOT__display_ready = 
        ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready) 
         & (0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state)));
}

void Vgpu_pipeline_tb___024root___nba_comb__TOP__0(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___nba_comb__TOP__0\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain = 0;
    // Body
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain 
        = (0x0000ffffU & (VL_EXTENDS_II(16,9, (0x000000ffU 
                                               & ((IData)(0x14U) 
                                                  + 
                                                  (7U 
                                                   & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt) 
                                                      >> 3U))))) 
                          - VL_EXTENDS_II(16,9, (0x000000ffU 
                                                 & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1) 
                                                     < (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2))
                                                     ? (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1)
                                                     : (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2))))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10 
        = (VL_LTS_III(32, 0U, VL_EXTENDS_II(32,16, (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain)))
            ? (0x000000ffU & VL_SHIFTR_III(8,16,32, 
                                           (0x0000ffffU 
                                            & ((IData)(0x00ffU) 
                                               * (0x0000ffffU 
                                                  & ((IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain) 
                                                     * (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain))))), 0x0000000eU))
            : 0U);
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6 
        = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10) 
                          + VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 4U)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5 
        = (0x0000ffffU & (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 5U) 
                          + (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 1U) 
                             + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6))));
}

void Vgpu_pipeline_tb___024root___eval_nba(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_nba\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2;
    __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 = 0;
    IData/*31:0*/ __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3;
    __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 = 0;
    SData/*15:0*/ __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2;
    __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 = 0;
    SData/*15:0*/ __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3;
    __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3 = 0;
    IData/*31:0*/ __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0;
    __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0 = 0;
    IData/*31:0*/ __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1;
    __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 = 0;
    SData/*15:0*/ __Vinline__nba_comb__TOP__0_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain;
    __Vinline__nba_comb__TOP__0_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain = 0;
    // Body
    if ((0x0000000000000030ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vgpu_pipeline_tb___024root___nba_sequent__TOP__0(vlSelf);
    }
    if ((0x000000000000000eULL & vlSelfRef.__VnbaTriggered[0U])) {
        if (VL_UNLIKELY((((~ (IData)(vlSymsp->TOP____024unit.__VmonitorOff)) 
                          & (1U == vlSymsp->TOP____024unit.__VmonitorNum))))) {
            VL_WRITEF_NX("Time=%t | clk=%b reset=%b | pix_in=%b | l0=%h l1=%h l2=%h | frag_E=%h | spi_mosi=%b | disp_ready=%b\n",11, 'T',-9
                         , '#',64,VL_TIME_UNITED_Q(1000)
                         , '#',1,(IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk)
                         , '#',1,vlSelfRef.gpu_pipeline_tb__DOT__reset
                         , '#',1,(IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside)
                         , '#',32,vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0
                         , '#',32,vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1
                         , '#',32,vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2
                         , '#',64,(((QData)((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[3U])) 
                                    << 0x00000020U) 
                                   | (QData)((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[2U])))
                         , '#',1,(IData)(vlSelfRef.gpu_pipeline_tb__DOT__spi_mosi)
                         , '#',1,((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready) 
                                  & (0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state))));
        }
    }
    if ((0x0000000000000010ULL & vlSelfRef.__VnbaTriggered[0U])) {
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa 
            = (0x0000ffffU & vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb 
            = (0x0000ffffU & vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc 
            = (0x0000ffffU & vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[0U] = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[1U] = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[2U] = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n[3U] = 0U;
        __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 
            = VL_MULS_III(32, (IData)(0x000000deU), 
                          VL_EXTENDS_II(32,16, (0x0000ffffU 
                                                & (VL_EXTENDS_II(16,16, 
                                                                 (0x0000ffffU 
                                                                  & ((IData)(8U) 
                                                                     + 
                                                                     (0x00001fffU 
                                                                      & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa) 
                                                                          - 
                                                                          VL_SHIFTRS_III(17,17,32, 
                                                                                (0x0001ffffU 
                                                                                & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc) 
                                                                                + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb))), 1U)) 
                                                                         >> 4U))))) 
                                                   - (IData)(8U)))));
        __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0 
            = VL_EXTENDS_II(32,16, (0x0000ffffU & (
                                                   VL_EXTENDS_II(16,16, 
                                                                 (0x0000ffffU 
                                                                  & ((IData)(8U) 
                                                                     + 
                                                                     (0x00001fffU 
                                                                      & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb) 
                                                                          - (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc)) 
                                                                         >> 4U))))) 
                                                   - (IData)(8U))));
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1 
            = (0x0000ffffU & ((VL_MULS_III(32, (IData)(0x00000100U), __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                               >> 0x0000001fU) ? ((IData)(1U) 
                                                  + 
                                                  (~ 
                                                   (VL_MULS_III(32, (IData)(0x00000100U), __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                                                    >> 8U)))
                               : (VL_MULS_III(32, (IData)(0x00000100U), __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                                  >> 8U)));
        __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
            = (VL_MULS_III(32, (IData)(0x00000080U), __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
               + __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1);
        __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
            = (__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 
               + VL_MULS_III(32, (IData)(0xffffff80U), __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0));
        __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 
            = (0x0000ffffU & ((__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                               >> 0x0000001fU) ? ((IData)(1U) 
                                                  + 
                                                  (~ 
                                                   (__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                                                    >> 8U)))
                               : (__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                                  >> 8U)));
        __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3 
            = (0x0000ffffU & ((__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                               >> 0x0000001fU) ? ((IData)(1U) 
                                                  + 
                                                  (~ 
                                                   (__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                                                    >> 8U)))
                               : (__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                                  >> 8U)));
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2 
            = ((__Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 
                < __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3)
                ? __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2
                : __Vinline__nba_sequent__TOP__2_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3);
    }
    if ((0x0000000000000030ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vgpu_pipeline_tb___024root___nba_sequent__TOP__3(vlSelf);
    }
    if ((0x0000000000000030ULL & vlSelfRef.__VnbaTriggered[0U])) {
        __Vinline__nba_comb__TOP__0_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain 
            = (0x0000ffffU & (VL_EXTENDS_II(16,9, (0x000000ffU 
                                                   & ((IData)(0x14U) 
                                                      + 
                                                      (7U 
                                                       & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt) 
                                                          >> 3U))))) 
                              - VL_EXTENDS_II(16,9, 
                                              (0x000000ffU 
                                               & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1) 
                                                   < (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2))
                                                   ? (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1)
                                                   : (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2))))));
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10 
            = (VL_LTS_III(32, 0U, VL_EXTENDS_II(32,16, __Vinline__nba_comb__TOP__0_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain))
                ? (0x000000ffU & VL_SHIFTR_III(8,16,32, 
                                               (0x0000ffffU 
                                                & ((IData)(0x00ffU) 
                                                   * 
                                                   (0x0000ffffU 
                                                    & ((IData)(__Vinline__nba_comb__TOP__0_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain) 
                                                       * (IData)(__Vinline__nba_comb__TOP__0_gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain))))), 0x0000000eU))
                : 0U);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6 
            = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10) 
                              + VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 4U)));
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5 
            = (0x0000ffffU & (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 5U) 
                              + (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 1U) 
                                 + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6))));
    }
}

void Vgpu_pipeline_tb___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vgpu_pipeline_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vgpu_pipeline_tb___024root___eval_phase__act(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_phase__act\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VactExecute;
    // Body
    Vgpu_pipeline_tb___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vgpu_pipeline_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vgpu_pipeline_tb___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    __VactExecute = Vgpu_pipeline_tb___024root___trigger_anySet__act(vlSelfRef.__VactTriggered);
    if (__VactExecute) {
        Vgpu_pipeline_tb___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vgpu_pipeline_tb___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vgpu_pipeline_tb___024root___eval_phase__nba(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_phase__nba\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vgpu_pipeline_tb___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vgpu_pipeline_tb___024root___eval_nba(vlSelf);
        Vgpu_pipeline_tb___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vgpu_pipeline_tb___024root___eval(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vgpu_pipeline_tb___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/rtl/tb/gpu_pipeline_tb.v", 9, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vgpu_pipeline_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/rtl/tb/gpu_pipeline_tb.v", 9, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vgpu_pipeline_tb___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vgpu_pipeline_tb___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vgpu_pipeline_tb___024root___eval_debug_assertions(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_debug_assertions\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
