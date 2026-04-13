#include "verilated.h"
#include "Vspu_whisper_bridge_v2_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_whisper_bridge_v2_tb* top = new Vspu_whisper_bridge_v2_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
