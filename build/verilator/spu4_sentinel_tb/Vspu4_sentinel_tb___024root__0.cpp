// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu4_sentinel_tb.h for the primary calling header

#include "Vspu4_sentinel_tb__pch.h"

void Vspu4_sentinel_tb___024root___eval_triggers_vec__act(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_triggers_vec__act\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((((~ (IData)(vlSelfRef.spu4_sentinel_tb__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__rst_n__0)) 
                                                      << 2U) 
                                                     | ((((IData)(vlSelfRef.spu4_sentinel_tb__DOT__clk) 
                                                          & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0))) 
                                                         << 1U) 
                                                        | ((IData)(vlSelfRef.spu4_sentinel_tb__DOT__clk) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0 
        = vlSelfRef.spu4_sentinel_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__rst_n__0 
        = vlSelfRef.spu4_sentinel_tb__DOT__rst_n;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VactDidInit)))))) {
        vlSelfRef.__VactDidInit = 1U;
        vlSelfRef.__VactTriggered[0U] = (1ULL | vlSelfRef.__VactTriggered[0U]);
    }
}

bool Vspu4_sentinel_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___trigger_anySet__act\n"); );
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

void Vspu4_sentinel_tb___024root___act_sequent__TOP__0(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___act_sequent__TOP__0\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu4_sentinel_tb__DOT__clk = (1U & (~ (IData)(vlSelfRef.spu4_sentinel_tb__DOT__clk)));
}

void Vspu4_sentinel_tb___024root___eval_act(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_act\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VactTriggered[0U])) {
        vlSelfRef.spu4_sentinel_tb__DOT__clk = (1U 
                                                & (~ (IData)(vlSelfRef.spu4_sentinel_tb__DOT__clk)));
    }
}

void Vspu4_sentinel_tb___024root___nba_sequent__TOP__0(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___nba_sequent__TOP__0\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    SData/*15:0*/ __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_A;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_A = 0;
    CData/*0:0*/ __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding = 0;
    SData/*15:0*/ __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C = 0;
    SData/*15:0*/ __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B = 0;
    SData/*15:0*/ __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D = 0;
    SData/*9:0*/ __Vdly__spu4_sentinel_tb__DOT__heartbeat_count;
    __Vdly__spu4_sentinel_tb__DOT__heartbeat_count = 0;
    // Body
    __Vdly__spu4_sentinel_tb__DOT__heartbeat_count 
        = vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding 
        = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_A 
        = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_A;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C 
        = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B 
        = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B;
    __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D 
        = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D;
    if (vlSelfRef.spu4_sentinel_tb__DOT__rst_n) {
        __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding = 0U;
        if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_valid) {
            if ((1U & (~ (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding)))) {
                __Vdly__spu4_sentinel_tb__DOT__heartbeat_count 
                    = (0x000003ffU & ((IData)(1U) + (IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count)));
                vlSelfRef.spu4_sentinel_tb__DOT__quadrance 
                    = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_Q;
            }
            if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding) {
                vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed 
                    = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_Q;
            }
        }
        if (((IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat) 
             & (0x03e8U >= (IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count)))) {
            if ((1U & (~ (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__seeded)))) {
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding = 1U;
            }
            __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_A 
                = ((IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__seeded)
                    ? (IData)(vlSelfRef.spu4_sentinel_tb__DOT__A_out)
                    : 0U);
        }
        if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_valid) {
            vlSelfRef.spu4_sentinel_tb__DOT__A_out 
                = vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_A;
        }
        if (((IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat) 
             & (0x03e8U >= (IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count)))) {
            if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__seeded) {
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C 
                    = (0x0000ffffU & (IData)((0x0000000fffffffffULL 
                                              & ((VL_MULS_QQQ(48, 0x0000000000000aabULL, 
                                                              (0x0000ffffffffffffULL 
                                                               & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__B_out)))) 
                                                  + 
                                                  (VL_MULS_QQQ(48, 0x0000000000000aabULL, 
                                                               (0x0000ffffffffffffULL 
                                                                & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__C_out)))) 
                                                   + 
                                                   VL_MULS_QQQ(48, 0x0000fffffffffaabULL, 
                                                               (0x0000ffffffffffffULL 
                                                                & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__D_out)))))) 
                                                 >> 0x0000000cU))));
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B 
                    = (0x0000ffffU & (IData)((0x0000000fffffffffULL 
                                              & ((VL_MULS_QQQ(48, 0x0000000000000aabULL, 
                                                              (0x0000ffffffffffffULL 
                                                               & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__B_out)))) 
                                                  + 
                                                  (VL_MULS_QQQ(48, 0x0000fffffffffaabULL, 
                                                               (0x0000ffffffffffffULL 
                                                                & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__C_out)))) 
                                                   + 
                                                   VL_MULS_QQQ(48, 0x0000000000000aabULL, 
                                                               (0x0000ffffffffffffULL 
                                                                & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__D_out)))))) 
                                                 >> 0x0000000cU))));
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D 
                    = (0x0000ffffU & (IData)((0x0000000fffffffffULL 
                                              & ((VL_MULS_QQQ(48, 0x0000fffffffffaabULL, 
                                                              (0x0000ffffffffffffULL 
                                                               & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__B_out)))) 
                                                  + 
                                                  (VL_MULS_QQQ(48, 0x0000000000000aabULL, 
                                                               (0x0000ffffffffffffULL 
                                                                & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__D_out)))) 
                                                   + 
                                                   VL_MULS_QQQ(48, 0x0000000000000aabULL, 
                                                               (0x0000ffffffffffffULL 
                                                                & VL_EXTENDS_QI(48,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__C_out)))))) 
                                                 >> 0x0000000cU))));
            } else {
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C = 0U;
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B = 0x00001000U;
                __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D = 0U;
            }
        }
        if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_valid) {
            if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding) {
                vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__seeded = 1U;
                vlSelfRef.spu4_sentinel_tb__DOT__B_out 
                    = (0x0000ffffU & (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B));
                vlSelfRef.spu4_sentinel_tb__DOT__D_out 
                    = (0x0000ffffU & (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D));
                vlSelfRef.spu4_sentinel_tb__DOT__C_out 
                    = (0x0000ffffU & (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C));
            } else if (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_henosis_needed) {
                vlSelfRef.spu4_sentinel_tb__DOT__B_out 
                    = (0x0000ffffU & VL_SHIFTRS_III(16,16,32, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B), 1U));
                vlSelfRef.spu4_sentinel_tb__DOT__D_out 
                    = (0x0000ffffU & VL_SHIFTRS_III(16,16,32, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D), 1U));
                vlSelfRef.spu4_sentinel_tb__DOT__C_out 
                    = (0x0000ffffU & VL_SHIFTRS_III(16,16,32, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C), 1U));
            } else {
                vlSelfRef.spu4_sentinel_tb__DOT__B_out 
                    = (0x0000ffffU & (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B));
                vlSelfRef.spu4_sentinel_tb__DOT__D_out 
                    = (0x0000ffffU & (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D));
                vlSelfRef.spu4_sentinel_tb__DOT__C_out 
                    = (0x0000ffffU & (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C));
            }
        }
        vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_valid = 0U;
        if (((IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat) 
             & (0x03e8U >= (IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count)))) {
            vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_valid = 1U;
        }
    } else {
        __Vdly__spu4_sentinel_tb__DOT__heartbeat_count = 0U;
        __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding = 0U;
        __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_A = 0U;
        __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C = 0U;
        __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B = 0U;
        __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__quadrance = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__A_out = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__seeded = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__B_out = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__D_out = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__C_out = 0U;
        vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_valid = 0U;
    }
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_A 
        = __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_A;
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B 
        = __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_B;
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D 
        = __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_D;
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding 
        = __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding;
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C 
        = __Vdly__spu4_sentinel_tb__DOT__u_dut__DOT__p_C;
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_Q 
        = (VL_MULS_III(32, VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_A)), 
                       VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_A))) 
           + (VL_MULS_III(32, VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B)), 
                          VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_B))) 
              + (VL_MULS_III(32, VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C)), 
                             VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_C))) 
                 + VL_MULS_III(32, VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D)), 
                               VL_EXTENDS_II(32,16, (IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_D))))));
    vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_henosis_needed 
        = ((IData)(vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__seeded) 
           & (vlSelfRef.spu4_sentinel_tb__DOT__u_dut__DOT__p_Q 
              > VL_SHIFTL_III(32,32,32, vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed, 1U)));
    vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count 
        = __Vdly__spu4_sentinel_tb__DOT__heartbeat_count;
}

void Vspu4_sentinel_tb___024root___eval_nba(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_nba\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((6ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vspu4_sentinel_tb___024root___nba_sequent__TOP__0(vlSelf);
    }
}

void Vspu4_sentinel_tb___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___trigger_orInto__act_vec_vec\n"); );
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
VL_ATTR_COLD void Vspu4_sentinel_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vspu4_sentinel_tb___024root___eval_phase__act(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_phase__act\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VactExecute;
    // Body
    Vspu4_sentinel_tb___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu4_sentinel_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vspu4_sentinel_tb___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    __VactExecute = Vspu4_sentinel_tb___024root___trigger_anySet__act(vlSelfRef.__VactTriggered);
    if (__VactExecute) {
        Vspu4_sentinel_tb___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vspu4_sentinel_tb___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vspu4_sentinel_tb___024root___eval_phase__nba(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_phase__nba\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vspu4_sentinel_tb___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vspu4_sentinel_tb___024root___eval_nba(vlSelf);
        Vspu4_sentinel_tb___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vspu4_sentinel_tb___024root___eval(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vspu4_sentinel_tb___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v", 5, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vspu4_sentinel_tb___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v", 5, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vspu4_sentinel_tb___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vspu4_sentinel_tb___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vspu4_sentinel_tb___024root___eval_debug_assertions(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_debug_assertions\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
