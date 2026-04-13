// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vgpu_pipeline_tb.h for the primary calling header

#include "Vgpu_pipeline_tb__pch.h"

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_static(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_static\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.gpu_pipeline_tb__DOT__clk = 0U;
    vlSelfRef.gpu_pipeline_tb__DOT__reset = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0 = 0U;
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__display_ready__0 
        = vlSelfRef.gpu_pipeline_tb__DOT__display_ready;
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__reset__0 = 0U;
}

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_static__TOP(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_static__TOP\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.gpu_pipeline_tb__DOT__clk = 0U;
    vlSelfRef.gpu_pipeline_tb__DOT__reset = 0U;
}

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_initial(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_initial\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSymsp->TOP____024unit.__VmonitorNum = 1U;
    vlSelfRef.gpu_pipeline_tb__DOT__reset = 0U;
    VL_WRITEF_NX("--- Simulation Finished ---\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/rtl/tb/gpu_pipeline_tb.v", 85, "");
}

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_initial__TOP(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_initial__TOP\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSymsp->TOP____024unit.__VmonitorNum = 1U;
    vlSelfRef.gpu_pipeline_tb__DOT__reset = 0U;
    VL_WRITEF_NX("--- Simulation Finished ---\n",0);
    VL_FINISH_MT("/home/john/projects/hardware/SPU/hardware/common/rtl/tb/gpu_pipeline_tb.v", 85, "");
}

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_final(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_final\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vgpu_pipeline_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vgpu_pipeline_tb___024root___eval_phase__stl(Vgpu_pipeline_tb___024root* vlSelf);

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_settle(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_settle\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vgpu_pipeline_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/home/john/projects/hardware/SPU/hardware/common/rtl/tb/gpu_pipeline_tb.v", 9, "", "DIDNOTCONVERGE: Settle region did not converge after '--converge-limit' of 10000 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        vlSelfRef.__VstlPhaseResult = Vgpu_pipeline_tb___024root___eval_phase__stl(vlSelf);
        vlSelfRef.__VstlFirstIteration = 0U;
    } while (vlSelfRef.__VstlPhaseResult);
}

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_triggers_vec__stl(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_triggers_vec__stl\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[1U]) 
                                     | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk) 
                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0))));
    vlSelfRef.__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0 
        = vlSelfRef.gpu_pipeline_tb__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered[0U] = (1ULL | vlSelfRef.__VstlTriggered[0U]);
    }
}

VL_ATTR_COLD bool Vgpu_pipeline_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vgpu_pipeline_tb___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vgpu_pipeline_tb___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] gpu_pipeline_tb.clk)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vgpu_pipeline_tb___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___trigger_anySet__stl\n"); );
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

extern const VlUnpacked<IData/*23:0*/, 256> Vgpu_pipeline_tb__ConstPool__TABLE_h39ac75e8_0;

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___stl_sequent__TOP__1(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___stl_sequent__TOP__1\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 = 0;
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 = 0;
    SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 = 0;
    SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3 = 0;
    SData/*15:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain = 0;
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0 = 0;
    IData/*31:0*/ gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1;
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 = 0;
    CData/*7:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    VlWide<3>/*95:0*/ __Vtemp_1;
    VlWide<3>/*95:0*/ __Vtemp_2;
    VlWide<3>/*95:0*/ __Vtemp_3;
    VlWide<3>/*95:0*/ __Vtemp_4;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_7;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_9;
    // Body
    vlSelfRef.gpu_pipeline_tb__DOT__psram_dq__en1 = 
        ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe)
          ? 0x0fU : 0U);
    vlSelfRef.gpu_pipeline_tb__DOT__display_ready = 
        ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready) 
         & (0U == (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
        = (VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x) 
                            - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1))), 
                       (VL_EXTENDS_QI(64,32, (IData)(
                                                     (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                                                      >> 0x00000020U))) 
                        - VL_EXTENDS_QI(64,32, (IData)(
                                                       (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                                                        >> 0x00000020U))))) 
           - VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y) 
                              - VL_EXTENDS_QI(64,32, (IData)(
                                                             (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                                                              >> 0x00000020U)))), 
                         (VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2)) 
                          - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1)))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
        = (VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x) 
                            - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0))), 
                       (VL_EXTENDS_QI(64,32, (IData)(
                                                     (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 
                                                      >> 0x00000020U))) 
                        - VL_EXTENDS_QI(64,32, (IData)(
                                                       (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                                                        >> 0x00000020U))))) 
           - VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y) 
                              - VL_EXTENDS_QI(64,32, (IData)(
                                                             (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                                                              >> 0x00000020U)))), 
                         (VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1)) 
                          - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0)))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 
        = (VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x) 
                            - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2))), 
                       (VL_EXTENDS_QI(64,32, (IData)(
                                                     (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 
                                                      >> 0x00000020U))) 
                        - VL_EXTENDS_QI(64,32, (IData)(
                                                       (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                                                        >> 0x00000020U))))) 
           - VL_MULS_QQQ(64, (VL_EXTENDS_QI(64,32, vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y) 
                              - VL_EXTENDS_QI(64,32, (IData)(
                                                             (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 
                                                              >> 0x00000020U)))), 
                         (VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0)) 
                          - VL_EXTENDS_QI(64,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2)))));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 
        = VL_MULS_III(32, (IData)(0x000000deU), VL_EXTENDS_II(32,16, 
                                                              (0x0000ffffU 
                                                               & (VL_EXTENDS_II(16,16, 
                                                                                (0x0000ffffU 
                                                                                & ((IData)(8U) 
                                                                                + 
                                                                                (0x00001fffU 
                                                                                & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa) 
                                                                                - 
                                                                                VL_SHIFTRS_III(17,17,32, 
                                                                                (0x0001ffffU 
                                                                                & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc) 
                                                                                + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb))), 1U)) 
                                                                                >> 4U))))) 
                                                                  - (IData)(8U)))));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0 
        = VL_EXTENDS_II(32,16, (0x0000ffffU & (VL_EXTENDS_II(16,16, 
                                                             (0x0000ffffU 
                                                              & ((IData)(8U) 
                                                                 + 
                                                                 (0x00001fffU 
                                                                  & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb) 
                                                                      - (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc)) 
                                                                     >> 4U))))) 
                                               - (IData)(8U))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
        = (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
           + (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
              + vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1 
        = (0x0000ffffU & ((VL_MULS_III(32, (IData)(0x00000100U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                           >> 0x0000001fU) ? ((IData)(1U) 
                                              + (~ 
                                                 (VL_MULS_III(32, (IData)(0x00000100U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                                                  >> 8U)))
                           : (VL_MULS_III(32, (IData)(0x00000100U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
                              >> 8U)));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
        = (VL_MULS_III(32, (IData)(0x00000080U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0) 
           + gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1);
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
        = (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_1 
           + VL_MULS_III(32, (IData)(0xffffff80U), gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_0));
    __Vtableidx1 = (0x000000ffU & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                                           >> 0x00000038U)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal 
        = Vgpu_pipeline_tb__ConstPool__TABLE_h39ac75e8_0
        [__Vtableidx1];
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2 
        = (0x0000ffffU & ((gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                           >> 0x0000001fU) ? ((IData)(1U) 
                                              + (~ 
                                                 (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                                                  >> 8U)))
                           : (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot2 
                              >> 8U)));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3 
        = (0x0000ffffU & ((gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                           >> 0x0000001fU) ? ((IData)(1U) 
                                              + (~ 
                                                 (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                                                  >> 8U)))
                           : (gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__dot3 
                              >> 8U)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside 
        = (((1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
                           >> 0x0000003fU))) == (1U 
                                                 & (IData)(
                                                           (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                                                            >> 0x0000003fU)))) 
           & (((1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
                              >> 0x0000003fU))) == 
               (1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                              >> 0x0000003fU)))) & 
              ((1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 
                              >> 0x0000003fU))) == 
               (1U & (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area 
                              >> 0x0000003fU))))));
    if (vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside) {
        __Vtemp_1[0U] = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        __Vtemp_1[1U] = 0U;
        __Vtemp_1[2U] = 0U;
        __Vtemp_2[0U] = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0);
        __Vtemp_2[1U] = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 
                                 >> 0x00000020U));
        __Vtemp_2[2U] = 0U;
        VL_MUL_W(3, __Vtemp_3, __Vtemp_1, __Vtemp_2);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0 
            = ((__Vtemp_3[1U] << 0x00000019U) | (__Vtemp_3[0U] 
                                                 >> 7U));
        __Vtemp_4[0U] = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        __Vtemp_4[1U] = 0U;
        __Vtemp_4[2U] = 0U;
        __Vtemp_5[0U] = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1);
        __Vtemp_5[1U] = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 
                                 >> 0x00000020U));
        __Vtemp_5[2U] = 0U;
        VL_MUL_W(3, __Vtemp_6, __Vtemp_4, __Vtemp_5);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1 
            = ((__Vtemp_6[1U] << 0x00000019U) | (__Vtemp_6[0U] 
                                                 >> 7U));
        __Vtemp_7[0U] = vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal;
        __Vtemp_7[1U] = 0U;
        __Vtemp_7[2U] = 0U;
        __Vtemp_8[0U] = (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2);
        __Vtemp_8[1U] = (IData)((vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 
                                 >> 0x00000020U));
        __Vtemp_8[2U] = 0U;
        VL_MUL_W(3, __Vtemp_9, __Vtemp_7, __Vtemp_8);
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2 
            = ((__Vtemp_9[1U] << 0x00000019U) | (__Vtemp_9[0U] 
                                                 >> 7U));
    } else {
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0 = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1 = 0U;
        vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2 = 0U;
    }
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2 
        = (((IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2) 
            < (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3))
            ? (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d2)
            : (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d3));
    gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain 
        = (0x0000ffffU & (VL_EXTENDS_II(16,9, (0x000000ffU 
                                               & ((IData)(0x14U) 
                                                  + 
                                                  (7U 
                                                   & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt) 
                                                      >> 3U))))) 
                          - VL_EXTENDS_II(16,9, (0x000000ffU 
                                                 & (((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1) 
                                                     < (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2))
                                                     ? (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1)
                                                     : (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2))))));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10 
        = (VL_LTS_III(32, 0U, VL_EXTENDS_II(32,16, (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain)))
            ? (0x000000ffU & VL_SHIFTR_III(8,16,32, 
                                           (0x0000ffffU 
                                            & ((IData)(0x00ffU) 
                                               * (0x0000ffffU 
                                                  & ((IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain) 
                                                     * (IData)(gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__remain))))), 0x0000000eU))
            : 0U);
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6 
        = (0x0000ffffU & ((IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10) 
                          + VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 4U)));
    vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5 
        = (0x0000ffffU & (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 5U) 
                          + (VL_SHIFTL_III(16,16,32, (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10), 1U) 
                             + (IData)(vlSelfRef.gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6))));
}

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___eval_stl(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_stl\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        vlSelfRef.gpu_pipeline_tb__DOT__clk = (1U & 
                                               (~ (IData)(vlSelfRef.gpu_pipeline_tb__DOT__clk)));
    }
    if ((1ULL & vlSelfRef.__VstlTriggered[1U])) {
        Vgpu_pipeline_tb___024root___stl_sequent__TOP__1(vlSelf);
    }
}

VL_ATTR_COLD bool Vgpu_pipeline_tb___024root___eval_phase__stl(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___eval_phase__stl\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vgpu_pipeline_tb___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vgpu_pipeline_tb___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vgpu_pipeline_tb___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vgpu_pipeline_tb___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vgpu_pipeline_tb___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vgpu_pipeline_tb___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vgpu_pipeline_tb___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @([hybrid] gpu_pipeline_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @( gpu_pipeline_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @( gpu_pipeline_tb.display_ready)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 3U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 3 is active: @( gpu_pipeline_tb.reset)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 4U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 4 is active: @(posedge gpu_pipeline_tb.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 5U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 5 is active: @(posedge gpu_pipeline_tb.reset)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vgpu_pipeline_tb___024root___ctor_var_reset(Vgpu_pipeline_tb___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vgpu_pipeline_tb___024root___ctor_var_reset\n"); );
    Vgpu_pipeline_tb__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->gpu_pipeline_tb__DOT__spi_sck = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4849853839589146775ull);
    vlSelf->gpu_pipeline_tb__DOT__spi_mosi = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18013471481962835595ull);
    vlSelf->gpu_pipeline_tb__DOT__display_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7146798042928788279ull);
    vlSelf->gpu_pipeline_tb__DOT__psram_dq__en1 = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_miso = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12854296494126763301ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_en = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15998178707415909464ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_addr = VL_SCOPED_RAND_RESET_I(23, __VscopeHash, 6933347340794459163ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_rd_data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 6433472271669459734ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7270953747484340162ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__pour_psram_addr = VL_SCOPED_RAND_RESET_I(23, __VscopeHash, 8414882460742108016ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__storage_rd_en = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1942612544543766931ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__pixel_inside = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1899357831766898692ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__l0 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16774113266287197486ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__l1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5072891343864124557ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__l2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11373877520464297704ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__fragment_energy_n, __VscopeHash, 7598586985798869203ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qc = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qb = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT____Vcellout__u_vram__out_qa = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7891153777743154355ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__sd_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 217690486530005381ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 890246502922088357ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__min_x = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12888634345178781815ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_x = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 58955984148818661ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__max_y = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12759727903929471973ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_x = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3616195191746202812ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__cur_y = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1899001011360360946ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v0 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 16856296046141020778ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v1 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 1380544705653867927ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_cmd_proc__DOT__r_v2 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 1619446691958427083ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge0 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 9657635999067777168ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge1 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 9993551947107655693ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__edge2 = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 12856077171656532837ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT__total_area = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 11715754325133373383ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_raster__DOT____Vcellout__rec_lut__reciprocal = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__d1 = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3560475542587723302ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__min_d2 = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3544324644796072881ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__breath_cnt = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 6180485419719148055ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 10305287618225169945ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 107671038464790414ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 10778863344251450320ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 11392585352256137137ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13516625973374568500ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_5 = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_6 = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT____VdfgRegularize_h60acd54f_0_10 = 0;
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__state = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 11238808090561015316ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_sd__DOT__byte_cnt = VL_SCOPED_RAND_RESET_I(13, __VscopeHash, 1210669207577118370ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_storage_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7883883278616515799ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__current_psram_addr = VL_SCOPED_RAND_RESET_I(23, __VscopeHash, 8072441592284083436ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__rem_quadrays = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11465100312612708618ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__quad_lane = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 14709680316446791939ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_pour__DOT__state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 325242254937375428ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__state = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12404676243939437007ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__timer = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14054222579712319920ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__bit_cnt = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 11003698583635011535ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_out = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 13361108641688549186ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__dq_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4095331281964759476ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_psram_hal__DOT__shift_reg = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 983028899311056922ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__current_addr = VL_SCOPED_RAND_RESET_I(23, __VscopeHash, 7864040545382474909ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__rem_len = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 10525310989624878784ull);
    vlSelf->gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_dma__DOT__state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 9138932555712868479ull);
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__pixel_latch = 0;
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_state = 0;
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_shreg = 0;
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__spi_bit_cnt = 0;
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__u_display__DOT__clk_div_cnt = 0;
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__spi_sck = 0;
    vlSelf->__Vdly__gpu_pipeline_tb__DOT__u_gpu_top__DOT__m_psram_ready = 0;
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__clk__0 = 0;
    vlSelf->__VstlDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__display_ready__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__gpu_pipeline_tb__DOT__reset__0 = 0;
    vlSelf->__VactDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
