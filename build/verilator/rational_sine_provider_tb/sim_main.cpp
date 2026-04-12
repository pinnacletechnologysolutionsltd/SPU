#include "verilated.h"
#include "Vrational_sine_provider_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vrational_sine_provider_tb* top = new Vrational_sine_provider_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
