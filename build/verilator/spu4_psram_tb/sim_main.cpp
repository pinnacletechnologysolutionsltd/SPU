#include "verilated.h"
#include "Vpsram_model.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vpsram_model* top = new Vpsram_model();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
