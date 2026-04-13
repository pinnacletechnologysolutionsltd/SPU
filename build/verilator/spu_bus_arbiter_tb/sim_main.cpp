#include "verilated.h"
#include "Vspu_bus_arbiter_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_bus_arbiter_tb* top = new Vspu_bus_arbiter_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
