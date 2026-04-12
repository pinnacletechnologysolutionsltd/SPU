#include "verilated.h"
#include "Vtoroidal_regression_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtoroidal_regression_tb* top = new Vtoroidal_regression_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
