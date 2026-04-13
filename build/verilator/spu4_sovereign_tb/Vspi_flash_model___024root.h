// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vspi_flash_model.h for the primary calling header

#ifndef VERILATED_VSPI_FLASH_MODEL___024ROOT_H_
#define VERILATED_VSPI_FLASH_MODEL___024ROOT_H_  // guard

#include "verilated.h"


class Vspi_flash_model__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vspi_flash_model___024root final {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(sck,0,0);
    VL_IN8(cs_n,0,0);
    VL_IN8(mosi,0,0);
    VL_OUT8(miso,0,0);
    CData/*7:0*/ spi_flash_model__DOT__cmd;
    CData/*2:0*/ spi_flash_model__DOT__state;
    CData/*7:0*/ spi_flash_model__DOT__bit_cnt;
    CData/*0:0*/ __Vtrigprevexpr___TOP__sck__0;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    IData/*23:0*/ spi_flash_model__DOT__addr;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<CData/*7:0*/, 256> spi_flash_model__DOT__data;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vspi_flash_model__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vspi_flash_model___024root(Vspi_flash_model__Syms* symsp, const char* namep);
    ~Vspi_flash_model___024root();
    VL_UNCOPYABLE(Vspi_flash_model___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
