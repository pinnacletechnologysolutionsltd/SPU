#include "verilated.h"
#include "Vspu4_phinary_cfg_unit_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu4_phinary_cfg_unit_tb* top = new Vspu4_phinary_cfg_unit_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
