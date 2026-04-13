#include "verilated.h"
#include "Vspu_mem_bridge_ddr3_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_mem_bridge_ddr3_tb* top = new Vspu_mem_bridge_ddr3_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
