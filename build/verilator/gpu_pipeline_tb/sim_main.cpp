#include "verilated.h"
#include "Vgpu_pipeline_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vgpu_pipeline_tb* top = new Vgpu_pipeline_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
