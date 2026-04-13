#include "verilated.h"
#include "Vpade_eval_compare_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vpade_eval_compare_tb* top = new Vpade_eval_compare_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
