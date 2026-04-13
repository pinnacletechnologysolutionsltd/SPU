#include "verilated.h"
#include "Vspu_bresenham_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_bresenham_tb* top = new Vspu_bresenham_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
