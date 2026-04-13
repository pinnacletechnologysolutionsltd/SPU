// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vspu_spread_mul_tb__pch.h"

//============================================================
// Constructors

Vspu_spread_mul_tb::Vspu_spread_mul_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vspu_spread_mul_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vspu_spread_mul_tb::Vspu_spread_mul_tb(const char* _vcname__)
    : Vspu_spread_mul_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vspu_spread_mul_tb::~Vspu_spread_mul_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vspu_spread_mul_tb___024root___eval_debug_assertions(Vspu_spread_mul_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vspu_spread_mul_tb___024root___eval_static(Vspu_spread_mul_tb___024root* vlSelf);
void Vspu_spread_mul_tb___024root___eval_initial(Vspu_spread_mul_tb___024root* vlSelf);
void Vspu_spread_mul_tb___024root___eval_settle(Vspu_spread_mul_tb___024root* vlSelf);
void Vspu_spread_mul_tb___024root___eval(Vspu_spread_mul_tb___024root* vlSelf);

void Vspu_spread_mul_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vspu_spread_mul_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vspu_spread_mul_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vspu_spread_mul_tb___024root___eval_static(&(vlSymsp->TOP));
        Vspu_spread_mul_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vspu_spread_mul_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vspu_spread_mul_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vspu_spread_mul_tb::eventsPending() { return false; }

uint64_t Vspu_spread_mul_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vspu_spread_mul_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vspu_spread_mul_tb___024root___eval_final(Vspu_spread_mul_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_spread_mul_tb::final() {
    contextp()->executingFinal(true);
    Vspu_spread_mul_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vspu_spread_mul_tb::hierName() const { return vlSymsp->name(); }
const char* Vspu_spread_mul_tb::modelName() const { return "Vspu_spread_mul_tb"; }
unsigned Vspu_spread_mul_tb::threads() const { return 1; }
void Vspu_spread_mul_tb::prepareClone() const { contextp()->prepareClone(); }
void Vspu_spread_mul_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
