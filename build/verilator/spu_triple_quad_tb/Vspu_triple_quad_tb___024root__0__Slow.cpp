// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu_triple_quad_tb.h for the primary calling header

#include "Vspu_triple_quad_tb__pch.h"

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_static(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_static\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu_triple_quad_tb__DOT__fail = 0U;
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_static__TOP(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_static__TOP\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.spu_triple_quad_tb__DOT__fail = 0U;
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_initial__TOP(Vspu_triple_quad_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_initial(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_initial\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vspu_triple_quad_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_initial__TOP(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_initial__TOP\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__0__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__0__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__0__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__0__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__1__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__1__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__1__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__1__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__2__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__2__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__2__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__2__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__3__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__3__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__3__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__3__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__4__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__4__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__4__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__4__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__5__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__5__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__5__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__5__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__6__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__6__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__6__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__6__name);
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__7__got;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__got = 0;
    CData/*0:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__7__exp;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__exp = 0;
    VlWide<4>/*127:0*/ __Vtask_spu_triple_quad_tb__DOT__check1__7__name;
    VL_ZERO_W(128, __Vtask_spu_triple_quad_tb__DOT__check1__7__name);
    // Body
    __Vtask_spu_triple_quad_tb__DOT__check1__0__name[0U] = 0x322c3329U;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__name[1U] = 0x28332c31U;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__name[2U] = 0x65617220U;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__name[3U] = 0x6c6c696eU;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__exp = 1U;
    __Vtask_spu_triple_quad_tb__DOT__check1__0__got 
        = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
           == vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2);
    if (VL_UNLIKELY(((1U & (~ (IData)(__Vtask_spu_triple_quad_tb__DOT__check1__0__got)))))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__0__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__0__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__0__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    __Vtask_spu_triple_quad_tb__DOT__check1__1__name[0U] = 0x322c3329U;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__name[1U] = 0x28332c31U;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__name[2U] = 0x6c736520U;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__name[3U] = 0x74206661U;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__exp = 0U;
    __Vtask_spu_triple_quad_tb__DOT__check1__1__got 
        = vlSelfRef.spu_triple_quad_tb__DOT__tangent;
    if (VL_UNLIKELY((__Vtask_spu_triple_quad_tb__DOT__check1__1__got))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__1__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__1__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__1__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    __Vtask_spu_triple_quad_tb__DOT__check1__2__name[0U] = 0x332c3329U;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__name[1U] = 0x2028332cU;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__name[2U] = 0x616c7365U;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__name[3U] = 0x61722066U;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__exp = 0U;
    __Vtask_spu_triple_quad_tb__DOT__check1__2__got 
        = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
           == vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2);
    if (VL_UNLIKELY((__Vtask_spu_triple_quad_tb__DOT__check1__2__got))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__2__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__2__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__2__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    __Vtask_spu_triple_quad_tb__DOT__check1__3__name[0U] = 0x302c3029U;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__name[1U] = 0x2028302cU;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__name[2U] = 0x6e656172U;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__name[3U] = 0x6f6c6c69U;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__exp = 1U;
    __Vtask_spu_triple_quad_tb__DOT__check1__3__got 
        = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
           == vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2);
    if (VL_UNLIKELY(((1U & (~ (IData)(__Vtask_spu_triple_quad_tb__DOT__check1__3__got)))))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__3__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__3__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__3__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    __Vtask_spu_triple_quad_tb__DOT__check1__4__name[0U] = 0x302c3029U;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__name[1U] = 0x2028302cU;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__name[2U] = 0x67656e74U;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__name[3U] = 0x2074616eU;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__exp = 1U;
    __Vtask_spu_triple_quad_tb__DOT__check1__4__got 
        = vlSelfRef.spu_triple_quad_tb__DOT__tangent;
    if (VL_UNLIKELY(((1U & (~ (IData)(__Vtask_spu_triple_quad_tb__DOT__check1__4__got)))))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__4__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__4__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__4__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    __Vtask_spu_triple_quad_tb__DOT__check1__5__name[0U] = 0x342c3029U;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__name[1U] = 0x2028342cU;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__name[2U] = 0x6e656172U;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__name[3U] = 0x6f6c6c69U;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__exp = 1U;
    __Vtask_spu_triple_quad_tb__DOT__check1__5__got 
        = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
           == vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2);
    if (VL_UNLIKELY(((1U & (~ (IData)(__Vtask_spu_triple_quad_tb__DOT__check1__5__got)))))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__5__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__5__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__5__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    __Vtask_spu_triple_quad_tb__DOT__check1__6__name[0U] = 0x322c3329U;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__name[1U] = 0x2028312cU;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__name[2U] = 0x6e656172U;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__name[3U] = 0x6f6c6c69U;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__exp = 0U;
    __Vtask_spu_triple_quad_tb__DOT__check1__6__got 
        = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
           == vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2);
    if (VL_UNLIKELY((__Vtask_spu_triple_quad_tb__DOT__check1__6__got))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__6__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__6__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__6__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    vlSelfRef.spu_triple_quad_tb__DOT__Q1 = 4U;
    vlSelfRef.spu_triple_quad_tb__DOT__Q2 = 4U;
    vlSelfRef.spu_triple_quad_tb__DOT__Q3 = 0U;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__name[0U] = 0x51333d30U;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__name[1U] = 0x6561722bU;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__name[2U] = 0x6c6c696eU;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__name[3U] = 0x6e20636fU;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__exp = 1U;
    __Vtask_spu_triple_quad_tb__DOT__check1__7__got 
        = vlSelfRef.spu_triple_quad_tb__DOT__tangent;
    if (VL_UNLIKELY(((1U & (~ (IData)(__Vtask_spu_triple_quad_tb__DOT__check1__7__got)))))) {
        VL_WRITEF_NX("FAIL: %0s  got=%0b  exp=%0b\n",3
                     , '#',128,__Vtask_spu_triple_quad_tb__DOT__check1__7__name.data()
                     , '#',1,(IData)(__Vtask_spu_triple_quad_tb__DOT__check1__7__got)
                     , '#',1,__Vtask_spu_triple_quad_tb__DOT__check1__7__exp);
        vlSelfRef.spu_triple_quad_tb__DOT__fail = ((IData)(1U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    if ((0U == vlSelfRef.spu_triple_quad_tb__DOT__fail)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL (%0d failures)\n",1, '~',32,vlSelfRef.spu_triple_quad_tb__DOT__fail);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_triple_quad_tb.v", 93, "");
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_final(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_final\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_triple_quad_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu_triple_quad_tb___024root___eval_phase__stl(Vspu_triple_quad_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_settle(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_settle\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu_triple_quad_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_triple_quad_tb.v", 26, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu_triple_quad_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_triggers_vec__stl(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool Vspu_triple_quad_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_triple_quad_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu_triple_quad_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu_triple_quad_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___stl_sequent__TOP__0(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___stl_sequent__TOP__0\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*63:0*/ spu_triple_quad_tb__DOT__u_dut__DOT__sum;
    spu_triple_quad_tb__DOT__u_dut__DOT__sum = 0;
    // Body
    vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2 
        = VL_SHIFTL_QQI(64,64,32, (((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1)) 
                                    * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1))) 
                                   + (((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2)) 
                                       * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2))) 
                                      + ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3)) 
                                         * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3))))), 1U);
    spu_triple_quad_tb__DOT__u_dut__DOT__sum = ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1)) 
                                                + ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3)) 
                                                   + (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2))));
    vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
        = (spu_triple_quad_tb__DOT__u_dut__DOT__sum 
           * spu_triple_quad_tb__DOT__u_dut__DOT__sum);
    vlSelfRef.spu_triple_quad_tb__DOT__tangent = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
                                                  == 
                                                  (VL_SHIFTL_QQI(64,64,32, 
                                                                 ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1)) 
                                                                  * 
                                                                  ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3)) 
                                                                   * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2)))), 2U) 
                                                   + vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2));
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___eval_stl(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_stl\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    QData/*63:0*/ __Vinline__stl_sequent__TOP__0_spu_triple_quad_tb__DOT__u_dut__DOT__sum;
    __Vinline__stl_sequent__TOP__0_spu_triple_quad_tb__DOT__u_dut__DOT__sum = 0;
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2 
            = VL_SHIFTL_QQI(64,64,32, (((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1)) 
                                        * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1))) 
                                       + (((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2)) 
                                           * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2))) 
                                          + ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3)) 
                                             * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3))))), 1U);
        __Vinline__stl_sequent__TOP__0_spu_triple_quad_tb__DOT__u_dut__DOT__sum 
            = ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1)) 
               + ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3)) 
                  + (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2))));
        vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
            = (__Vinline__stl_sequent__TOP__0_spu_triple_quad_tb__DOT__u_dut__DOT__sum 
               * __Vinline__stl_sequent__TOP__0_spu_triple_quad_tb__DOT__u_dut__DOT__sum);
        vlSelfRef.spu_triple_quad_tb__DOT__tangent 
            = (vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__lhs 
               == (VL_SHIFTL_QQI(64,64,32, ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q1)) 
                                            * ((QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q3)) 
                                               * (QData)((IData)(vlSelfRef.spu_triple_quad_tb__DOT__Q2)))), 2U) 
                   + vlSelfRef.spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2));
    }
}

VL_ATTR_COLD bool Vspu_triple_quad_tb___024root___eval_phase__stl(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___eval_phase__stl\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu_triple_quad_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu_triple_quad_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu_triple_quad_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu_triple_quad_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vspu_triple_quad_tb___024root___ctor_var_reset(Vspu_triple_quad_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_triple_quad_tb___024root___ctor_var_reset\n"); );
    Vspu_triple_quad_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->spu_triple_quad_tb__DOT__Q1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12760217537810702281ull);
    vlSelf->spu_triple_quad_tb__DOT__Q2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7159109577038575536ull);
    vlSelf->spu_triple_quad_tb__DOT__Q3 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8599157102910198676ull);
    vlSelf->spu_triple_quad_tb__DOT__tangent = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6562592014482951548ull);
    vlSelf->spu_triple_quad_tb__DOT__u_dut__DOT__lhs = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 5613007688850710010ull);
    vlSelf->spu_triple_quad_tb__DOT__u_dut__DOT__rhs_sum2 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 12002321086703468757ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
}
