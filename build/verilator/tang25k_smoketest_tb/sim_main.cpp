#include "verilated.h"
#include "Vtang25k_smoketest_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtang25k_smoketest_tb* top = new Vtang25k_smoketest_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
