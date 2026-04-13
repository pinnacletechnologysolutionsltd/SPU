// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrplu_tb.h for the primary calling header

#include "Vrplu_tb__pch.h"

VL_ATTR_COLD void Vrplu_tb___024root___eval_static(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_static\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rplu_tb__DOT__clk = 0U;
    vlSelfRef.rplu_tb__DOT__rst_n = 0U;
    vlSelfRef.rplu_tb__DOT__errors = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__rplu_tb__DOT__clk__0 = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__rplu_tb__DOT__rst_n__0 = 0U;
}

VL_ATTR_COLD void Vrplu_tb___024root___eval_static__TOP(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_static__TOP\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rplu_tb__DOT__clk = 0U;
    vlSelfRef.rplu_tb__DOT__rst_n = 0U;
    vlSelfRef.rplu_tb__DOT__errors = 0U;
}

VL_ATTR_COLD void Vrplu_tb___024root___eval_initial__TOP(Vrplu_tb___024root* vlSelf);

VL_ATTR_COLD void Vrplu_tb___024root___eval_initial(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_initial\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vrplu_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vrplu_tb___024root___eval_initial__TOP(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_initial__TOP\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ rplu_tb__DOT__i;
    rplu_tb__DOT__i = 0;
    // Body
    vlSelfRef.rplu_tb__DOT__rst_n = 1U;
    VL_READMEM_N(true, 64, 1024, 0, "hardware/common/rtl/gpu/rplu_rom_carbon.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__exp_carbon)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 64, 1024, 0, "hardware/common/rtl/gpu/rplu_rom_iron.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__exp_iron)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 1, 1024, 0, "hardware/common/rtl/gpu/rplu_dissoc_carbon.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__exp_diss_c)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 1, 1024, 0, "hardware/common/rtl/gpu/rplu_dissoc_iron.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__exp_diss_i)
                 , 0, ~0ULL);
    vlSelfRef.rplu_tb__DOT__start = 0U;
    vlSelfRef.rplu_tb__DOT__addr = 0U;
    rplu_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000400U, rplu_tb__DOT__i)) {
        vlSelfRef.rplu_tb__DOT__addr = (0x000003ffU 
                                        & rplu_tb__DOT__i);
        vlSelfRef.rplu_tb__DOT__start = 1U;
        vlSelfRef.rplu_tb__DOT__start = 0U;
        if (VL_UNLIKELY(((((vlSelfRef.rplu_tb__DOT__p_out 
                            != (IData)((vlSelfRef.rplu_tb__DOT__exp_carbon
                                        [(0x000003ffU 
                                          & rplu_tb__DOT__i)] 
                                        >> 0x20U))) 
                           | (vlSelfRef.rplu_tb__DOT__q_out 
                              != (IData)(vlSelfRef.rplu_tb__DOT__exp_carbon
                                         [(0x000003ffU 
                                           & rplu_tb__DOT__i)]))) 
                          | ((IData)(vlSelfRef.rplu_tb__DOT__dissoc) 
                             != vlSelfRef.rplu_tb__DOT__exp_diss_c
                             [(0x000003ffU & rplu_tb__DOT__i)]))))) {
            VL_WRITEF_NX("ERROR carbon[%0d]: got p=%0d q=%0d diss=%0d expected p=%0d q=%0d diss=%0d\n",7
                         , '~',32,rplu_tb__DOT__i, '~',32,vlSelfRef.rplu_tb__DOT__p_out
                         , '~',32,vlSelfRef.rplu_tb__DOT__q_out
                         , '#',1,(IData)(vlSelfRef.rplu_tb__DOT__dissoc)
                         , '~',32,(IData)((vlSelfRef.rplu_tb__DOT__exp_carbon
                                           [(0x000003ffU 
                                             & rplu_tb__DOT__i)] 
                                           >> 0x20U))
                         , '~',32,(IData)(vlSelfRef.rplu_tb__DOT__exp_carbon
                                          [(0x000003ffU 
                                            & rplu_tb__DOT__i)])
                         , '#',1,vlSelfRef.rplu_tb__DOT__exp_diss_c
                         [(0x000003ffU & rplu_tb__DOT__i)]);
            vlSelfRef.rplu_tb__DOT__errors = ((IData)(1U) 
                                              + vlSelfRef.rplu_tb__DOT__errors);
        }
        rplu_tb__DOT__i = ((IData)(1U) + rplu_tb__DOT__i);
    }
    vlSelfRef.rplu_tb__DOT__material_id = 1U;
    rplu_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000400U, rplu_tb__DOT__i)) {
        vlSelfRef.rplu_tb__DOT__addr = (0x000003ffU 
                                        & rplu_tb__DOT__i);
        vlSelfRef.rplu_tb__DOT__start = 1U;
        vlSelfRef.rplu_tb__DOT__start = 0U;
        if (VL_UNLIKELY(((((vlSelfRef.rplu_tb__DOT__p_out 
                            != (IData)((vlSelfRef.rplu_tb__DOT__exp_iron
                                        [(0x000003ffU 
                                          & rplu_tb__DOT__i)] 
                                        >> 0x20U))) 
                           | (vlSelfRef.rplu_tb__DOT__q_out 
                              != (IData)(vlSelfRef.rplu_tb__DOT__exp_iron
                                         [(0x000003ffU 
                                           & rplu_tb__DOT__i)]))) 
                          | ((IData)(vlSelfRef.rplu_tb__DOT__dissoc) 
                             != vlSelfRef.rplu_tb__DOT__exp_diss_i
                             [(0x000003ffU & rplu_tb__DOT__i)]))))) {
            VL_WRITEF_NX("ERROR iron[%0d]: got p=%0d q=%0d diss=%0d expected p=%0d q=%0d diss=%0d\n",7
                         , '~',32,rplu_tb__DOT__i, '~',32,vlSelfRef.rplu_tb__DOT__p_out
                         , '~',32,vlSelfRef.rplu_tb__DOT__q_out
                         , '#',1,(IData)(vlSelfRef.rplu_tb__DOT__dissoc)
                         , '~',32,(IData)((vlSelfRef.rplu_tb__DOT__exp_iron
                                           [(0x000003ffU 
                                             & rplu_tb__DOT__i)] 
                                           >> 0x20U))
                         , '~',32,(IData)(vlSelfRef.rplu_tb__DOT__exp_iron
                                          [(0x000003ffU 
                                            & rplu_tb__DOT__i)])
                         , '#',1,vlSelfRef.rplu_tb__DOT__exp_diss_i
                         [(0x000003ffU & rplu_tb__DOT__i)]);
            vlSelfRef.rplu_tb__DOT__errors = ((IData)(1U) 
                                              + vlSelfRef.rplu_tb__DOT__errors);
        }
        rplu_tb__DOT__i = ((IData)(1U) + rplu_tb__DOT__i);
    }
    if ((0U == vlSelfRef.rplu_tb__DOT__errors)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL: %0d errors\n",1, '~',32,vlSelfRef.rplu_tb__DOT__errors);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rplu_tb.v", 65, "");
    VL_READMEM_N(true, 64, 1024, 0, "hardware/common/rtl/gpu/rplu_rom_carbon.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__uut__DOT__rom_carbon)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 64, 1024, 0, "hardware/common/rtl/gpu/rplu_rom_iron.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__uut__DOT__rom_iron)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 1, 1024, 0, "hardware/common/rtl/gpu/rplu_dissoc_carbon.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__uut__DOT__diss_carbon)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 1, 1024, 0, "hardware/common/rtl/gpu/rplu_dissoc_iron.mem"s
                 ,  &(vlSelfRef.rplu_tb__DOT__uut__DOT__diss_iron)
                 , 0, ~0ULL);
    vlSelfRef.rplu_tb__DOT__p_out = 0U;
    vlSelfRef.rplu_tb__DOT__q_out = 0U;
    vlSelfRef.rplu_tb__DOT__dissoc = 0U;
}

VL_ATTR_COLD void Vrplu_tb___024root___eval_final(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_final\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrplu_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vrplu_tb___024root___eval_phase__stl(Vrplu_tb___024root* vlSelf);

VL_ATTR_COLD void Vrplu_tb___024root___eval_settle(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_settle\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vrplu_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rplu_tb.v", 2, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vrplu_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vrplu_tb___024root___eval_triggers_vec__stl(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_triggers_vec__stl\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.rplu_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rplu_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__rplu_tb__DOT__clk__0 
        = vlSelfRef.rplu_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vrplu_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrplu_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vrplu_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] rplu_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vrplu_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vrplu_tb___024root___eval_stl(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_stl\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.rplu_tb__DOT__clk = (1U & (~ (IData)(vlSelfRef.rplu_tb__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vrplu_tb___024root___eval_phase__stl(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___eval_phase__stl\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vrplu_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vrplu_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vrplu_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vrplu_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vrplu_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrplu_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vrplu_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] rplu_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge rplu_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge rplu_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vrplu_tb___024root___ctor_var_reset(Vrplu_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrplu_tb___024root___ctor_var_reset\n"); );
    Vrplu_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->rplu_tb__DOT__start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8229851492272888233ull);
    vlSelf->rplu_tb__DOT__addr = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 4876544299032626895ull);
    vlSelf->rplu_tb__DOT__material_id = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8877995502505384034ull);
    vlSelf->rplu_tb__DOT__p_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7335039635662714405ull);
    vlSelf->rplu_tb__DOT__q_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17086947593741665099ull);
    vlSelf->rplu_tb__DOT__dissoc = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10792090291217825253ull);
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__exp_carbon[__Vi0] = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 5456780459718482040ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__exp_iron[__Vi0] = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 16368187385872597651ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__exp_diss_c[__Vi0] = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2014364004574141073ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__exp_diss_i[__Vi0] = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8388449684859828498ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__uut__DOT__rom_carbon[__Vi0] = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 1370698494036371916ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__uut__DOT__rom_iron[__Vi0] = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 12234485123591380757ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__uut__DOT__diss_carbon[__Vi0] = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14537395175940996722ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1024; ++__Vi0) {
        vlSelf->rplu_tb__DOT__uut__DOT__diss_iron[__Vi0] = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9499919953235366499ull);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__rplu_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__rplu_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
