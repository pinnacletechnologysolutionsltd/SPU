#include "verilated.h"
#include "Vdavis_gate_dsp_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vdavis_gate_dsp_tb* top = new Vdavis_gate_dsp_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
