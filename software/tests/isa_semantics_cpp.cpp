// Exercise maintained C++ VM with independently seeded boundary state.
#define main spu_vm_cli_main
#include "../vm/spu_vm.cpp"
#undef main

int main() {
    SPUCore core(64, false);
    std::string mode;
    uint64_t word;
    std::cin >> mode >> std::hex >> word >> std::dec;
    core.load({word});
    for (auto& r : core.regs) std::cin >> r.a >> r.b >> r.pell_step;
    for (auto& q : core.qregs)
        for (auto* r : {&q.a, &q.b, &q.c, &q.d})
            std::cin >> r->a >> r->b;
    core.call_stack = {19, 23};
    core.snap_failures = 2;
    core.proof = mode == "proof";
    std::ostringstream diagnostics;
    auto* output = std::cout.rdbuf(diagnostics.rdbuf());
    try { core.step(); } catch (const VmFault&) {}
    if (mode == "reload") core.load({0xff00000000000000ULL});
    if (mode == "cold") core = SPUCore(64, false);
    if (mode == "pell9") {
        core = SPUCore(64, false);
        core.load({0x0001000001000000ULL});
        core.step();
        core.load(std::vector<uint64_t>(9, 0x0401000000000000ULL));
        core.run();
    }
    std::cout.rdbuf(output);
    std::cout << "STATUS " << (core.fault_kind.empty() ? "OK" : core.fault_kind)
              << " " << core.pc << " " << core.halted << " " << core.step_count
              << " " << core.snap_failures;
    for (int address : core.call_stack) std::cout << " " << address;
    std::cout << "\n";
    for (int i = 0; i < NUM_REGS; ++i)
        std::cout << "R " << i << " " << core.regs[i].a << " " << core.regs[i].b
                  << " " << core.regs[i].pell_step << "\n";
    for (int i = 0; i < 13; ++i) {
        std::cout << "Q " << i;
        for (auto r : {core.qregs[i].a, core.qregs[i].b, core.qregs[i].c, core.qregs[i].d})
            std::cout << " " << r.a << " " << r.b;
        std::cout << "\n";
    }
    if (mode == "proof") std::cout << "PROOF " << diagnostics.str();
}
