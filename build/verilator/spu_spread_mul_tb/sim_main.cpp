#include "verilated.h"
#include "Vspu_spread_mul_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_spread_mul_tb* top = new Vspu_spread_mul_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
