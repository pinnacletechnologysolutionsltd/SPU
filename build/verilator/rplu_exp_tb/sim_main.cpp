#include "verilated.h"
#include "Vrplu_exp_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vrplu_exp_tb* top = new Vrplu_exp_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
