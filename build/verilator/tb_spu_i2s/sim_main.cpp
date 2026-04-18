#include "verilated.h"
#include "Vtb_spu_i2s.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtb_spu_i2s* top = new Vtb_spu_i2s();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
