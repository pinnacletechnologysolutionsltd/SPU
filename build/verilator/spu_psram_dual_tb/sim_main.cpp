#include "verilated.h"
#include "Vspu_psram_dual_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_psram_dual_tb* top = new Vspu_psram_dual_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
