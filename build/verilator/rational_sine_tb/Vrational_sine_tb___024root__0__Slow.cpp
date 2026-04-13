// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrational_sine_tb.h for the primary calling header

#include "Vrational_sine_tb__pch.h"

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_static(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_static\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_initial__TOP(Vrational_sine_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_initial(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_initial\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vrational_sine_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_initial__TOP(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_initial__TOP\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    VL_WRITEF_NX("addr\tword_hex\tp16\tq16\tvalue_approx\n0\t%08x\t%0d\t%0d\t%0f\n1\t%08x\t%0d\t%0d\t%0f\n2\t%08x\t%0d\t%0d\t%0f\n3\t%08x\t%0d\t%0d\t%0f\n4\t%08x\t%0d\t%0d\t%0f\n5\t%08x\t%0d\t%0d\t%0f\n6\t%08x\t%0d\t%0d\t%0f\n7\t%08x\t%0d\t%0d\t%0f\n8\t%08x\t%0d\t%0d\t%0f\n9\t%08x\t%0d\t%0d\t%0f\n10\t%08x\t%0d\t%0d\t%0f\n11\t%08x\t%0d\t%0d\t%0f\n12\t%08x\t%0d\t%0d\t%0f\n13\t%08x\t%0d\t%0d\t%0f\n14\t%08x\t%0d\t%0d\t%0f\n",60
                 , '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04), '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04));
    vlSelfRef.rational_sine_tb__DOT__addr = 0x000fU;
    VL_WRITEF_NX("15\t%08x\t%0d\t%0d\t%0f\n",4, '#',32,vlSelfRef.rational_sine_tb__DOT__dout
                 , '~',16,(vlSelfRef.rational_sine_tb__DOT__dout 
                           >> 0x10U), '~',16,vlSelfRef.rational_sine_tb__DOT__dout
                 , 'D',(VL_ISTOR_D_I(16, (vlSelfRef.rational_sine_tb__DOT__dout 
                                          >> 0x10U)) 
                        / 3.27670000000000000e+04));
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_sine_tb.v", 16, "");
    VL_READMEM_N(true, 32, 4096, 0, "hardware/common/rtl/gpu/rational_sine_4096.mem"s
                 ,  &(vlSelfRef.rational_sine_tb__DOT__UUT__DOT__rom)
                 , 0, ~0ULL);
}

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_final(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_final\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_sine_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vrational_sine_tb___024root___eval_phase__stl(Vrational_sine_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_settle(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_settle\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vrational_sine_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_sine_tb.v", 2, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vrational_sine_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_triggers_vec__stl(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_triggers_vec__stl\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool Vrational_sine_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_sine_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vrational_sine_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vrational_sine_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vrational_sine_tb___024root___stl_sequent__TOP__0(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___stl_sequent__TOP__0\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rational_sine_tb__DOT__dout = vlSelfRef.rational_sine_tb__DOT__UUT__DOT__rom
        [vlSelfRef.rational_sine_tb__DOT__addr];
}

VL_ATTR_COLD void Vrational_sine_tb___024root___eval_stl(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_stl\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.rational_sine_tb__DOT__dout = vlSelfRef.rational_sine_tb__DOT__UUT__DOT__rom
            [vlSelfRef.rational_sine_tb__DOT__addr];
    }
}

VL_ATTR_COLD bool Vrational_sine_tb___024root___eval_phase__stl(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___eval_phase__stl\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vrational_sine_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vrational_sine_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vrational_sine_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vrational_sine_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vrational_sine_tb___024root___ctor_var_reset(Vrational_sine_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_tb___024root___ctor_var_reset\n"); );
    Vrational_sine_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->rational_sine_tb__DOT__addr = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 6189816785004040396ull);
    vlSelf->rational_sine_tb__DOT__dout = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15494928863076883700ull);
    for (int __Vi0 = 0; __Vi0 < 4096; ++__Vi0) {
        vlSelf->rational_sine_tb__DOT__UUT__DOT__rom[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13708657060058478703ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
}
