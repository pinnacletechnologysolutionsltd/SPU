#include "verilated.h"
#include "Vspu_triple_spread_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_triple_spread_tb* top = new Vspu_triple_spread_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
