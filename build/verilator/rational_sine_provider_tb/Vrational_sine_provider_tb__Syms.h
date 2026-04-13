// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VRATIONAL_SINE_PROVIDER_TB__SYMS_H_
#define VERILATED_VRATIONAL_SINE_PROVIDER_TB__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vrational_sine_provider_tb.h"

// INCLUDE MODULE CLASSES
#include "Vrational_sine_provider_tb___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vrational_sine_provider_tb__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vrational_sine_provider_tb* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vrational_sine_provider_tb___024root TOP;

    // CONSTRUCTORS
    Vrational_sine_provider_tb__Syms(VerilatedContext* contextp, const char* namep, Vrational_sine_provider_tb* modelp);
    ~Vrational_sine_provider_tb__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
