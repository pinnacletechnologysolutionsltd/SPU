// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vspu4_sentinel_tb__pch.h"

//============================================================
// Constructors

Vspu4_sentinel_tb::Vspu4_sentinel_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vspu4_sentinel_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vspu4_sentinel_tb::Vspu4_sentinel_tb(const char* _vcname__)
    : Vspu4_sentinel_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vspu4_sentinel_tb::~Vspu4_sentinel_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vspu4_sentinel_tb___024root___eval_debug_assertions(Vspu4_sentinel_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vspu4_sentinel_tb___024root___eval_static(Vspu4_sentinel_tb___024root* vlSelf);
void Vspu4_sentinel_tb___024root___eval_initial(Vspu4_sentinel_tb___024root* vlSelf);
void Vspu4_sentinel_tb___024root___eval_settle(Vspu4_sentinel_tb___024root* vlSelf);
void Vspu4_sentinel_tb___024root___eval(Vspu4_sentinel_tb___024root* vlSelf);

void Vspu4_sentinel_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vspu4_sentinel_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vspu4_sentinel_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vspu4_sentinel_tb___024root___eval_static(&(vlSymsp->TOP));
        Vspu4_sentinel_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vspu4_sentinel_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vspu4_sentinel_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vspu4_sentinel_tb::eventsPending() { return false; }

uint64_t Vspu4_sentinel_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vspu4_sentinel_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vspu4_sentinel_tb___024root___eval_final(Vspu4_sentinel_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu4_sentinel_tb::final() {
    contextp()->executingFinal(true);
    Vspu4_sentinel_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vspu4_sentinel_tb::hierName() const { return vlSymsp->name(); }
const char* Vspu4_sentinel_tb::modelName() const { return "Vspu4_sentinel_tb"; }
unsigned Vspu4_sentinel_tb::threads() const { return 1; }
void Vspu4_sentinel_tb::prepareClone() const { contextp()->prepareClone(); }
void Vspu4_sentinel_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
