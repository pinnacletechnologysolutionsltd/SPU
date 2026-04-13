// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtang25k_smoketest_tb.h for the primary calling header

#include "Vtang25k_smoketest_tb__pch.h"

void Vtang25k_smoketest_tb___024root___eval_triggers_vec__act(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_triggers_vec__act\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((~ (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__rst_n__0)) 
                                                      << 2U) 
                                                     | ((((IData)(vlSelfRef.tang25k_smoketest_tb__DOT__clk) 
                                                          & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0))) 
                                                         << 1U) 
                                                        | ((IData)(vlSelfRef.tang25k_smoketest_tb__DOT__clk) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__clk__0 
        = vlSelfRef.tang25k_smoketest_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__tang25k_smoketest_tb__DOT__rst_n__0 
        = vlSelfRef.tang25k_smoketest_tb__DOT__rst_n;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VactDidInit)))))) {
        vlSelfRef.__VactDidInit = 1U;
        vlSelfRef.__VactTriggered[0U] = (1ULL | vlSelfRef.__VactTriggered[0U]);
    }
}

bool Vtang25k_smoketest_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___trigger_anySet__act\n"); );
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

void Vtang25k_smoketest_tb___024root___act_sequent__TOP__0(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___act_sequent__TOP__0\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.tang25k_smoketest_tb__DOT__clk = (1U 
                                                & (~ (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__clk)));
}

void Vtang25k_smoketest_tb___024root___eval_act(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_act\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VactTriggered[0U])) {
        vlSelfRef.tang25k_smoketest_tb__DOT__clk = 
            (1U & (~ (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__clk)));
    }
}

void Vtang25k_smoketest_tb___024root___nba_sequent__TOP__0(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___nba_sequent__TOP__0\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt = 0;
    CData/*0:0*/ __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 0;
    CData/*3:0*/ __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0;
    SData/*15:0*/ __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0;
    // Body
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt 
        = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy 
        = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
        = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div 
        = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
    if (vlSelfRef.tang25k_smoketest_tb__DOT__rst_n) {
        __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt 
            = ((IData)(1U) + vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt);
        if (VL_UNLIKELY((((~ (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started)) 
                          & (0x000003e8U == vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt))))) {
            VL_WRITEF_NX("SMOKE: POWER-ON OK at time=%0t\n",2, 'T',-9
                         , '#',64,VL_TIME_UNITED_Q(1000));
            vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started = 1U;
            __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 1U;
            __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0U;
            __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0U;
        }
        if (vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy) {
            __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div 
                = (0x0000ffffU & ((IData)(1U) + (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div)));
            if ((0x0064U == (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div))) {
                __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0U;
                if ((0U == (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit))) {
                    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
                        = (0x0000000fU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)));
                } else if (((1U <= (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)) 
                            & (8U >= (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)))) {
                    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
                        = (0x0000000fU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)));
                } else if (VL_UNLIKELY(((9U == (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit))))) {
                    VL_WRITEF_NX("SMOKE: UART SENT 'O' at time=%0t\n",2, 'T',-9
                                 , '#',64,VL_TIME_UNITED_Q(1000));
                    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0U;
                    __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 0U;
                    vlSelfRef.tang25k_smoketest_tb__DOT__smoke_ok = 1U;
                }
            }
        }
    } else {
        __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0U;
        __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0U;
        __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 0U;
        __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt = 0U;
        vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started = 0U;
        vlSelfRef.tang25k_smoketest_tb__DOT__smoke_ok = 0U;
    }
    vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt 
        = __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
    vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy 
        = __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
    vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
        = __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
    vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div 
        = __Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
}

void Vtang25k_smoketest_tb___024root___eval_nba(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_nba\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
    __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt = 0;
    CData/*0:0*/ __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
    __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 0;
    CData/*3:0*/ __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
    __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0;
    SData/*15:0*/ __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
    __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0;
    // Body
    if ((6ULL & vlSelfRef.__VnbaTriggered[0U])) {
        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt 
            = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy 
            = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
            = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div 
            = vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
        if (vlSelfRef.tang25k_smoketest_tb__DOT__rst_n) {
            __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt 
                = ((IData)(1U) + vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt);
            if (VL_UNLIKELY((((~ (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started)) 
                              & (0x000003e8U == vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt))))) {
                VL_WRITEF_NX("SMOKE: POWER-ON OK at time=%0t\n",2, 'T',-9
                             , '#',64,VL_TIME_UNITED_Q(1000));
                vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started = 1U;
                __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 1U;
                __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0U;
                __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0U;
            }
            if (vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy) {
                __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div 
                    = (0x0000ffffU & ((IData)(1U) + (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div)));
                if ((0x0064U == (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div))) {
                    __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0U;
                    if ((0U == (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit))) {
                        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
                            = (0x0000000fU & ((IData)(1U) 
                                              + (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)));
                    } else if (((1U <= (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)) 
                                & (8U >= (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)))) {
                        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
                            = (0x0000000fU & ((IData)(1U) 
                                              + (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit)));
                    } else if (VL_UNLIKELY(((9U == (IData)(vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit))))) {
                        VL_WRITEF_NX("SMOKE: UART SENT 'O' at time=%0t\n",2, 'T',-9
                                     , '#',64,VL_TIME_UNITED_Q(1000));
                        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0U;
                        __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 0U;
                        vlSelfRef.tang25k_smoketest_tb__DOT__smoke_ok = 1U;
                    }
                }
            }
        } else {
            __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit = 0U;
            __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div = 0U;
            __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy = 0U;
            __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt = 0U;
            vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__started = 0U;
            vlSelfRef.tang25k_smoketest_tb__DOT__smoke_ok = 0U;
        }
        vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt 
            = __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__cnt;
        vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy 
            = __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_busy;
        vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit 
            = __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_bit;
        vlSelfRef.tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div 
            = __Vinline__nba_sequent__TOP__0___Vdly__tang25k_smoketest_tb__DOT__uut__DOT__u_smoke__DOT__tx_div;
    }
}

void Vtang25k_smoketest_tb___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vtang25k_smoketest_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vtang25k_smoketest_tb___024root___eval_phase__act(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_phase__act\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VactExecute;
    // Body
    Vtang25k_smoketest_tb___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtang25k_smoketest_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vtang25k_smoketest_tb___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    __VactExecute = Vtang25k_smoketest_tb___024root___trigger_anySet__act(vlSelfRef.__VactTriggered);
    if (__VactExecute) {
        Vtang25k_smoketest_tb___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vtang25k_smoketest_tb___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vtang25k_smoketest_tb___024root___eval_phase__nba(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_phase__nba\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vtang25k_smoketest_tb___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vtang25k_smoketest_tb___024root___eval_nba(vlSelf);
        Vtang25k_smoketest_tb___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vtang25k_smoketest_tb___024root___eval(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtang25k_smoketest_tb___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v", 3, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtang25k_smoketest_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/spu4/tests/tang25k_smoketest_tb.v", 3, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vtang25k_smoketest_tb___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vtang25k_smoketest_tb___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vtang25k_smoketest_tb___024root___eval_debug_assertions(Vtang25k_smoketest_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtang25k_smoketest_tb___024root___eval_debug_assertions\n"); );
    Vtang25k_smoketest_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
