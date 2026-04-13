// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspu4_precession_tb.h for the primary calling header

#ifndef VERILATED_VSPU4_PRECESSION_TB___024ROOT_H_
#define VERILATED_VSPU4_PRECESSION_TB___024ROOT_H_  // guard

#include "verilated.h"


class Vspu4_precession_tb__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspu4_precession_tb___024root final {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        CData/*0:0*/ spu4_precession_tb__DOT__clk;
        CData/*0:0*/ spu4_precession_tb__DOT__rst_n;
        CData/*3:0*/ spu4_precession_tb__DOT__uut__DOT__alu_op;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__rot_done;
        CData/*1:0*/ spu4_precession_tb__DOT__uut__DOT__state;
        CData/*1:0*/ spu4_precession_tb__DOT__uut__DOT__next_state;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__state_we;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__core_we;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__core_rot_start;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__7__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__6__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__5__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__4__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__3__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__2__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__1__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__sel_w__BRA__0__KET__;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mode_autonomous;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_start;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_done;
        CData/*3:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__state;
        CData/*3:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__sub_state;
        CData/*4:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__count;
        CData/*0:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__busy;
        CData/*2:0*/ __VdfgRegularize_h6e95ff9d_0_2;
        CData/*7:0*/ __VdfgRegularize_h6e95ff9d_0_3;
        CData/*0:0*/ __VdlySet__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__spu4_precession_tb__DOT__clk__0;
        CData/*0:0*/ __VstlDidInit;
        CData/*0:0*/ __VstlFirstIteration;
        CData/*0:0*/ __VstlPhaseResult;
        CData/*0:0*/ __Vtrigprevexpr___TOP__spu4_precession_tb__DOT__rst_n__0;
        CData/*0:0*/ __VactDidInit;
        CData/*0:0*/ __VactPhaseResult;
        CData/*0:0*/ __VnbaPhaseResult;
        SData/*9:0*/ spu4_precession_tb__DOT__uut__DOT__pc_reg;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__rot_a;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__rot_b;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__rot_c;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__rot_d;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_a;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_b;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__B_s;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__C_s;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__D_s;
        SData/*15:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__b_reg;
        SData/*15:0*/ __VdfgRegularize_h6e95ff9d_0_0;
        SData/*15:0*/ __VdfgRegularize_h6e95ff9d_0_1;
        IData/*31:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__mult_prod;
        IData/*17:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__accum;
        IData/*17:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__final_sum;
        IData/*31:0*/ spu4_precession_tb__DOT__uut__DOT__u_qrot_alu__DOT__u_mult__DOT__a_shifted;
        IData/*31:0*/ __VactIterCount;
        QData/*63:0*/ spu4_precession_tb__DOT__uut__DOT__core_din;
        QData/*63:0*/ spu4_precession_tb__DOT__uut__DOT__rplu_data;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v0;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v1;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v2;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v3;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v4;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v5;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v6;
        QData/*63:0*/ __VdlyVal__spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf__v7;
        VlUnpacked<IData/*23:0*/, 1024> spu4_precession_tb__DOT__prog_mem;
    };
    struct {
        VlUnpacked<QData/*63:0*/, 8> spu4_precession_tb__DOT__uut__DOT__u_regfile__DOT__rf;
        VlUnpacked<QData/*63:0*/, 2> __VstlTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    };

    // INTERNAL VARIABLES
    Vspu4_precession_tb__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspu4_precession_tb___024root(Vspu4_precession_tb__Syms* symsp, const char* namep);
    ~Vspu4_precession_tb___024root();
    VL_UNCOPYABLE(Vspu4_precession_tb___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
