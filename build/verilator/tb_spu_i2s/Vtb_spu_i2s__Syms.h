// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VTB_SPU_I2S__SYMS_H_
#define VERILATED_VTB_SPU_I2S__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vtb_spu_i2s.h"

// INCLUDE MODULE CLASSES
#include "Vtb_spu_i2s___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vtb_spu_i2s__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vtb_spu_i2s* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vtb_spu_i2s___024root          TOP;

    // CONSTRUCTORS
    Vtb_spu_i2s__Syms(VerilatedContext* contextp, const char* namep, Vtb_spu_i2s* modelp);
    ~Vtb_spu_i2s__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
