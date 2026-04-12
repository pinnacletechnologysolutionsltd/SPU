#include "verilated.h"
#include "Vlaminar_node_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vlaminar_node_tb* top = new Vlaminar_node_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
