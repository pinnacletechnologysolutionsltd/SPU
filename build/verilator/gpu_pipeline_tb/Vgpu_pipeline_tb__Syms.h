// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VGPU_PIPELINE_TB__SYMS_H_
#define VERILATED_VGPU_PIPELINE_TB__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vgpu_pipeline_tb.h"

// INCLUDE MODULE CLASSES
#include "Vgpu_pipeline_tb___024root.h"
#include "Vgpu_pipeline_tb___024unit.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vgpu_pipeline_tb__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vgpu_pipeline_tb* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vgpu_pipeline_tb___024root     TOP;
    Vgpu_pipeline_tb___024unit     TOP____024unit;

    // CONSTRUCTORS
    Vgpu_pipeline_tb__Syms(VerilatedContext* contextp, const char* namep, Vgpu_pipeline_tb* modelp);
    ~Vgpu_pipeline_tb__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
