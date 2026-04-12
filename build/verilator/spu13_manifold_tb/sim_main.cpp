#include "verilated.h"
#include "Vspu13_manifold_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu13_manifold_tb* top = new Vspu13_manifold_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
