#include "verilated.h"
#include "Vspu_rotor_vault_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_rotor_vault_tb* top = new Vspu_rotor_vault_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
