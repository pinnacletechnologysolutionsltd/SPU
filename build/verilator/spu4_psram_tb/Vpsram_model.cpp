// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vpsram_model__pch.h"

//============================================================
// Constructors

Vpsram_model::Vpsram_model(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vpsram_model__Syms(contextp(), _vcname__, this)}
    , sck{vlSymsp->TOP.sck}
    , ce_n{vlSymsp->TOP.ce_n}
    , dq{vlSymsp->TOP.dq}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vpsram_model::Vpsram_model(const char* _vcname__)
    : Vpsram_model(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vpsram_model::~Vpsram_model() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vpsram_model___024root___eval_debug_assertions(Vpsram_model___024root* vlSelf);
#endif  // VL_DEBUG
void Vpsram_model___024root___eval_static(Vpsram_model___024root* vlSelf);
void Vpsram_model___024root___eval_initial(Vpsram_model___024root* vlSelf);
void Vpsram_model___024root___eval_settle(Vpsram_model___024root* vlSelf);
void Vpsram_model___024root___eval(Vpsram_model___024root* vlSelf);

void Vpsram_model::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vpsram_model::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vpsram_model___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vpsram_model___024root___eval_static(&(vlSymsp->TOP));
        Vpsram_model___024root___eval_initial(&(vlSymsp->TOP));
        Vpsram_model___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vpsram_model___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vpsram_model::eventsPending() { return false; }

uint64_t Vpsram_model::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vpsram_model::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vpsram_model___024root___eval_final(Vpsram_model___024root* vlSelf);

VL_ATTR_COLD void Vpsram_model::final() {
    contextp()->executingFinal(true);
    Vpsram_model___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vpsram_model::hierName() const { return vlSymsp->name(); }
const char* Vpsram_model::modelName() const { return "Vpsram_model"; }
unsigned Vpsram_model::threads() const { return 1; }
void Vpsram_model::prepareClone() const { contextp()->prepareClone(); }
void Vpsram_model::atClone() const {
    contextp()->threadPoolpOnClone();
}
