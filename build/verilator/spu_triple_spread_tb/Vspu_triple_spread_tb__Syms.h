// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VSPU_TRIPLE_SPREAD_TB__SYMS_H_
#define VERILATED_VSPU_TRIPLE_SPREAD_TB__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vspu_triple_spread_tb.h"

// INCLUDE MODULE CLASSES
#include "Vspu_triple_spread_tb___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vspu_triple_spread_tb__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vspu_triple_spread_tb* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vspu_triple_spread_tb___024root TOP;

    // CONSTRUCTORS
    Vspu_triple_spread_tb__Syms(VerilatedContext* contextp, const char* namep, Vspu_triple_spread_tb* modelp);
    ~Vspu_triple_spread_tb__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
