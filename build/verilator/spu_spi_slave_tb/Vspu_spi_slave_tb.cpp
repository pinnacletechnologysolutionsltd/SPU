// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vspu_spi_slave_tb__pch.h"

//============================================================
// Constructors

Vspu_spi_slave_tb::Vspu_spi_slave_tb(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vspu_spi_slave_tb__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vspu_spi_slave_tb::Vspu_spi_slave_tb(const char* _vcname__)
    : Vspu_spi_slave_tb(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vspu_spi_slave_tb::~Vspu_spi_slave_tb() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vspu_spi_slave_tb___024root___eval_debug_assertions(Vspu_spi_slave_tb___024root* vlSelf);
#endif  // VL_DEBUG
void Vspu_spi_slave_tb___024root___eval_static(Vspu_spi_slave_tb___024root* vlSelf);
void Vspu_spi_slave_tb___024root___eval_initial(Vspu_spi_slave_tb___024root* vlSelf);
void Vspu_spi_slave_tb___024root___eval_settle(Vspu_spi_slave_tb___024root* vlSelf);
void Vspu_spi_slave_tb___024root___eval(Vspu_spi_slave_tb___024root* vlSelf);

void Vspu_spi_slave_tb::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vspu_spi_slave_tb::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vspu_spi_slave_tb___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vspu_spi_slave_tb___024root___eval_static(&(vlSymsp->TOP));
        Vspu_spi_slave_tb___024root___eval_initial(&(vlSymsp->TOP));
        Vspu_spi_slave_tb___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vspu_spi_slave_tb___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vspu_spi_slave_tb::eventsPending() { return false; }

uint64_t Vspu_spi_slave_tb::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vspu_spi_slave_tb::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vspu_spi_slave_tb___024root___eval_final(Vspu_spi_slave_tb___024root* vlSelf);

VL_ATTR_COLD void Vspu_spi_slave_tb::final() {
    contextp()->executingFinal(true);
    Vspu_spi_slave_tb___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vspu_spi_slave_tb::hierName() const { return vlSymsp->name(); }
const char* Vspu_spi_slave_tb::modelName() const { return "Vspu_spi_slave_tb"; }
unsigned Vspu_spi_slave_tb::threads() const { return 1; }
void Vspu_spi_slave_tb::prepareClone() const { contextp()->prepareClone(); }
void Vspu_spi_slave_tb::atClone() const {
    contextp()->threadPoolpOnClone();
}
