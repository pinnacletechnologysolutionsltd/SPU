#include "verilated.h"
#include "Vsimple_lau_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vsimple_lau_tb* top = new Vsimple_lau_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
