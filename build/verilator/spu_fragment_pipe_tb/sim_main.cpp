#include "verilated.h"
#include "Vspu_fragment_pipe_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_fragment_pipe_tb* top = new Vspu_fragment_pipe_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
