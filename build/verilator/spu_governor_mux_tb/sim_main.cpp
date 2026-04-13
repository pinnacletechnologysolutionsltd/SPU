#include "verilated.h"
#include "Vspu_governor_mux_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_governor_mux_tb* top = new Vspu_governor_mux_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
