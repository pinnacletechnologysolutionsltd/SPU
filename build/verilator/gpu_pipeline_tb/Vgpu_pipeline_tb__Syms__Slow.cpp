// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vgpu_pipeline_tb__pch.h"

Vgpu_pipeline_tb__Syms::Vgpu_pipeline_tb__Syms(VerilatedContext* contextp, const char* namep, Vgpu_pipeline_tb* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup top module instance
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(1080);
    // Setup sub module instances
    TOP____024unit.ctor(this, "$unit");
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    TOP.__PVT____024unit = &TOP____024unit;
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    TOP____024unit.__Vconfigure(true);
    // Setup scopes
}

Vgpu_pipeline_tb__Syms::~Vgpu_pipeline_tb__Syms() {
    // Tear down scopes
    // Tear down sub module instances
    TOP____024unit.dtor();
}
