#include "verilated.h"
#include "Vspu_spi_slave_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_spi_slave_tb* top = new Vspu_spi_slave_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
