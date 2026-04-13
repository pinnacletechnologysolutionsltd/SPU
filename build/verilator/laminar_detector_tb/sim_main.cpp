#include "verilated.h"
#include "Vlaminar_detector_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vlaminar_detector_tb* top = new Vlaminar_detector_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
