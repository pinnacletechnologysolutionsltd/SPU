#include "verilated.h"
#include "Vspu_laminar_power_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_laminar_power_tb* top = new Vspu_laminar_power_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
