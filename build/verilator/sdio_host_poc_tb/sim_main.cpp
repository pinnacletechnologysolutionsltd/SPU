#include "verilated.h"
#include "Vsdio_host_poc_tb.h"
#include <iostream>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vsdio_host_poc_tb* top = new Vsdio_host_poc_tb();
    while (!Verilated::gotFinish()) {
        top->eval();
    }
    delete top;
    return 0;
}
