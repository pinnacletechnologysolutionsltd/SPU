// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vspi_flash_model__pch.h"

//============================================================
// Constructors

Vspi_flash_model::Vspi_flash_model(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vspi_flash_model__Syms(contextp(), _vcname__, this)}
    , sck{vlSymsp->TOP.sck}
    , cs_n{vlSymsp->TOP.cs_n}
    , mosi{vlSymsp->TOP.mosi}
    , miso{vlSymsp->TOP.miso}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vspi_flash_model::Vspi_flash_model(const char* _vcname__)
    : Vspi_flash_model(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vspi_flash_model::~Vspi_flash_model() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vspi_flash_model___024root___eval_debug_assertions(Vspi_flash_model___024root* vlSelf);
#endif  // VL_DEBUG
void Vspi_flash_model___024root___eval_static(Vspi_flash_model___024root* vlSelf);
void Vspi_flash_model___024root___eval_initial(Vspi_flash_model___024root* vlSelf);
void Vspi_flash_model___024root___eval_settle(Vspi_flash_model___024root* vlSelf);
void Vspi_flash_model___024root___eval(Vspi_flash_model___024root* vlSelf);

void Vspi_flash_model::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vspi_flash_model::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vspi_flash_model___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vspi_flash_model___024root___eval_static(&(vlSymsp->TOP));
        Vspi_flash_model___024root___eval_initial(&(vlSymsp->TOP));
        Vspi_flash_model___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vspi_flash_model___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vspi_flash_model::eventsPending() { return false; }

uint64_t Vspi_flash_model::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vspi_flash_model::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vspi_flash_model___024root___eval_final(Vspi_flash_model___024root* vlSelf);

VL_ATTR_COLD void Vspi_flash_model::final() {
    contextp()->executingFinal(true);
    Vspi_flash_model___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vspi_flash_model::hierName() const { return vlSymsp->name(); }
const char* Vspi_flash_model::modelName() const { return "Vspi_flash_model"; }
unsigned Vspi_flash_model::threads() const { return 1; }
void Vspi_flash_model::prepareClone() const { contextp()->prepareClone(); }
void Vspi_flash_model::atClone() const {
    contextp()->threadPoolpOnClone();
}
