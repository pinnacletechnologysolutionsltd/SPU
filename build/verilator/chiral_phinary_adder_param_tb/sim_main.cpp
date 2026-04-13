#include "verilated.h"
#include "Vchiral_phinary_adder_param_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vchiral_phinary_adder_param_tb* top = new Vchiral_phinary_adder_param_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
