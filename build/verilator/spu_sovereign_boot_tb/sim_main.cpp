#include "verilated.h"
#include "Vspu_sovereign_boot_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_sovereign_boot_tb* top = new Vspu_sovereign_boot_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
