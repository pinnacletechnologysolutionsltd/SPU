#include "verilated.h"
#include "Vspu_input_sync_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_input_sync_tb* top = new Vspu_input_sync_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
