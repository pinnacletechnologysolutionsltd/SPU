#include "verilated.h"
#include "Vspu13_deep_spin_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu13_deep_spin_tb* top = new Vspu13_deep_spin_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
