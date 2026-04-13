// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VRPLU_TB__SYMS_H_
#define VERILATED_VRPLU_TB__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vrplu_tb.h"

// INCLUDE MODULE CLASSES
#include "Vrplu_tb___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vrplu_tb__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vrplu_tb* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vrplu_tb___024root             TOP;

    // CONSTRUCTORS
    Vrplu_tb__Syms(VerilatedContext* contextp, const char* namep, Vrplu_tb* modelp);
    ~Vrplu_tb__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
