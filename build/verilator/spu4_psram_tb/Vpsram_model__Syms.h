// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VPSRAM_MODEL__SYMS_H_
#define VERILATED_VPSRAM_MODEL__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vpsram_model.h"

// INCLUDE MODULE CLASSES
#include "Vpsram_model___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vpsram_model__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vpsram_model* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vpsram_model___024root         TOP;

    // CONSTRUCTORS
    Vpsram_model__Syms(VerilatedContext* contextp, const char* namep, Vpsram_model* modelp);
    ~Vpsram_model__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
