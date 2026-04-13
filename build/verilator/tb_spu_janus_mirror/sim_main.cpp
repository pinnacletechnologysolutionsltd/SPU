#include "verilated.h"
#include "Vtb_spu_janus_mirror.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtb_spu_janus_mirror* top = new Vtb_spu_janus_mirror();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
