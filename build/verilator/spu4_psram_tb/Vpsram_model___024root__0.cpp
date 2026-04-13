// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vpsram_model.h for the primary calling header

#include "Vpsram_model__pch.h"

void Vpsram_model___024root___eval_triggers_vec__act(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_triggers_vec__act\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((IData)(vlSelfRef.sck) 
                                                       & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__sck__0))) 
                                                      << 1U) 
                                                     | ((IData)(vlSelfRef.ce_n) 
                                                        & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__ce_n__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__ce_n__0 = vlSelfRef.ce_n;
    vlSelfRef.__Vtrigprevexpr___TOP__sck__0 = vlSelfRef.sck;
}

bool Vpsram_model___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___trigger_anySet__act\n"); );
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

void Vpsram_model___024root___nba_sequent__TOP__0(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___nba_sequent__TOP__0\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*3:0*/ __Vdly__psram_model__DOT__state;
    __Vdly__psram_model__DOT__state = 0;
    CData/*7:0*/ __Vdly__psram_model__DOT__bit_cnt;
    __Vdly__psram_model__DOT__bit_cnt = 0;
    CData/*7:0*/ __Vdly__psram_model__DOT__cmd;
    __Vdly__psram_model__DOT__cmd = 0;
    IData/*23:0*/ __Vdly__psram_model__DOT__addr_r;
    __Vdly__psram_model__DOT__addr_r = 0;
    CData/*7:0*/ __VdlyVal__psram_model__DOT__mem__v0;
    __VdlyVal__psram_model__DOT__mem__v0 = 0;
    CData/*7:0*/ __VdlyDim0__psram_model__DOT__mem__v0;
    __VdlyDim0__psram_model__DOT__mem__v0 = 0;
    CData/*0:0*/ __VdlySet__psram_model__DOT__mem__v0;
    __VdlySet__psram_model__DOT__mem__v0 = 0;
    // Body
    __Vdly__psram_model__DOT__state = vlSelfRef.psram_model__DOT__state;
    __Vdly__psram_model__DOT__bit_cnt = vlSelfRef.psram_model__DOT__bit_cnt;
    __Vdly__psram_model__DOT__cmd = vlSelfRef.psram_model__DOT__cmd;
    __Vdly__psram_model__DOT__addr_r = vlSelfRef.psram_model__DOT__addr_r;
    __VdlySet__psram_model__DOT__mem__v0 = 0U;
    if (vlSelfRef.ce_n) {
        vlSelfRef.psram_model__DOT__dq_oe = 0U;
        __Vdly__psram_model__DOT__state = 0U;
        __Vdly__psram_model__DOT__bit_cnt = 0U;
    } else if (((((((((0U == (IData)(vlSelfRef.psram_model__DOT__state)) 
                      | (1U == (IData)(vlSelfRef.psram_model__DOT__state))) 
                     | (2U == (IData)(vlSelfRef.psram_model__DOT__state))) 
                    | (3U == (IData)(vlSelfRef.psram_model__DOT__state))) 
                   | (4U == (IData)(vlSelfRef.psram_model__DOT__state))) 
                  | (5U == (IData)(vlSelfRef.psram_model__DOT__state))) 
                 | (6U == (IData)(vlSelfRef.psram_model__DOT__state))) 
                | (9U == (IData)(vlSelfRef.psram_model__DOT__state)))) {
        if ((0U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            if (vlSelfRef.psram_model__DOT__qpi_mode) {
                __Vdly__psram_model__DOT__cmd = ((0x000000f0U 
                                                  & ((IData)(vlSelfRef.psram_model__DOT__cmd) 
                                                     << 4U)) 
                                                 | (IData)(vlSelfRef.dq));
                if ((1U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                    __Vdly__psram_model__DOT__bit_cnt = 0U;
                    if ((0x0bU == (0x0000000fU & (IData)(vlSelfRef.psram_model__DOT__cmd)))) {
                        __Vdly__psram_model__DOT__state = 2U;
                    } else if ((8U == (0x0000000fU 
                                       & (IData)(vlSelfRef.psram_model__DOT__cmd)))) {
                        __Vdly__psram_model__DOT__state = 5U;
                    }
                } else {
                    __Vdly__psram_model__DOT__bit_cnt 
                        = (0x000000ffU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
                }
            } else {
                __Vdly__psram_model__DOT__cmd = ((0x000000feU 
                                                  & ((IData)(vlSelfRef.psram_model__DOT__cmd) 
                                                     << 1U)) 
                                                 | (1U 
                                                    & (IData)(vlSelfRef.dq)));
                if ((7U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                    __Vdly__psram_model__DOT__bit_cnt = 0U;
                    if ((0x66U == (0x0000007fU & (IData)(vlSelfRef.psram_model__DOT__cmd)))) {
                        __Vdly__psram_model__DOT__state = 1U;
                    } else if ((0x35U == (0x0000007fU 
                                          & (IData)(vlSelfRef.psram_model__DOT__cmd)))) {
                        vlSelfRef.psram_model__DOT__qpi_mode = 1U;
                        __Vdly__psram_model__DOT__state = 9U;
                    } else if ((0x6bU == (0x0000007fU 
                                          & (IData)(vlSelfRef.psram_model__DOT__cmd)))) {
                        __Vdly__psram_model__DOT__state = 2U;
                    } else if ((0x38U == (0x0000007fU 
                                          & (IData)(vlSelfRef.psram_model__DOT__cmd)))) {
                        __Vdly__psram_model__DOT__state = 5U;
                    }
                } else {
                    __Vdly__psram_model__DOT__bit_cnt 
                        = (0x000000ffU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
                }
            }
        } else if ((1U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            __Vdly__psram_model__DOT__state = 0U;
        } else if ((2U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            __Vdly__psram_model__DOT__addr_r = ((0x00fffff0U 
                                                 & (vlSelfRef.psram_model__DOT__addr_r 
                                                    << 4U)) 
                                                | (IData)(vlSelfRef.dq));
            if ((5U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                __Vdly__psram_model__DOT__bit_cnt = 0U;
                __Vdly__psram_model__DOT__state = 3U;
            } else {
                __Vdly__psram_model__DOT__bit_cnt = 
                    (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
            }
        } else if ((3U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            if ((5U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                __Vdly__psram_model__DOT__bit_cnt = 0U;
                vlSelfRef.psram_model__DOT__dq_oe = 1U;
                __Vdly__psram_model__DOT__state = 4U;
            } else {
                __Vdly__psram_model__DOT__bit_cnt = 
                    (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
            }
        } else if ((4U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            vlSelfRef.psram_model__DOT__dq_r = (0x0000000fU 
                                                & (vlSelfRef.psram_model__DOT__mem
                                                   [
                                                   (0x000000ffU 
                                                    & vlSelfRef.psram_model__DOT__addr_r)] 
                                                   >> 
                                                   (7U 
                                                    & ((IData)(7U) 
                                                       - 
                                                       ((1U 
                                                         & (IData)(vlSelfRef.psram_model__DOT__bit_cnt))
                                                         ? 0U
                                                         : 4U)))));
            if ((3U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                vlSelfRef.psram_model__DOT__dq_oe = 0U;
                __Vdly__psram_model__DOT__state = 0U;
                __Vdly__psram_model__DOT__bit_cnt = 0U;
            } else {
                __Vdly__psram_model__DOT__bit_cnt = 
                    (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
            }
        } else if ((5U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            __Vdly__psram_model__DOT__addr_r = ((0x00fffff0U 
                                                 & (vlSelfRef.psram_model__DOT__addr_r 
                                                    << 4U)) 
                                                | (IData)(vlSelfRef.dq));
            if ((5U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                __Vdly__psram_model__DOT__bit_cnt = 0U;
                __Vdly__psram_model__DOT__state = 6U;
            } else {
                __Vdly__psram_model__DOT__bit_cnt = 
                    (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
            }
        } else if ((6U == (IData)(vlSelfRef.psram_model__DOT__state))) {
            __VdlyVal__psram_model__DOT__mem__v0 = 
                ((0x000000f0U & (vlSelfRef.psram_model__DOT__mem
                                 [(0x000000ffU & vlSelfRef.psram_model__DOT__addr_r)] 
                                 << 4U)) | (IData)(vlSelfRef.dq));
            __VdlyDim0__psram_model__DOT__mem__v0 = 
                (0x000000ffU & vlSelfRef.psram_model__DOT__addr_r);
            __VdlySet__psram_model__DOT__mem__v0 = 1U;
            if ((1U == (IData)(vlSelfRef.psram_model__DOT__bit_cnt))) {
                __Vdly__psram_model__DOT__state = 0U;
                __Vdly__psram_model__DOT__bit_cnt = 0U;
            } else {
                __Vdly__psram_model__DOT__bit_cnt = 
                    (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.psram_model__DOT__bit_cnt)));
            }
        } else {
            __Vdly__psram_model__DOT__state = 0U;
        }
    }
    vlSelfRef.psram_model__DOT__state = __Vdly__psram_model__DOT__state;
    vlSelfRef.psram_model__DOT__bit_cnt = __Vdly__psram_model__DOT__bit_cnt;
    vlSelfRef.psram_model__DOT__cmd = __Vdly__psram_model__DOT__cmd;
    vlSelfRef.psram_model__DOT__addr_r = __Vdly__psram_model__DOT__addr_r;
    if (__VdlySet__psram_model__DOT__mem__v0) {
        vlSelfRef.psram_model__DOT__mem[__VdlyDim0__psram_model__DOT__mem__v0] 
            = __VdlyVal__psram_model__DOT__mem__v0;
    }
    vlSelfRef.dq = (((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                      ? 0x0fU : 0U) & (((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                                         ? (IData)(vlSelfRef.psram_model__DOT__dq_r)
                                         : 0U) & ((IData)(vlSelfRef.psram_model__DOT__dq_oe)
                                                   ? 0x0fU
                                                   : 0U)));
}

void Vpsram_model___024root___eval_nba(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_nba\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((3ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vpsram_model___024root___nba_sequent__TOP__0(vlSelf);
    }
}

void Vpsram_model___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vpsram_model___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vpsram_model___024root___eval_phase__act(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_phase__act\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vpsram_model___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vpsram_model___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vpsram_model___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vpsram_model___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vpsram_model___024root___eval_phase__nba(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_phase__nba\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vpsram_model___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vpsram_model___024root___eval_nba(vlSelf);
        Vpsram_model___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vpsram_model___024root___eval(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vpsram_model___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_psram_tb.v", 4, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vpsram_model___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_psram_tb.v", 4, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vpsram_model___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vpsram_model___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vpsram_model___024root___eval_debug_assertions(Vpsram_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vpsram_model___024root___eval_debug_assertions\n"); );
    Vpsram_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.sck & 0xfeU)))) {
        Verilated::overWidthError("sck");
    }
    if (VL_UNLIKELY(((vlSelfRef.ce_n & 0xfeU)))) {
        Verilated::overWidthError("ce_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.dq & 0xf0U)))) {
        Verilated::overWidthError("dq");
    }
}
#endif  // VL_DEBUG
