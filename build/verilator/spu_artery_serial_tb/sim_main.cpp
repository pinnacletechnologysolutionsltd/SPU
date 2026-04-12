#include "verilated.h"
#include "Vspu_artery_serial_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_artery_serial_tb* top = new Vspu_artery_serial_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
