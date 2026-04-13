// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vgpu_pipeline_tb.h for the primary calling header

#ifndef VERILATED_VGPU_PIPELINE_TB___024ROOT_H_
#define VERILATED_VGPU_PIPELINE_TB___024ROOT_H_  // guard

#include "verilated.h"
class Vgpu_pipeline_tb___024unit;


class Vgpu_pipeline_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vgpu_pipeline_tb___024root final {
  public:
    // CELLS
    Vgpu_pipeline_tb___024unit* __PVT____024unit;

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        CData/*0:0*/ gpu_pipeline_tb__DOT__clk;
        CData/*0:0*/ gpu_pipeline_tb__DOT__reset;
        CData/*0:0*/ gpu_pipeline_tb__DOT__spi_sck;
        CData/*0:0*/ gpu_pipeline_tb__DOT__spi_mosi;
        CData/*0:0*/ gpu_pipeline_tb__DOT__display_ready;
        CData/*3:0*/ gpu_pipeline_tb__DOT__psram_dq__en1;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_miso;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en;
        CData/*7:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_data;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_ready;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_valid;
        CData/*2:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state;
        CData/*5:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt;
        CData/*1:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state;
        CData/*3:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt;
        CData/*2:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt;
        CData/*3:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state;
        CData/*1:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane;
        CData/*1:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state;
        CData/*3:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state;
        CData/*5:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt;
        CData/*3:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out;
        CData/*0:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe;
        CData/*1:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state;
        CData/*1:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state;
        CData/*3:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt;
        CData/*2:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt;
        CData/*0:0*/ __Vdly__gpu_pipeline_tb__DOT__spi_sck;
        CData/*0:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready;
        CData/*0:0*/ __Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0;
        CData/*0:0*/ __VstlDidInit;
        CData/*0:0*/ __VstlFirstIteration;
        CData/*0:0*/ __VstlPhaseResult;
        CData/*0:0*/ __Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__display_ready__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__reset__0;
        CData/*0:0*/ __VactDidInit;
        CData/*0:0*/ __VactPhaseResult;
        CData/*0:0*/ __VnbaPhaseResult;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10;
        SData/*12:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__rem_quadrays;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer;
        SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__rem_len;
        SData/*15:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch;
        SData/*15:0*/ __Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg;
        IData/*22:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_addr;
        IData/*22:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__pour_psram_addr;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2;
        VlWide<4>/*127:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x;
    };
    struct {
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y;
        IData/*23:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_storage_addr;
        IData/*22:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_psram_addr;
        IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg;
        IData/*22:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__current_addr;
        IData/*31:0*/ __VactIterCount;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2;
        QData/*63:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area;
        VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    };

    // INTERNAL VARIABLES
    Vgpu_pipeline_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vgpu_pipeline_tb___024root(Vgpu_pipeline_tb__Syms* symsp, const char* namep);
    ~Vgpu_pipeline_tb___024root();
    VL_UNCOPYABLE(Vgpu_pipeline_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
