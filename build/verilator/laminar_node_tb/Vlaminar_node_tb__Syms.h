// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VLAMINAR_NODE_TB__SYMS_H_
#define VERILATED_VLAMINAR_NODE_TB__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vlaminar_node_tb.h"

// INCLUDE MODULE CLASSES
#include "Vlaminar_node_tb___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vlaminar_node_tb__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vlaminar_node_tb* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vlaminar_node_tb___024root     TOP;

    // CONSTRUCTORS
    Vlaminar_node_tb__Syms(VerilatedContext* contextp, const char* namep, Vlaminar_node_tb* modelp);
    ~Vlaminar_node_tb__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
