#include "verilated.h"
#include "Vtb_spu_flow_control.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtb_spu_flow_control* top = new Vtb_spu_flow_control();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
