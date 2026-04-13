// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vrational_sine_provider_tb__pch.h"

Vrational_sine_provider_tb__Syms::Vrational_sine_provider_tb__Syms(VerilatedContext* contextp, const char* namep, Vrational_sine_provider_tb* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup top module instance
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(186);
    // Setup sub module instances
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    // Setup scopes
}

Vrational_sine_provider_tb__Syms::~Vrational_sine_provider_tb__Syms() {
    // Tear down scopes
    // Tear down sub module instances
}
