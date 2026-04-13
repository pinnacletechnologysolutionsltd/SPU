// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vtang25k_smoketest_tb__pch.h"

//============================================================
// Constructors

Vtang25k_smoketest_tb::Vtang25k_smoketest_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vtang25k_smoketest_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vtang25k_smoketest_tb::Vtang25k_smoketest_tb(const char* _vcname__)
    : Vtang25k_smoketest_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vtang25k_smoketest_tb::~Vtang25k_smoketest_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vtang25k_smoketest_tb___024root___eval_debug_assertions(Vtang25k_smoketest_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vtang25k_smoketest_tb___024root___eval_static(Vtang25k_smoketest_tb___024root* vlSelf);
void Vtang25k_smoketest_tb___024root___eval_initial(Vtang25k_smoketest_tb___024root* vlSelf);
void Vtang25k_smoketest_tb___024root___eval_settle(Vtang25k_smoketest_tb___024root* vlSelf);
void Vtang25k_smoketest_tb___024root___eval(Vtang25k_smoketest_tb___024root* vlSelf);

void Vtang25k_smoketest_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vtang25k_smoketest_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vtang25k_smoketest_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vtang25k_smoketest_tb___024root___eval_static(&(vlSymsp->TOP));
        Vtang25k_smoketest_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vtang25k_smoketest_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vtang25k_smoketest_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vtang25k_smoketest_tb::eventsPending() { return false; }

uint64_t Vtang25k_smoketest_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vtang25k_smoketest_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vtang25k_smoketest_tb___024root___eval_final(Vtang25k_smoketest_tb___024root* vlSelf);

VL_ATTR_COLD void Vtang25k_smoketest_tb::final() {
    contextp()->executingFinal(true);
    Vtang25k_smoketest_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vtang25k_smoketest_tb::hierName() const { return vlSymsp->name(); }
const char* Vtang25k_smoketest_tb::modelName() const { return "Vtang25k_smoketest_tb"; }
unsigned Vtang25k_smoketest_tb::threads() const { return 1; }
void Vtang25k_smoketest_tb::prepareClone() const { contextp()->prepareClone(); }
void Vtang25k_smoketest_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
