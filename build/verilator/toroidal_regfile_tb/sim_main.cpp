#include "verilated.h"
#include "Vtoroidal_regfile_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtoroidal_regfile_tb* top = new Vtoroidal_regfile_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
