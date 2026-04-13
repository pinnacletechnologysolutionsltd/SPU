#include "verilated.h"
#include "Vspu_4_alu_fold_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_4_alu_fold_tb* top = new Vspu_4_alu_fold_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
