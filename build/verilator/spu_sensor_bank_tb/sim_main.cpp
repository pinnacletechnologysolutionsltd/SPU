#include "verilated.h"
#include "Vspu_sensor_bank_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_sensor_bank_tb* top = new Vspu_sensor_bank_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
