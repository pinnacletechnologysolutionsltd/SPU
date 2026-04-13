#include "verilated.h"
#include "Vspu_pdm_audio_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_pdm_audio_tb* top = new Vspu_pdm_audio_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
