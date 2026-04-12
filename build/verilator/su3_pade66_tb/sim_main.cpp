#include "verilated.h"
#include "Vsu3_pade66_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vsu3_pade66_tb* top = new Vsu3_pade66_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
