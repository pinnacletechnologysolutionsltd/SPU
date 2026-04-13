#include "verilated.h"
#include "Vinjection_gate_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vinjection_gate_tb* top = new Vinjection_gate_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
