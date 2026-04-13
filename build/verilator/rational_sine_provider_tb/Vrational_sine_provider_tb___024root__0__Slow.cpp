// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vrational_sine_provider_tb.h for the primary calling header

#include "Vrational_sine_provider_tb__pch.h"

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_static(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_static\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rational_sine_provider_tb__DOT__compute_s3__Vstatic__s = 0.0;
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_static__TOP(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_static__TOP\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rational_sine_provider_tb__DOT__compute_s3__Vstatic__s = 0.0;
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_initial__TOP(Vrational_sine_provider_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_initial(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_initial\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vrational_sine_provider_tb___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_initial__TOP(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_initial__TOP\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ rational_sine_provider_tb__DOT__i;
    rational_sine_provider_tb__DOT__i = 0;
    double rational_sine_provider_tb__DOT__sum16;
    rational_sine_provider_tb__DOT__sum16 = 0;
    double rational_sine_provider_tb__DOT__sum32;
    rational_sine_provider_tb__DOT__sum32 = 0;
    double rational_sine_provider_tb__DOT__max16;
    rational_sine_provider_tb__DOT__max16 = 0;
    double rational_sine_provider_tb__DOT__max32;
    rational_sine_provider_tb__DOT__max32 = 0;
    IData/*31:0*/ rational_sine_provider_tb__DOT__max_i16;
    rational_sine_provider_tb__DOT__max_i16 = 0;
    IData/*31:0*/ rational_sine_provider_tb__DOT__max_i32;
    rational_sine_provider_tb__DOT__max_i32 = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__Vfuncout;
    __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__Vfuncout = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__base_s;
    __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__base_s = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__1__x;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__1__x = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__2__x;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__2__x = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__3__x;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__3__x = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__Vfuncout;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__Vfuncout = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__x;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__x = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__5__x;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__5__x = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__Vfuncout;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__Vfuncout = 0;
    double __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__x;
    __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__x = 0;
    // Body
    rational_sine_provider_tb__DOT__sum16 = 0.0;
    rational_sine_provider_tb__DOT__sum32 = 0.0;
    rational_sine_provider_tb__DOT__max16 = 0.0;
    rational_sine_provider_tb__DOT__max32 = 0.0;
    rational_sine_provider_tb__DOT__max_i16 = 0xffffffffU;
    rational_sine_provider_tb__DOT__max_i32 = 0xffffffffU;
    VL_WRITEF_NX("idx\torig\trecon16\terr16\trecon32\terr32\n",0);
    rational_sine_provider_tb__DOT__i = 0U;
    while (VL_GTS_III(32, 0x00000100U, rational_sine_provider_tb__DOT__i)) {
        vlSelfRef.rational_sine_provider_tb__DOT__addr 
            = (0x00000fffU & rational_sine_provider_tb__DOT__i);
        __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__base_s 
            = (VL_ISTOR_D_I(32, rational_sine_provider_tb__DOT__i) 
               / 4.09600000000000000e+03);
        vlSelfRef.rational_sine_provider_tb__DOT__compute_s3__Vstatic__s 
            = __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__base_s;
        __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__Vfuncout 
            = ((vlSelfRef.rational_sine_provider_tb__DOT__compute_s3__Vstatic__s 
                * (3.0 - (4.0 * vlSelfRef.rational_sine_provider_tb__DOT__compute_s3__Vstatic__s))) 
               * (3.0 - (4.0 * vlSelfRef.rational_sine_provider_tb__DOT__compute_s3__Vstatic__s)));
        vlSelfRef.rational_sine_provider_tb__DOT__orig 
            = __Vfunc_rational_sine_provider_tb__DOT__compute_s3__0__Vfuncout;
        vlSelfRef.rational_sine_provider_tb__DOT__recon16 
            = ((VL_ISTOR_D_I(32, (((- (IData)((vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16 
                                               >> 0x0000001fU))) 
                                   << 0x00000010U) 
                                  | (vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16 
                                     >> 0x00000010U))) 
                / 3.27670000000000000e+04) + (1.73205080756887719e+00 
                                              * (VL_ISTOR_D_I(32, 
                                                              (((- (IData)(
                                                                           (1U 
                                                                            & (vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16 
                                                                               >> 0x0000000fU)))) 
                                                                << 0x00000010U) 
                                                               | (0x0000ffffU 
                                                                  & vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16))) 
                                                 / 3.27670000000000000e+04)));
        vlSelfRef.rational_sine_provider_tb__DOT__recon32 
            = ((VL_ISTOR_D_I(32, vlSelfRef.rational_sine_provider_tb__DOT__p32_out) 
                / 2.14748364700000000e+09) + (1.73205080756887719e+00 
                                              * (VL_ISTOR_D_I(32, vlSelfRef.rational_sine_provider_tb__DOT__q32_out) 
                                                 / 2.14748364700000000e+09)));
        vlSelfRef.rational_sine_provider_tb__DOT__err16 
            = (vlSelfRef.rational_sine_provider_tb__DOT__orig 
               - vlSelfRef.rational_sine_provider_tb__DOT__recon16);
        vlSelfRef.rational_sine_provider_tb__DOT__err32 
            = (vlSelfRef.rational_sine_provider_tb__DOT__orig 
               - vlSelfRef.rational_sine_provider_tb__DOT__recon32);
        __Vfunc_rational_sine_provider_tb__DOT__abs_r__1__x 
            = vlSelfRef.rational_sine_provider_tb__DOT__err16;
        vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_0__abs_r 
            = ((__Vfunc_rational_sine_provider_tb__DOT__abs_r__1__x 
                < 0.0) ? (- __Vfunc_rational_sine_provider_tb__DOT__abs_r__1__x)
                : __Vfunc_rational_sine_provider_tb__DOT__abs_r__1__x);
        rational_sine_provider_tb__DOT__sum16 = (rational_sine_provider_tb__DOT__sum16 
                                                 + vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_0__abs_r);
        __Vfunc_rational_sine_provider_tb__DOT__abs_r__2__x 
            = vlSelfRef.rational_sine_provider_tb__DOT__err32;
        vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_1__abs_r 
            = ((__Vfunc_rational_sine_provider_tb__DOT__abs_r__2__x 
                < 0.0) ? (- __Vfunc_rational_sine_provider_tb__DOT__abs_r__2__x)
                : __Vfunc_rational_sine_provider_tb__DOT__abs_r__2__x);
        rational_sine_provider_tb__DOT__sum32 = (rational_sine_provider_tb__DOT__sum32 
                                                 + vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_1__abs_r);
        __Vfunc_rational_sine_provider_tb__DOT__abs_r__3__x 
            = vlSelfRef.rational_sine_provider_tb__DOT__err16;
        vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_2__abs_r 
            = ((__Vfunc_rational_sine_provider_tb__DOT__abs_r__3__x 
                < 0.0) ? (- __Vfunc_rational_sine_provider_tb__DOT__abs_r__3__x)
                : __Vfunc_rational_sine_provider_tb__DOT__abs_r__3__x);
        if ((vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_2__abs_r 
             > rational_sine_provider_tb__DOT__max16)) {
            __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__x 
                = vlSelfRef.rational_sine_provider_tb__DOT__err16;
            __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__Vfuncout 
                = ((__Vfunc_rational_sine_provider_tb__DOT__abs_r__4__x 
                    < 0.0) ? (- __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__x)
                    : __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__x);
            rational_sine_provider_tb__DOT__max16 = __Vfunc_rational_sine_provider_tb__DOT__abs_r__4__Vfuncout;
            rational_sine_provider_tb__DOT__max_i16 
                = rational_sine_provider_tb__DOT__i;
        }
        __Vfunc_rational_sine_provider_tb__DOT__abs_r__5__x 
            = vlSelfRef.rational_sine_provider_tb__DOT__err32;
        vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_3__abs_r 
            = ((__Vfunc_rational_sine_provider_tb__DOT__abs_r__5__x 
                < 0.0) ? (- __Vfunc_rational_sine_provider_tb__DOT__abs_r__5__x)
                : __Vfunc_rational_sine_provider_tb__DOT__abs_r__5__x);
        if ((vlSelfRef.rational_sine_provider_tb__DOT____VlemCall_3__abs_r 
             > rational_sine_provider_tb__DOT__max32)) {
            __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__x 
                = vlSelfRef.rational_sine_provider_tb__DOT__err32;
            __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__Vfuncout 
                = ((__Vfunc_rational_sine_provider_tb__DOT__abs_r__6__x 
                    < 0.0) ? (- __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__x)
                    : __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__x);
            rational_sine_provider_tb__DOT__max32 = __Vfunc_rational_sine_provider_tb__DOT__abs_r__6__Vfuncout;
            rational_sine_provider_tb__DOT__max_i32 
                = rational_sine_provider_tb__DOT__i;
        }
        VL_WRITEF_NX("%0d\t%0f\t%0f\t%0f\t%0f\t%0f\n",6
                     , '~',32,rational_sine_provider_tb__DOT__i
                     , 'D',vlSelfRef.rational_sine_provider_tb__DOT__orig
                     , 'D',vlSelfRef.rational_sine_provider_tb__DOT__recon16
                     , 'D',vlSelfRef.rational_sine_provider_tb__DOT__err16
                     , 'D',vlSelfRef.rational_sine_provider_tb__DOT__recon32
                     , 'D',vlSelfRef.rational_sine_provider_tb__DOT__err32);
        rational_sine_provider_tb__DOT__i = ((IData)(1U) 
                                             + rational_sine_provider_tb__DOT__i);
    }
    VL_WRITEF_NX("Summary16: mean_err=%e max_err=%e idx=%0d\nSummary32: mean_err=%e max_err=%e idx=%0d\n",6
                 , 'D',(rational_sine_provider_tb__DOT__sum16 
                        / 256.0), 'D',rational_sine_provider_tb__DOT__max16
                 , '~',32,rational_sine_provider_tb__DOT__max_i16
                 , 'D',(rational_sine_provider_tb__DOT__sum32 
                        / 256.0), 'D',rational_sine_provider_tb__DOT__max32
                 , '~',32,rational_sine_provider_tb__DOT__max_i32);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_sine_provider_tb.v", 58, "");
    VL_READMEM_N(true, 32, 4096, 0, "hardware/common/rtl/gpu/rational_sine_4096.mem"s
                 ,  &(vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__rom16__DOT__rom)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 64, 4096, 0, "hardware/common/rtl/gpu/rational_sine_4096_q32.mem"s
                 ,  &(vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom)
                 , 0, ~0ULL);
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_final(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_final\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_sine_provider_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vrational_sine_provider_tb___024root___eval_phase__stl(Vrational_sine_provider_tb___024root* vlSelf);

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_settle(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_settle\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vrational_sine_provider_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/rational_sine_provider_tb.v", 2, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vrational_sine_provider_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_triggers_vec__stl(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_triggers_vec__stl\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
}

VL_ATTR_COLD bool Vrational_sine_provider_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vrational_sine_provider_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vrational_sine_provider_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vrational_sine_provider_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___stl_sequent__TOP__0(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___stl_sequent__TOP__0\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16 
        = vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__rom16__DOT__rom
        [vlSelfRef.rational_sine_provider_tb__DOT__addr];
    vlSelfRef.rational_sine_provider_tb__DOT__p32_out 
        = (IData)((vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom
                   [vlSelfRef.rational_sine_provider_tb__DOT__addr] 
                   >> 0x00000020U));
    vlSelfRef.rational_sine_provider_tb__DOT__q32_out 
        = (IData)(vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom
                  [vlSelfRef.rational_sine_provider_tb__DOT__addr]);
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___eval_stl(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_stl\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16 
            = vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__rom16__DOT__rom
            [vlSelfRef.rational_sine_provider_tb__DOT__addr];
        vlSelfRef.rational_sine_provider_tb__DOT__p32_out 
            = (IData)((vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom
                       [vlSelfRef.rational_sine_provider_tb__DOT__addr] 
                       >> 0x00000020U));
        vlSelfRef.rational_sine_provider_tb__DOT__q32_out 
            = (IData)(vlSelfRef.rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom
                      [vlSelfRef.rational_sine_provider_tb__DOT__addr]);
    }
}

VL_ATTR_COLD bool Vrational_sine_provider_tb___024root___eval_phase__stl(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___eval_phase__stl\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vrational_sine_provider_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vrational_sine_provider_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vrational_sine_provider_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vrational_sine_provider_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vrational_sine_provider_tb___024root___ctor_var_reset(Vrational_sine_provider_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vrational_sine_provider_tb___024root___ctor_var_reset\n"); );
    Vrational_sine_provider_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->rational_sine_provider_tb__DOT__addr = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 12614332462618992287ull);
    vlSelf->rational_sine_provider_tb__DOT__p32_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14182134340212235955ull);
    vlSelf->rational_sine_provider_tb__DOT__q32_out = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11828548360358097760ull);
    vlSelf->rational_sine_provider_tb__DOT__orig = 0;
    vlSelf->rational_sine_provider_tb__DOT__recon16 = 0;
    vlSelf->rational_sine_provider_tb__DOT__recon32 = 0;
    vlSelf->rational_sine_provider_tb__DOT__err16 = 0;
    vlSelf->rational_sine_provider_tb__DOT__err32 = 0;
    vlSelf->rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__dout16 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4046072201419667006ull);
    for (int __Vi0 = 0; __Vi0 < 4096; ++__Vi0) {
        vlSelf->rational_sine_provider_tb__DOT__PROVIDER16__DOT__gp_q16__DOT__rom16__DOT__rom[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5088210012562903419ull);
    }
    for (int __Vi0 = 0; __Vi0 < 4096; ++__Vi0) {
        vlSelf->rational_sine_provider_tb__DOT__PROVIDER32__DOT__gp_q32__DOT__rom_q32__DOT__rom[__Vi0] = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 3625428357264216851ull);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
}
