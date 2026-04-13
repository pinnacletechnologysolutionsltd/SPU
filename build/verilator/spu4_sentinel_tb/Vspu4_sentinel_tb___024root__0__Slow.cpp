// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu4_sentinel_tb.h for the primary calling header

#include "Vspu4_sentinel_tb__pch.h"

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_static(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_static\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0 
        = vlSelfRef.spu4_sentinel_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__rst_n__0 
        = vlSelfRef.spu4_sentinel_tb__DOT__rst_n;
}

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_initial(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_initial\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift;
    __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift = 0;
    IData/*31:0*/ __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__i;
    __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__i = 0;
    // Body
    vlSymsp->_vm_contextp__->dumpfile("sentinel_sqr.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v:45: $dumpvar ignored, as Verilated without --trace\n");
    vlSelfRef.spu4_sentinel_tb__DOT__clk = 0U;
    vlSelfRef.spu4_sentinel_tb__DOT__heartbeat = 0U;
    vlSelfRef.spu4_sentinel_tb__DOT__rst_n = 1U;
    VL_WRITEF_NX("--- [Sentinel SQR] Seeding Manifold ---\n    A=0000  B=1000  C=0000  D=0000\n    Mode: 60-degree Rational SQR (Q12)\n--- [Sentinel SQR] Beginning 1,000-Heartbeat Stress Test ---\n",0);
    __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x000003e9U, __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__i)) {
        vlSelfRef.spu4_sentinel_tb__DOT__heartbeat = 1U;
        vlSelfRef.spu4_sentinel_tb__DOT__heartbeat = 0U;
        __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__i 
            = ((IData)(1U) + __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__i);
    }
    VL_WRITEF_NX("--- [Sentinel SQR] Results after %0d heartbeats ---\n    Final:   A=%04x  B=%04x  C=%04x  D=%04x\n    Q_seed:  %08x\n    Q_now:   %08x\n",7
                 , '#',10,vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count
                 , '#',16,(IData)(vlSelfRef.spu4_sentinel_tb__DOT__A_out)
                 , '#',16,vlSelfRef.spu4_sentinel_tb__DOT__B_out
                 , '#',16,(IData)(vlSelfRef.spu4_sentinel_tb__DOT__C_out)
                 , '#',16,vlSelfRef.spu4_sentinel_tb__DOT__D_out
                 , '#',32,vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed
                 , '#',32,vlSelfRef.spu4_sentinel_tb__DOT__quadrance);
    __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift 
        = (vlSelfRef.spu4_sentinel_tb__DOT__quadrance 
           - vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed);
    if (VL_GTS_III(32, 0U, __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift)) {
        __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift 
            = (- __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift);
    }
    VL_WRITEF_NX("    |Drift|: %0d LSBs\n",1, '~',32,__Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift);
    if (VL_UNLIKELY((((0x03e8U == (IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count)) 
                      & VL_GTES_III(32, 0x00001000U, __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift))))) {
        VL_WRITEF_NX("[PASS] SQR Geometric Persistence VERIFIED. Janus Parity stable (drift <= 4096 LSB).\n",0);
    } else if (VL_LTS_III(32, 0x00001000U, __Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift)) {
        VL_WRITEF_NX("[FAIL] JANUS PARITY DRIFT DETECTED (%0d LSBs). SQR stiffness requires recalibration.\n",1
                     , '~',32,__Vinline__eval_initial__TOP_spu4_sentinel_tb__DOT__drift);
    } else {
        VL_WRITEF_NX("[WARN] Heartbeat count not reached: %0d/1000\n",1
                     , '#',10,vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v", 81, "");
}

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_initial__TOP(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_initial__TOP\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ spu4_sentinel_tb__DOT__drift;
    spu4_sentinel_tb__DOT__drift = 0;
    IData/*31:0*/ spu4_sentinel_tb__DOT__i;
    spu4_sentinel_tb__DOT__i = 0;
    // Body
    vlSymsp->_vm_contextp__->dumpfile("sentinel_sqr.vcd"s);
    VL_PRINTF_MT("-Info: /home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v:45: $dumpvar ignored, as Verilated without --trace\n");
    vlSelfRef.spu4_sentinel_tb__DOT__clk = 0U;
    vlSelfRef.spu4_sentinel_tb__DOT__heartbeat = 0U;
    vlSelfRef.spu4_sentinel_tb__DOT__rst_n = 1U;
    VL_WRITEF_NX("--- [Sentinel SQR] Seeding Manifold ---\n    A=0000  B=1000  C=0000  D=0000\n    Mode: 60-degree Rational SQR (Q12)\n--- [Sentinel SQR] Beginning 1,000-Heartbeat Stress Test ---\n",0);
    spu4_sentinel_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x000003e9U, spu4_sentinel_tb__DOT__i)) {
        vlSelfRef.spu4_sentinel_tb__DOT__heartbeat = 1U;
        vlSelfRef.spu4_sentinel_tb__DOT__heartbeat = 0U;
        spu4_sentinel_tb__DOT__i = ((IData)(1U) + spu4_sentinel_tb__DOT__i);
    }
    VL_WRITEF_NX("--- [Sentinel SQR] Results after %0d heartbeats ---\n    Final:   A=%04x  B=%04x  C=%04x  D=%04x\n    Q_seed:  %08x\n    Q_now:   %08x\n",7
                 , '#',10,vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count
                 , '#',16,(IData)(vlSelfRef.spu4_sentinel_tb__DOT__A_out)
                 , '#',16,vlSelfRef.spu4_sentinel_tb__DOT__B_out
                 , '#',16,(IData)(vlSelfRef.spu4_sentinel_tb__DOT__C_out)
                 , '#',16,vlSelfRef.spu4_sentinel_tb__DOT__D_out
                 , '#',32,vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed
                 , '#',32,vlSelfRef.spu4_sentinel_tb__DOT__quadrance);
    spu4_sentinel_tb__DOT__drift = (vlSelfRef.spu4_sentinel_tb__DOT__quadrance 
                                    - vlSelfRef.spu4_sentinel_tb__DOT__quadrance_seed);
    if (VL_GTS_III(32, 0U, spu4_sentinel_tb__DOT__drift)) {
        spu4_sentinel_tb__DOT__drift = (- spu4_sentinel_tb__DOT__drift);
    }
    VL_WRITEF_NX("    |Drift|: %0d LSBs\n",1, '~',32,spu4_sentinel_tb__DOT__drift);
    if (VL_UNLIKELY((((0x03e8U == (IData)(vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count)) 
                      & VL_GTES_III(32, 0x00001000U, spu4_sentinel_tb__DOT__drift))))) {
        VL_WRITEF_NX("[PASS] SQR Geometric Persistence VERIFIED. Janus Parity stable (drift <= 4096 LSB).\n",0);
    } else if (VL_LTS_III(32, 0x00001000U, spu4_sentinel_tb__DOT__drift)) {
        VL_WRITEF_NX("[FAIL] JANUS PARITY DRIFT DETECTED (%0d LSBs). SQR stiffness requires recalibration.\n",1
                     , '~',32,spu4_sentinel_tb__DOT__drift);
    } else {
        VL_WRITEF_NX("[WARN] Heartbeat count not reached: %0d/1000\n",1
                     , '#',10,vlSelfRef.spu4_sentinel_tb__DOT__heartbeat_count);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v", 81, "");
}

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_final(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_final\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_sentinel_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu4_sentinel_tb___024root___eval_phase__stl(Vspu4_sentinel_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_settle(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_settle\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu4_sentinel_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu4_sentinel_tb.v", 5, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu4_sentinel_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_triggers_vec__stl(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.spu4_sentinel_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0 
        = vlSelfRef.spu4_sentinel_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vspu4_sentinel_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_sentinel_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu4_sentinel_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu4_sentinel_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu4_sentinel_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___stl_sequent__TOP__1(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___stl_sequent__TOP__1\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
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
}

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___eval_stl(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_stl\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu4_sentinel_tb__DOT__clk = (1U 
                                                & (~ (IData)(vlSelfRef.spu4_sentinel_tb__DOT__clk)));
    }
    if ((1ULL & vlSelfRef.__VstlTriggered[1U])) {
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
    }
}

VL_ATTR_COLD bool Vspu4_sentinel_tb___024root___eval_phase__stl(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___eval_phase__stl\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu4_sentinel_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu4_sentinel_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu4_sentinel_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu4_sentinel_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vspu4_sentinel_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu4_sentinel_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu4_sentinel_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu4_sentinel_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge spu4_sentinel_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge spu4_sentinel_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vspu4_sentinel_tb___024root___ctor_var_reset(Vspu4_sentinel_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu4_sentinel_tb___024root___ctor_var_reset\n"); );
    Vspu4_sentinel_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->spu4_sentinel_tb__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10103016315524167479ull);
    vlSelf->spu4_sentinel_tb__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4526041362158842221ull);
    vlSelf->spu4_sentinel_tb__DOT__heartbeat = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7628073545808181405ull);
    vlSelf->spu4_sentinel_tb__DOT__A_out = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4329313331898268818ull);
    vlSelf->spu4_sentinel_tb__DOT__B_out = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15786911080659420922ull);
    vlSelf->spu4_sentinel_tb__DOT__C_out = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 17544017546741724844ull);
    vlSelf->spu4_sentinel_tb__DOT__D_out = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16027975985645544741ull);
    vlSelf->spu4_sentinel_tb__DOT__quadrance = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2968542112603743275ull);
    vlSelf->spu4_sentinel_tb__DOT__quadrance_seed = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11943950851720756792ull);
    vlSelf->spu4_sentinel_tb__DOT__heartbeat_count = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 13529880471079980292ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__seeded = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9209085104771151948ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_A = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 6926820491996253763ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_B = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4411355518479822906ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_C = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 8972110317996593417ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_D = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16575415207809494799ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7367307890225555363ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_seeding = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3031995012864957791ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_Q = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7951025141271551237ull);
    vlSelf->spu4_sentinel_tb__DOT__u_dut__DOT__p_henosis_needed = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14951751441343380180ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu4_sentinel_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
