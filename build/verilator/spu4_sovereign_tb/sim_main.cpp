#include "verilated.h"
#include "Vspi_flash_model.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspi_flash_model* top = new Vspi_flash_model();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
