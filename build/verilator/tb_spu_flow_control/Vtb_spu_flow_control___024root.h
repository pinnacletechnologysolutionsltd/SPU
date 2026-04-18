// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vtb_spu_flow_control.h for the primary calling header

#ifndef VERILATED_VTB_SPU_FLOW_CONTROL___024ROOT_H_
#define VERILATED_VTB_SPU_FLOW_CONTROL___024ROOT_H_  // guard

#include "verilated.h"


class Vtb_spu_flow_control__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vtb_spu_flow_control___024root final {
  public:

    // DESIGN SPECIFIC STATE
    CData/*0:0*/ tb_spu_flow_control__DOT__clk;
    CData/*0:0*/ tb_spu_flow_control__DOT__rst_n;
    CData/*0:0*/ tb_spu_flow_control__DOT__spi_cs_n;
    CData/*0:0*/ tb_spu_flow_control__DOT__spi_sck;
    CData/*0:0*/ tb_spu_flow_control__DOT__spi_mosi;
    CData/*0:0*/ tb_spu_flow_control__DOT__spi_miso;
    CData/*0:0*/ tb_spu_flow_control__DOT__fifo_full;
    CData/*2:0*/ tb_spu_flow_control__DOT__uut__DOT__sck_r;
    CData/*2:0*/ tb_spu_flow_control__DOT__uut__DOT__cs_r;
    CData/*1:0*/ tb_spu_flow_control__DOT__uut__DOT__mosi_r;
    CData/*3:0*/ tb_spu_flow_control__DOT__uut__DOT__snaps_lat;
    CData/*0:0*/ tb_spu_flow_control__DOT__uut__DOT__janus_lat;
    CData/*2:0*/ tb_spu_flow_control__DOT__uut__DOT__ratio_lat;
    CData/*0:0*/ tb_spu_flow_control__DOT__uut__DOT__ratio_valid_lat;
    CData/*5:0*/ tb_spu_flow_control__DOT__uut__DOT__resp_len;
    CData/*2:0*/ tb_spu_flow_control__DOT__uut__DOT__state;
    CData/*2:0*/ tb_spu_flow_control__DOT__uut__DOT__bit_cnt;
    CData/*7:0*/ tb_spu_flow_control__DOT__uut__DOT__cmd_byte;
    CData/*5:0*/ tb_spu_flow_control__DOT__uut__DOT__byte_idx;
    CData/*2:0*/ tb_spu_flow_control__DOT__uut__DOT__resp_bit;
    CData/*7:0*/ tb_spu_flow_control__DOT__uut__DOT__shift_out;
    CData/*5:0*/ tb_spu_flow_control__DOT__uut__DOT__recv_bits;
    CData/*0:0*/ __Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__clk__0;
    CData/*0:0*/ __VstlDidInit;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__tb_spu_flow_control__DOT__rst_n__0;
    CData/*0:0*/ __VactDidInit;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    SData/*15:0*/ tb_spu_flow_control__DOT__uut__DOT__dissonance_lat;
    SData/*12:0*/ tb_spu_flow_control__DOT__uut__DOT__scale_overflow_lat;
    IData/*31:0*/ __VactIterCount;
    QData/*51:0*/ tb_spu_flow_control__DOT__uut__DOT__scale_tab_lat;
    QData/*63:0*/ tb_spu_flow_control__DOT__uut__DOT__hdr_shift;
    QData/*63:0*/ tb_spu_flow_control__DOT__uut__DOT__data_shift;
    VlUnpacked<SData/*15:0*/, 4> tb_spu_flow_control__DOT__uut__DOT__p_axis;
    VlUnpacked<SData/*15:0*/, 4> tb_spu_flow_control__DOT__uut__DOT__q_axis;
    VlUnpacked<CData/*7:0*/, 32> tb_spu_flow_control__DOT__uut__DOT__resp_buf;
    VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vtb_spu_flow_control__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vtb_spu_flow_control___024root(Vtb_spu_flow_control__Syms* symsp, const char* namep);
    ~Vtb_spu_flow_control___024root();
    VL_UNCOPYABLE(Vtb_spu_flow_control___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
