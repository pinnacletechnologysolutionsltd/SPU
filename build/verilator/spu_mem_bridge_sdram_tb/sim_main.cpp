#include "verilated.h"
#include "Vspu_mem_bridge_sdram_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_mem_bridge_sdram_tb* top = new Vspu_mem_bridge_sdram_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
