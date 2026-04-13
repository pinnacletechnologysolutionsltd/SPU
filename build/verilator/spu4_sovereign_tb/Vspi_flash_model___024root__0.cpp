// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspi_flash_model.h for the primary calling header

#include "Vspi_flash_model__pch.h"

void Vspi_flash_model___024root___eval_triggers_vec__act(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_triggers_vec__act\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.sck) 
                                                     & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__sck__0)))));
    vlSelfRef.__Vtrigprevexpr___TOP__sck__0 = vlSelfRef.sck;
}

bool Vspi_flash_model___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___trigger_anySet__act\n"); );
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

void Vspi_flash_model___024root___nba_sequent__TOP__0(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___nba_sequent__TOP__0\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*2:0*/ __Vdly__spi_flash_model__DOT__state;
    __Vdly__spi_flash_model__DOT__state = 0;
    CData/*7:0*/ __Vdly__spi_flash_model__DOT__bit_cnt;
    __Vdly__spi_flash_model__DOT__bit_cnt = 0;
    IData/*23:0*/ __Vdly__spi_flash_model__DOT__addr;
    __Vdly__spi_flash_model__DOT__addr = 0;
    // Body
    __Vdly__spi_flash_model__DOT__state = vlSelfRef.spi_flash_model__DOT__state;
    __Vdly__spi_flash_model__DOT__bit_cnt = vlSelfRef.spi_flash_model__DOT__bit_cnt;
    __Vdly__spi_flash_model__DOT__addr = vlSelfRef.spi_flash_model__DOT__addr;
    if ((1U & (~ (IData)(vlSelfRef.cs_n)))) {
        if ((0U == (IData)(vlSelfRef.spi_flash_model__DOT__state))) {
            vlSelfRef.spi_flash_model__DOT__cmd = (
                                                   (0x000000feU 
                                                    & ((IData)(vlSelfRef.spi_flash_model__DOT__cmd) 
                                                       << 1U)) 
                                                   | (IData)(vlSelfRef.mosi));
            if ((7U == (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt))) {
                __Vdly__spi_flash_model__DOT__state = 1U;
                __Vdly__spi_flash_model__DOT__bit_cnt = 0U;
            } else {
                __Vdly__spi_flash_model__DOT__bit_cnt 
                    = (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)));
            }
        } else if ((1U == (IData)(vlSelfRef.spi_flash_model__DOT__state))) {
            __Vdly__spi_flash_model__DOT__addr = ((0x00fffffeU 
                                                   & (vlSelfRef.spi_flash_model__DOT__addr 
                                                      << 1U)) 
                                                  | (IData)(vlSelfRef.mosi));
            if ((0x17U == (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt))) {
                __Vdly__spi_flash_model__DOT__bit_cnt = 0U;
                __Vdly__spi_flash_model__DOT__state = 2U;
            } else {
                __Vdly__spi_flash_model__DOT__bit_cnt 
                    = (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)));
            }
        } else if ((2U == (IData)(vlSelfRef.spi_flash_model__DOT__state))) {
            vlSelfRef.miso = (1U & (vlSelfRef.spi_flash_model__DOT__data
                                    [(0x000000ffU & vlSelfRef.spi_flash_model__DOT__addr)] 
                                    >> (7U & ((IData)(7U) 
                                              - (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)))));
            if ((7U == (7U & (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)))) {
                __Vdly__spi_flash_model__DOT__addr 
                    = (0x00ffffffU & ((IData)(1U) + vlSelfRef.spi_flash_model__DOT__addr));
            }
            __Vdly__spi_flash_model__DOT__bit_cnt = 
                (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)));
        }
    }
    vlSelfRef.spi_flash_model__DOT__state = __Vdly__spi_flash_model__DOT__state;
    vlSelfRef.spi_flash_model__DOT__bit_cnt = __Vdly__spi_flash_model__DOT__bit_cnt;
    vlSelfRef.spi_flash_model__DOT__addr = __Vdly__spi_flash_model__DOT__addr;
}

void Vspi_flash_model___024root___eval_nba(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_nba\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*2:0*/ __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__state;
    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__state = 0;
    CData/*7:0*/ __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt;
    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt = 0;
    IData/*23:0*/ __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__addr;
    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__addr = 0;
    // Body
    if ((1ULL & vlSelfRef.__VnbaTriggered[0U])) {
        __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__state 
            = vlSelfRef.spi_flash_model__DOT__state;
        __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt 
            = vlSelfRef.spi_flash_model__DOT__bit_cnt;
        __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__addr 
            = vlSelfRef.spi_flash_model__DOT__addr;
        if ((1U & (~ (IData)(vlSelfRef.cs_n)))) {
            if ((0U == (IData)(vlSelfRef.spi_flash_model__DOT__state))) {
                vlSelfRef.spi_flash_model__DOT__cmd 
                    = ((0x000000feU & ((IData)(vlSelfRef.spi_flash_model__DOT__cmd) 
                                       << 1U)) | (IData)(vlSelfRef.mosi));
                if ((7U == (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt))) {
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__state = 1U;
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt = 0U;
                } else {
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt 
                        = (0x000000ffU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)));
                }
            } else if ((1U == (IData)(vlSelfRef.spi_flash_model__DOT__state))) {
                __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__addr 
                    = ((0x00fffffeU & (vlSelfRef.spi_flash_model__DOT__addr 
                                       << 1U)) | (IData)(vlSelfRef.mosi));
                if ((0x17U == (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt))) {
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt = 0U;
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__state = 2U;
                } else {
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt 
                        = (0x000000ffU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)));
                }
            } else if ((2U == (IData)(vlSelfRef.spi_flash_model__DOT__state))) {
                vlSelfRef.miso = (1U & (vlSelfRef.spi_flash_model__DOT__data
                                        [(0x000000ffU 
                                          & vlSelfRef.spi_flash_model__DOT__addr)] 
                                        >> (7U & ((IData)(7U) 
                                                  - (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)))));
                if ((7U == (7U & (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)))) {
                    __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__addr 
                        = (0x00ffffffU & ((IData)(1U) 
                                          + vlSelfRef.spi_flash_model__DOT__addr));
                }
                __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt 
                    = (0x000000ffU & ((IData)(1U) + (IData)(vlSelfRef.spi_flash_model__DOT__bit_cnt)));
            }
        }
        vlSelfRef.spi_flash_model__DOT__state = __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__state;
        vlSelfRef.spi_flash_model__DOT__bit_cnt = __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__bit_cnt;
        vlSelfRef.spi_flash_model__DOT__addr = __Vinline__nba_sequent__TOP__0___Vdly__spi_flash_model__DOT__addr;
    }
}

void Vspi_flash_model___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vspi_flash_model___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vspi_flash_model___024root___eval_phase__act(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_phase__act\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vspi_flash_model___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspi_flash_model___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vspi_flash_model___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vspi_flash_model___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vspi_flash_model___024root___eval_phase__nba(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_phase__nba\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vspi_flash_model___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vspi_flash_model___024root___eval_nba(vlSelf);
        Vspi_flash_model___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vspi_flash_model___024root___eval(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vspi_flash_model___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sovereign_tb.v", 4, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vspi_flash_model___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sovereign_tb.v", 4, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vspi_flash_model___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vspi_flash_model___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vspi_flash_model___024root___eval_debug_assertions(Vspi_flash_model___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspi_flash_model___024root___eval_debug_assertions\n"); );
    Vspi_flash_model__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.sck & 0xfeU)))) {
        Verilated::overWidthError("sck");
    }
    if (VL_UNLIKELY(((vlSelfRef.cs_n & 0xfeU)))) {
        Verilated::overWidthError("cs_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.mosi & 0xfeU)))) {
        Verilated::overWidthError("mosi");
    }
}
#endif  // VL_DEBUG
