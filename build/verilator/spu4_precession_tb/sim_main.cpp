#include "verilated.h"
#include "Vspu4_precession_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu4_precession_tb* top = new Vspu4_precession_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
