// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VTANG25K_SMOKETEST_TB__SYMS_H_
#define VERILATED_VTANG25K_SMOKETEST_TB__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vtang25k_smoketest_tb.h"

// INCLUDE MODULE CLASSES
#include "Vtang25k_smoketest_tb___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vtang25k_smoketest_tb__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vtang25k_smoketest_tb* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vtang25k_smoketest_tb___024root TOP;

    // CONSTRUCTORS
    Vtang25k_smoketest_tb__Syms(VerilatedContext* contextp, const char* namep, Vtang25k_smoketest_tb* modelp);
    ~Vtang25k_smoketest_tb__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
