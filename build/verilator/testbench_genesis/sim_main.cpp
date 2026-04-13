#include "verilated.h"
#include "Vtestbench_genesis.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtestbench_genesis* top = new Vtestbench_genesis();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
