#include "verilated.h"
#include "Vspu_unified_alu_tdm_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_unified_alu_tdm_tb* top = new Vspu_unified_alu_tdm_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
