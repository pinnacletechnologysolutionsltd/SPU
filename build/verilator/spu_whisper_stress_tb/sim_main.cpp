#include "verilated.h"
#include "Vspu_whisper_stress_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_whisper_stress_tb* top = new Vspu_whisper_stress_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
