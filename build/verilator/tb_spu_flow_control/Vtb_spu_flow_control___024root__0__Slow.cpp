// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtb_spu_flow_control.h for the primary calling header

#include "Vtb_spu_flow_control__pch.h"

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_static(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_static\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*7:0*/ __Vinline__eval_static__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data;
    __Vinline__eval_static__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data = 0;
    // Body
    __Vinline__eval_static__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data = 0;
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0 
        = vlSelfRef.tb_spu_flow_control__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__rst_n__0 
        = vlSelfRef.tb_spu_flow_control__DOT__rst_n;
}

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_static__TOP(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_static__TOP\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*7:0*/ tb_spu_flow_control__DOT__read_bytes__Vstatic__data;
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data = 0;
    // Body
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data = 0;
}

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_initial(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_initial\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*7:0*/ __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data;
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data = 0;
    // Body
    vlSelfRef.tb_spu_flow_control__DOT__clk = 0U;
    vlSelfRef.tb_spu_flow_control__DOT__rst_n = 1U;
    VL_WRITEF_NX("--- Test 1: FIFO EMPTY ---\n",0);
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [0]: 0x%h\n",1, '#',8,__Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [1]: 0x%h\n",1, '#',8,__Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [2]: 0x%h\n--- Test 2: FIFO FULL ---\n",1
                 , '#',8,__Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    vlSelfRef.tb_spu_flow_control__DOT__fifo_full = 1U;
    vlSelfRef.tb_spu_flow_control__DOT__spi_mosi = 0U;
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [0]: 0x%h\n",1, '#',8,__Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [1]: 0x%h\n",1, '#',8,__Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    __Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    vlSelfRef.tb_spu_flow_control__DOT__spi_sck = 0U;
    VL_WRITEF_NX("Read byte [2]: 0x%h\n",1, '#',8,__Vinline__eval_initial__TOP_tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    vlSelfRef.tb_spu_flow_control__DOT__spi_cs_n = 1U;
    VL_WRITEF_NX("PASS: Flow control flags verified\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_flow_control.v", 100, "");
}

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_initial__TOP(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_initial__TOP\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*7:0*/ tb_spu_flow_control__DOT__read_bytes__Vstatic__data;
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data = 0;
    // Body
    vlSelfRef.tb_spu_flow_control__DOT__clk = 0U;
    vlSelfRef.tb_spu_flow_control__DOT__rst_n = 1U;
    VL_WRITEF_NX("--- Test 1: FIFO EMPTY ---\n",0);
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [0]: 0x%h\n",1, '#',8,tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [1]: 0x%h\n",1, '#',8,tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [2]: 0x%h\n--- Test 2: FIFO FULL ---\n",1
                 , '#',8,tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    vlSelfRef.tb_spu_flow_control__DOT__fifo_full = 1U;
    vlSelfRef.tb_spu_flow_control__DOT__spi_mosi = 0U;
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [0]: 0x%h\n",1, '#',8,tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    VL_WRITEF_NX("Read byte [1]: 0x%h\n",1, '#',8,tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    tb_spu_flow_control__DOT__read_bytes__Vstatic__data 
        = (0x000000ffU & (- (IData)((IData)(vlSelfRef.tb_spu_flow_control__DOT__spi_miso))));
    vlSelfRef.tb_spu_flow_control__DOT__spi_sck = 0U;
    VL_WRITEF_NX("Read byte [2]: 0x%h\n",1, '#',8,tb_spu_flow_control__DOT__read_bytes__Vstatic__data);
    vlSelfRef.tb_spu_flow_control__DOT__spi_cs_n = 1U;
    VL_WRITEF_NX("PASS: Flow control flags verified\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_flow_control.v", 100, "");
}

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_final(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_final\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_spu_flow_control___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vtb_spu_flow_control___024root___eval_phase__stl(Vtb_spu_flow_control___024root* vlSelf);

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_settle(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_settle\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vtb_spu_flow_control___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/tb_spu_flow_control.v", 4, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vtb_spu_flow_control___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_triggers_vec__stl(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_triggers_vec__stl\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.tb_spu_flow_control__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0 
        = vlSelfRef.tb_spu_flow_control__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vtb_spu_flow_control___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_spu_flow_control___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vtb_spu_flow_control___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] tb_spu_flow_control.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vtb_spu_flow_control___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vtb_spu_flow_control___024root___eval_stl(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_stl\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.tb_spu_flow_control__DOT__clk = (1U 
                                                   & (~ (IData)(vlSelfRef.tb_spu_flow_control__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vtb_spu_flow_control___024root___eval_phase__stl(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___eval_phase__stl\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vtb_spu_flow_control___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtb_spu_flow_control___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vtb_spu_flow_control___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vtb_spu_flow_control___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vtb_spu_flow_control___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_spu_flow_control___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vtb_spu_flow_control___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] tb_spu_flow_control.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge tb_spu_flow_control.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge tb_spu_flow_control.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vtb_spu_flow_control___024root___ctor_var_reset(Vtb_spu_flow_control___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_spu_flow_control___024root___ctor_var_reset\n"); );
    Vtb_spu_flow_control__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->tb_spu_flow_control__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16095907935521812317ull);
    vlSelf->tb_spu_flow_control__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1710229959834973858ull);
    vlSelf->tb_spu_flow_control__DOT__spi_cs_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14195088610200061916ull);
    vlSelf->tb_spu_flow_control__DOT__spi_sck = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14150929642287860266ull);
    vlSelf->tb_spu_flow_control__DOT__spi_mosi = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 55104936027122088ull);
    vlSelf->tb_spu_flow_control__DOT__spi_miso = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6761775918504990651ull);
    vlSelf->tb_spu_flow_control__DOT__fifo_full = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9333943191936051590ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__sck_r = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 10137003523600471295ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__cs_r = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 8563922691212693187ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__mosi_r = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 14575797011593146891ull);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->tb_spu_flow_control__DOT__uut__DOT__p_axis[__Vi0] = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 17931295591044315128ull);
    }
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->tb_spu_flow_control__DOT__uut__DOT__q_axis[__Vi0] = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9816173747470627735ull);
    }
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__dissonance_lat = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16389600602667932950ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__snaps_lat = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 16587536901325530123ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__janus_lat = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3469950572016764594ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat = VL_SCOPED_RAND_RESET_Q(52, __VscopeHash, 17880729556286539031ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__scale_overflow_lat = VL_SCOPED_RAND_RESET_I(13, __VscopeHash, 17329490166535327286ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__ratio_lat = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3872400083072234488ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__ratio_valid_lat = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18099569820419385064ull);
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->tb_spu_flow_control__DOT__uut__DOT__resp_buf[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 15358193646104779803ull);
    }
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__resp_len = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 6378118505203675457ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 2965395863824643747ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__bit_cnt = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 464467638430049018ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__cmd_byte = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 7580437030808342806ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__byte_idx = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 14981138400767689433ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__resp_bit = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3112063255572046216ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__shift_out = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 15325689186530797089ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__recv_bits = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 8300204973444396380ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__hdr_shift = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 13644843849298334821ull);
    vlSelf->tb_spu_flow_control__DOT__uut__DOT__data_shift = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 3510289685916501733ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
