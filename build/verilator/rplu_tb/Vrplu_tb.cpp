// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vrplu_tb__pch.h"

//============================================================
// Constructors

Vrplu_tb::Vrplu_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vrplu_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vrplu_tb::Vrplu_tb(const char* _vcname__)
    : Vrplu_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vrplu_tb::~Vrplu_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vrplu_tb___024root___eval_debug_assertions(Vrplu_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vrplu_tb___024root___eval_static(Vrplu_tb___024root* vlSelf);
void Vrplu_tb___024root___eval_initial(Vrplu_tb___024root* vlSelf);
void Vrplu_tb___024root___eval_settle(Vrplu_tb___024root* vlSelf);
void Vrplu_tb___024root___eval(Vrplu_tb___024root* vlSelf);

void Vrplu_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vrplu_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vrplu_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vrplu_tb___024root___eval_static(&(vlSymsp->TOP));
        Vrplu_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vrplu_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vrplu_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vrplu_tb::eventsPending() { return false; }

uint64_t Vrplu_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vrplu_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vrplu_tb___024root___eval_final(Vrplu_tb___024root* vlSelf);

VL_ATTR_COLD void Vrplu_tb::final() {
    contextp()->executingFinal(true);
    Vrplu_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vrplu_tb::hierName() const { return vlSymsp->name(); }
const char* Vrplu_tb::modelName() const { return "Vrplu_tb"; }
unsigned Vrplu_tb::threads() const { return 1; }
void Vrplu_tb::prepareClone() const { contextp()->prepareClone(); }
void Vrplu_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
