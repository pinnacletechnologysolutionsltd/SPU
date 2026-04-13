#include "verilated.h"
#include "Vspu_uart_bridge_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vspu_uart_bridge_tb* top = new Vspu_uart_bridge_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
