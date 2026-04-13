#include "verilated.h"
#include "Vpade_eval_4_4_tb_localpoly.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vpade_eval_4_4_tb_localpoly* top = new Vpade_eval_4_4_tb_localpoly();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
