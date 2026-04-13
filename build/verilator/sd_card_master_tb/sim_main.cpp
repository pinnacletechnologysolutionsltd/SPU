#include "verilated.h"
#include "Vsd_card_master_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vsd_card_master_tb* top = new Vsd_card_master_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
