// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vspu_spi_slave_tb.h for the primary calling header

#include "Vspu_spi_slave_tb__pch.h"

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_static(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_static\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vinline__eval_static__TOP_spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b;
    __Vinline__eval_static__TOP_spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0;
    // Body
    __Vinline__eval_static__TOP_spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0;
    vlSelfRef.__Vtrigprevexpr___TOP__spu_spi_slave_tb__DOT__clk__0 
        = vlSelfRef.spu_spi_slave_tb__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__spu_spi_slave_tb__DOT__rst_n__0 
        = vlSelfRef.spu_spi_slave_tb__DOT__rst_n;
}

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_static__TOP(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_static__TOP\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b;
    spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0;
    // Body
    spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0;
}

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_initial__TOP(Vspu_spi_slave_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_initial(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_initial\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vspu_spi_slave_tb___024root___eval_initial__TOP(vlSelf);
}

extern const VlWide<26>/*831:0*/ Vspu_spi_slave_tb__ConstPool__CONST_h571eb658_0;

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_initial__TOP(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_initial__TOP\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ spu_spi_slave_tb__DOT__pass_count;
    spu_spi_slave_tb__DOT__pass_count = 0;
    IData/*31:0*/ spu_spi_slave_tb__DOT__fail_count;
    spu_spi_slave_tb__DOT__fail_count = 0;
    IData/*31:0*/ spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b;
    spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0;
    IData/*31:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_transaction__0__n_bytes;
    __Vtask_spu_spi_slave_tb__DOT__spi_transaction__0__n_bytes = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv = 0;
    IData/*31:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_transaction__3__n_bytes;
    __Vtask_spu_spi_slave_tb__DOT__spi_transaction__3__n_bytes = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv = 0;
    IData/*31:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_transaction__6__n_bytes;
    __Vtask_spu_spi_slave_tb__DOT__spi_transaction__6__n_bytes = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd = 0;
    CData/*7:0*/ __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv = 0;
    // Body
    vlSelfRef.spu_spi_slave_tb__DOT__clk = 0U;
    spu_spi_slave_tb__DOT__pass_count = 0U;
    spu_spi_slave_tb__DOT__fail_count = 0U;
    VL_ASSIGN_W(832, vlSelfRef.spu_spi_slave_tb__DOT__manifold_state, Vspu_spi_slave_tb__ConstPool__CONST_h571eb658_0);
    vlSelfRef.spu_spi_slave_tb__DOT__manifold_state[0U] = 0x12340056U;
    vlSelfRef.spu_spi_slave_tb__DOT__manifold_state[1U] = 0xabcd0078U;
    vlSelfRef.spu_spi_slave_tb__DOT__satellite_snaps = 0x0aU;
    vlSelfRef.spu_spi_slave_tb__DOT__is_janus_point = 1U;
    vlSelfRef.spu_spi_slave_tb__DOT__dissonance = 0xbeefU;
    vlSelfRef.spu_spi_slave_tb__DOT__rst_n = 1U;
    __Vtask_spu_spi_slave_tb__DOT__spi_transaction__0__n_bytes = 0x00000020U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv = 0U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv 
        = ((1U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv)) 
           | (0x000000feU & ((- (IData)((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso))) 
                             << 1U)));
    vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 0U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv 
        = ((0xfeU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__1__recv)) 
           | (IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso));
    vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
    spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0U;
    while (VL_LTS_III(32, spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b, __Vtask_spu_spi_slave_tb__DOT__spi_transaction__0__n_bytes)) {
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd = 0U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv = 0;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 7U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0x7fU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 7U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 6U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xbfU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 6U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 5U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xdfU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 5U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 4U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xefU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 4U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 3U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xf7U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 3U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 2U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xfbU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 2U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd) 
                   >> 1U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xfdU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 1U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__cmd));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv 
            = ((0xfeU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv)) 
               | (IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[(0x0000001fU 
                                                 & spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b)] 
            = __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__2__recv;
        spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b 
            = ((IData)(1U) + spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b);
    }
    if (((((((((0x12U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[0U]) 
               & (0x34U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[1U])) 
              & (0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[2U])) 
             & (0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[3U])) 
            & (0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[4U])) 
           & (0x56U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[5U])) 
          & (0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[6U])) 
         & (0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[7U]))) {
        VL_WRITEF_NX("T1a PASS: axis0 bytes correct\n",0);
        spu_spi_slave_tb__DOT__pass_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__pass_count);
    } else {
        VL_WRITEF_NX("T1a FAIL: axis0 P=[%02h,%02h] Q=[%02h,%02h] expected 12,34,00,56\n",4
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[0U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[1U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[4U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[5U]);
        spu_spi_slave_tb__DOT__fail_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__fail_count);
    }
    if (((((0xabU == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[8U]) 
           & (0xcdU == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[9U])) 
          & (0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[12U])) 
         & (0x78U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[13U]))) {
        VL_WRITEF_NX("T1b PASS: axis1 bytes correct\n",0);
        spu_spi_slave_tb__DOT__pass_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__pass_count);
    } else {
        VL_WRITEF_NX("T1b FAIL: axis1 P=[%02h,%02h] Q=[%02h,%02h]\n",4
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[8U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[9U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[12U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[13U]);
        spu_spi_slave_tb__DOT__fail_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__fail_count);
    }
    __Vtask_spu_spi_slave_tb__DOT__spi_transaction__3__n_bytes = 3U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv = 0U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv 
        = ((1U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv)) 
           | (0x000000feU & ((- (IData)((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso))) 
                             << 1U)));
    vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 0U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv 
        = ((0xfeU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__4__recv)) 
           | (IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso));
    vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
    spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0U;
    while (VL_LTS_III(32, spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b, __Vtask_spu_spi_slave_tb__DOT__spi_transaction__3__n_bytes)) {
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd = 0U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv = 0;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 7U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0x7fU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 7U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 6U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xbfU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 6U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 5U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xdfU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 5U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 4U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xefU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 4U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 3U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xf7U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 3U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 2U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xfbU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 2U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd) 
                   >> 1U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xfdU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 1U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__cmd));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv 
            = ((0xfeU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv)) 
               | (IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[(0x0000001fU 
                                                 & spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b)] 
            = __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__5__recv;
        spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b 
            = ((IData)(1U) + spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b);
    }
    if ((((0xbeU == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[0U]) 
          & (0xefU == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[1U])) 
         & (2U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[2U]))) {
        VL_WRITEF_NX("T2 PASS: status bytes correct (dis=BEEF flags=02)\n",0);
        spu_spi_slave_tb__DOT__pass_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__pass_count);
    } else {
        VL_WRITEF_NX("T2 FAIL: [%02h,%02h,%02h] expected BE,EF,02\n",3
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[0U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[1U]
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[2U]);
        spu_spi_slave_tb__DOT__fail_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__fail_count);
    }
    __Vtask_spu_spi_slave_tb__DOT__spi_transaction__6__n_bytes = 1U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv = 0U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv 
        = ((1U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv)) 
           | (0x000000feU & ((- (IData)((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso))) 
                             << 1U)));
    vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 1U;
    __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv 
        = ((0xfeU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__7__recv)) 
           | (IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso));
    vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
    spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b = 0U;
    while (VL_LTS_III(32, spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b, __Vtask_spu_spi_slave_tb__DOT__spi_transaction__6__n_bytes)) {
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd = 0U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv = 0;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 7U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0x7fU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 7U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 6U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xbfU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 6U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 5U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xdfU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 5U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 4U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xefU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 4U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 3U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xf7U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 3U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 2U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xfbU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 2U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & ((IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd) 
                   >> 1U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xfdU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso) 
                  << 1U));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__spi_mosi = 
            (1U & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__cmd));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 1U;
        __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv 
            = ((0xfeU & (IData)(__Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv)) 
               | (IData)(vlSelfRef.spu_spi_slave_tb__DOT__spi_miso));
        vlSelfRef.spu_spi_slave_tb__DOT__spi_sck = 0U;
        vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[(0x0000001fU 
                                                 & spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b)] 
            = __Vtask_spu_spi_slave_tb__DOT__spi_byte_send__8__recv;
        spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b 
            = ((IData)(1U) + spu_spi_slave_tb__DOT__spi_transaction__Vstatic__b);
    }
    vlSelfRef.spu_spi_slave_tb__DOT__spi_cs_n = 1U;
    if ((0U == vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[0U])) {
        VL_WRITEF_NX("T3 PASS: unknown cmd returns 0x00\n",0);
        spu_spi_slave_tb__DOT__pass_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__pass_count);
    } else {
        VL_WRITEF_NX("T3 FAIL: expected 0x00 got %02h\n",1
                     , '#',8,vlSelfRef.spu_spi_slave_tb__DOT__rx_buf[0U]);
        spu_spi_slave_tb__DOT__fail_count = ((IData)(1U) 
                                             + spu_spi_slave_tb__DOT__fail_count);
    }
    if ((0U == spu_spi_slave_tb__DOT__fail_count)) {
        VL_WRITEF_NX("PASS\n",0);
    } else {
        VL_WRITEF_NX("FAIL (%0d failures)\n",1, '~',32,spu_spi_slave_tb__DOT__fail_count);
    }
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_spi_slave_tb.v", 163, "");
    VL_WRITEF_NX("FAIL (timeout)\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_spi_slave_tb.v", 167, "");
}

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_final(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_final\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_spi_slave_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vspu_spi_slave_tb___024root___eval_phase__stl(Vspu_spi_slave_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_settle(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_settle\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vspu_spi_slave_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/tests/spu_spi_slave_tb.v", 5, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vspu_spi_slave_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_triggers_vec__stl(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_triggers_vec__stl\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.spu_spi_slave_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__spu_spi_slave_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__spu_spi_slave_tb__DOT__clk__0 
        = vlSelfRef.spu_spi_slave_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vspu_spi_slave_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_spi_slave_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu_spi_slave_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu_spi_slave_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vspu_spi_slave_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___eval_stl(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_stl\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.spu_spi_slave_tb__DOT__clk = (1U 
                                                & (~ (IData)(vlSelfRef.spu_spi_slave_tb__DOT__clk)));
    }
}

VL_ATTR_COLD bool Vspu_spi_slave_tb___024root___eval_phase__stl(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___eval_phase__stl\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vspu_spi_slave_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vspu_spi_slave_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vspu_spi_slave_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vspu_spi_slave_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vspu_spi_slave_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vspu_spi_slave_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vspu_spi_slave_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] spu_spi_slave_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(posedge spu_spi_slave_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @(negedge spu_spi_slave_tb.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vspu_spi_slave_tb___024root___ctor_var_reset(Vspu_spi_slave_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vspu_spi_slave_tb___024root___ctor_var_reset\n"); );
    Vspu_spi_slave_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->spu_spi_slave_tb__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5019301607676864439ull);
    vlSelf->spu_spi_slave_tb__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8379177455515898752ull);
    vlSelf->spu_spi_slave_tb__DOT__spi_cs_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13467520668008408967ull);
    vlSelf->spu_spi_slave_tb__DOT__spi_sck = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4418821445497257343ull);
    vlSelf->spu_spi_slave_tb__DOT__spi_mosi = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6299000331066767805ull);
    vlSelf->spu_spi_slave_tb__DOT__spi_miso = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5861614886052524158ull);
    VL_SCOPED_RAND_RESET_W(832, vlSelf->spu_spi_slave_tb__DOT__manifold_state, __VscopeHash, 11619828542649672884ull);
    vlSelf->spu_spi_slave_tb__DOT__satellite_snaps = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 10830446045251615304ull);
    vlSelf->spu_spi_slave_tb__DOT__is_janus_point = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16655217744958656208ull);
    vlSelf->spu_spi_slave_tb__DOT__dissonance = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 8338856921180172848ull);
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->spu_spi_slave_tb__DOT__rx_buf[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 1214611389997184991ull);
    }
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__sck_r = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 18204085553626679842ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__cs_r = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 13327959677048847139ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__mosi_r = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2162853674682350328ull);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->spu_spi_slave_tb__DOT__dut__DOT__p_axis[__Vi0] = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11839418805818294787ull);
    }
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->spu_spi_slave_tb__DOT__dut__DOT__q_axis[__Vi0] = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 2102969675224159477ull);
    }
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__dissonance_lat = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14520670642959971348ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__snaps_lat = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 8331413879457863760ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__janus_lat = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17217757520351225978ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__scale_tab_lat = VL_SCOPED_RAND_RESET_Q(52, __VscopeHash, 6891093216981088661ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__scale_overflow_lat = VL_SCOPED_RAND_RESET_I(13, __VscopeHash, 6807695772703041255ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__ratio_lat = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 10196843115397945928ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__ratio_valid_lat = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1572103716438683399ull);
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->spu_spi_slave_tb__DOT__dut__DOT__resp_buf[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 12188153880998534819ull);
    }
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__resp_len = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 5339866993099119118ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 10745998342758154029ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__bit_cnt = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 6066373825312180443ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__cmd_byte = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 16198917739418587403ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__byte_idx = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 17814977761799159093ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__resp_bit = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 4164407320520572341ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__shift_out = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 17430154682422923960ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__recv_bits = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 17596837571866727977ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__hdr_shift = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 3556296487113811757ull);
    vlSelf->spu_spi_slave_tb__DOT__dut__DOT__data_shift = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 11457304881486547489ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu_spi_slave_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__spu_spi_slave_tb__DOT__rst_n__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
