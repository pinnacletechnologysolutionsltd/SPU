// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vtb_spu_flow_control__pch.h"

//============================================================
// Constructors

Vtb_spu_flow_control::Vtb_spu_flow_control(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vtb_spu_flow_control__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vtb_spu_flow_control::Vtb_spu_flow_control(const char* _vcname__)
    : Vtb_spu_flow_control(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vtb_spu_flow_control::~Vtb_spu_flow_control() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vtb_spu_flow_control___024root___eval_debug_assertions(Vtb_spu_flow_control___024root* vlSelf);
#endif  // VL_DEBUG
void Vtb_spu_flow_control___024root___eval_static(Vtb_spu_flow_control___024root* vlSelf);
void Vtb_spu_flow_control___024root___eval_initial(Vtb_spu_flow_control___024root* vlSelf);
void Vtb_spu_flow_control___024root___eval_settle(Vtb_spu_flow_control___024root* vlSelf);
void Vtb_spu_flow_control___024root___eval(Vtb_spu_flow_control___024root* vlSelf);

void Vtb_spu_flow_control::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vtb_spu_flow_control::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vtb_spu_flow_control___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vtb_spu_flow_control___024root___eval_static(&(vlSymsp->TOP));
        Vtb_spu_flow_control___024root___eval_initial(&(vlSymsp->TOP));
        Vtb_spu_flow_control___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vtb_spu_flow_control___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vtb_spu_flow_control::eventsPending() { return false; }

uint64_t Vtb_spu_flow_control::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vtb_spu_flow_control::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vtb_spu_flow_control___024root___eval_final(Vtb_spu_flow_control___024root* vlSelf);

VL_ATTR_COLD void Vtb_spu_flow_control::final() {
    contextp()->executingFinal(true);
    Vtb_spu_flow_control___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vtb_spu_flow_control::hierName() const { return vlSymsp->name(); }
const char* Vtb_spu_flow_control::modelName() const { return "Vtb_spu_flow_control"; }
unsigned Vtb_spu_flow_control::threads() const { return 1; }
void Vtb_spu_flow_control::prepareClone() const { contextp()->prepareClone(); }
void Vtb_spu_flow_control::atClone() const {
    contextp()->threadPoolpOnClone();
}
