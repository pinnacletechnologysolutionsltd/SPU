// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vspu_triple_quad_tb__pch.h"

Vspu_triple_quad_tb__Syms::Vspu_triple_quad_tb__Syms(VerilatedContext* contextp, const char* namep, Vspu_triple_quad_tb* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup top module instance
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(222);
    // Setup sub module instances
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    // Setup scopes
}

Vspu_triple_quad_tb__Syms::~Vspu_triple_quad_tb__Syms() {
    // Tear down scopes
    // Tear down sub module instances
}
