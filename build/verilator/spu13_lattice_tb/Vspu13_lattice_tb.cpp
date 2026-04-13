// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vspu13_lattice_tb__pch.h"

//============================================================
// Constructors

Vspu13_lattice_tb::Vspu13_lattice_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vspu13_lattice_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vspu13_lattice_tb::Vspu13_lattice_tb(const char* _vcname__)
    : Vspu13_lattice_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vspu13_lattice_tb::~Vspu13_lattice_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vspu13_lattice_tb___024root___eval_debug_assertions(Vspu13_lattice_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vspu13_lattice_tb___024root___eval_static(Vspu13_lattice_tb___024root* vlSelf);
void Vspu13_lattice_tb___024root___eval_initial(Vspu13_lattice_tb___024root* vlSelf);
void Vspu13_lattice_tb___024root___eval_settle(Vspu13_lattice_tb___024root* vlSelf);
void Vspu13_lattice_tb___024root___eval(Vspu13_lattice_tb___024root* vlSelf);

void Vspu13_lattice_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vspu13_lattice_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vspu13_lattice_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vspu13_lattice_tb___024root___eval_static(&(vlSymsp->TOP));
        Vspu13_lattice_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vspu13_lattice_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vspu13_lattice_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vspu13_lattice_tb::eventsPending() { return false; }

uint64_t Vspu13_lattice_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vspu13_lattice_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vspu13_lattice_tb___024root___eval_final(Vspu13_lattice_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu13_lattice_tb::final() {
    contextp()->executingFinal(true);
    Vspu13_lattice_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vspu13_lattice_tb::hierName() const { return vlSymsp->name(); }
const char* Vspu13_lattice_tb::modelName() const { return "Vspu13_lattice_tb"; }
unsigned Vspu13_lattice_tb::threads() const { return 1; }
void Vspu13_lattice_tb::prepareClone() const { contextp()->prepareClone(); }
void Vspu13_lattice_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
