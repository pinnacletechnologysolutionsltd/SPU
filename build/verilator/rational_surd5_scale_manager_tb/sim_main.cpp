#include "verilated.h"
#include "Vrational_surd5_scale_manager_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vrational_surd5_scale_manager_tb* top = new Vrational_surd5_scale_manager_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
