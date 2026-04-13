#include "verilated.h"
#include "Vdavis_to_rplu_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vdavis_to_rplu_tb* top = new Vdavis_to_rplu_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
