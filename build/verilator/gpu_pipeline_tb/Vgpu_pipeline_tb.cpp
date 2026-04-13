// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vgpu_pipeline_tb__pch.h"

//============================================================
// Constructors

Vgpu_pipeline_tb::Vgpu_pipeline_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vgpu_pipeline_tb__Syms(contextp(), _vcname__, this)}
    , __PVT____024unit{vlSymsp->TOP.__PVT____024unit}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vgpu_pipeline_tb::Vgpu_pipeline_tb(const char* _vcname__)
    : Vgpu_pipeline_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vgpu_pipeline_tb::~Vgpu_pipeline_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vgpu_pipeline_tb___024root___eval_debug_assertions(Vgpu_pipeline_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vgpu_pipeline_tb___024root___eval_static(Vgpu_pipeline_tb___024root* vlSelf);
void Vgpu_pipeline_tb___024root___eval_initial(Vgpu_pipeline_tb___024root* vlSelf);
void Vgpu_pipeline_tb___024root___eval_settle(Vgpu_pipeline_tb___024root* vlSelf);
void Vgpu_pipeline_tb___024root___eval(Vgpu_pipeline_tb___024root* vlSelf);

void Vgpu_pipeline_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vgpu_pipeline_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vgpu_pipeline_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vgpu_pipeline_tb___024root___eval_static(&(vlSymsp->TOP));
        Vgpu_pipeline_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vgpu_pipeline_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vgpu_pipeline_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vgpu_pipeline_tb::eventsPending() { return false; }

uint64_t Vgpu_pipeline_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vgpu_pipeline_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vgpu_pipeline_tb___024root___eval_final(Vgpu_pipeline_tb___024root* vlSelf);

VL_ATTR_COLD void Vgpu_pipeline_tb::final() {
    contextp()->executingFinal(true);
    Vgpu_pipeline_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vgpu_pipeline_tb::hierName() const { return vlSymsp->name(); }
const char* Vgpu_pipeline_tb::modelName() const { return "Vgpu_pipeline_tb"; }
unsigned Vgpu_pipeline_tb::threads() const { return 1; }
void Vgpu_pipeline_tb::prepareClone() const { contextp()->prepareClone(); }
void Vgpu_pipeline_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
