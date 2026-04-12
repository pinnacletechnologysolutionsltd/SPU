#include "verilated.h"
#include "Vtb_spu_flash_bridge.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtb_spu_flash_bridge* top = new Vtb_spu_flash_bridge();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
