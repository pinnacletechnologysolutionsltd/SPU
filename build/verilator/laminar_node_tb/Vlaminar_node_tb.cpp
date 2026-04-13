// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vlaminar_node_tb__pch.h"

//============================================================
// Constructors

Vlaminar_node_tb::Vlaminar_node_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vlaminar_node_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vlaminar_node_tb::Vlaminar_node_tb(const char* _vcname__)
    : Vlaminar_node_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vlaminar_node_tb::~Vlaminar_node_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vlaminar_node_tb___024root___eval_debug_assertions(Vlaminar_node_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vlaminar_node_tb___024root___eval_static(Vlaminar_node_tb___024root* vlSelf);
void Vlaminar_node_tb___024root___eval_initial(Vlaminar_node_tb___024root* vlSelf);
void Vlaminar_node_tb___024root___eval_settle(Vlaminar_node_tb___024root* vlSelf);
void Vlaminar_node_tb___024root___eval(Vlaminar_node_tb___024root* vlSelf);

void Vlaminar_node_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vlaminar_node_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vlaminar_node_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vlaminar_node_tb___024root___eval_static(&(vlSymsp->TOP));
        Vlaminar_node_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vlaminar_node_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vlaminar_node_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vlaminar_node_tb::eventsPending() { return false; }

uint64_t Vlaminar_node_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vlaminar_node_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vlaminar_node_tb___024root___eval_final(Vlaminar_node_tb___024root* vlSelf);

VL_ATTR_COLD void Vlaminar_node_tb::final() {
    contextp()->executingFinal(true);
    Vlaminar_node_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vlaminar_node_tb::hierName() const { return vlSymsp->name(); }
const char* Vlaminar_node_tb::modelName() const { return "Vlaminar_node_tb"; }
unsigned Vlaminar_node_tb::threads() const { return 1; }
void Vlaminar_node_tb::prepareClone() const { contextp()->prepareClone(); }
void Vlaminar_node_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
