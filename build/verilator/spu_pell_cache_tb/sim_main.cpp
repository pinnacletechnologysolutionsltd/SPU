#include "verilated.h"
#include "Vspu_pell_cache_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_pell_cache_tb* top = new Vspu_pell_cache_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
