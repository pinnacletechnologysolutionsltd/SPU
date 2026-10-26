// C++ VM SPREAD driver for test_gram_v1_spread_cpp.py.
// stdin per case: mode(l|g) rd  v[4][2]  w[4][2]   (int32 lanes). stdout: one full-state line per case.
#define main spu_vm_cli_main
#include "../vm/spu_vm.cpp"
#undef main

// Exact int32 boundary of the final-result check (random cases cannot hit it).
static bool boundary_ok() {
    using namespace gram;
    int32_t o;
    I256 big = mul(I256::from_i64(1LL << 40), I256::from_i64(1LL << 40));  // 2^80 spans limbs
    return to_i32(I256::from_i64(INT32_MAX), o) && o == INT32_MAX
        && !to_i32(I256::from_i64((int64_t)INT32_MAX + 1), o)
        && to_i32(I256::from_i64(INT32_MIN), o) && o == INT32_MIN
        && !to_i32(I256::from_i64((int64_t)INT32_MIN - 1), o)
        && !to_i32(big, o) && !to_i32(negate(big), o)
        && to_i32(sub(big, big), o) && o == 0
        && !to_i32(I256{{0, 1, 0, 0}}, o);  // 2^64
}

int main() {
    if (!boundary_ok()) { std::cout << "BOUNDARY_FAIL\n"; return 1; }
    std::string mode;
    int rd;
    while (std::cin >> mode >> rd) {
        SPUCore core(64, false, false,
                     mode == "g" ? MetricSemantics::GramV1 : MetricSemantics::LegacyDot);
        // Seed every register distinctly so any stray write is visible in the full-state dump.
        for (int i = 0; i < NUM_REGS; i++) core.regs[i] = RationalSurd(100 + i, -i);
        for (int q = 2; q < 13; q++)
            for (auto* r : {&core.qregs[q].a, &core.qregs[q].b, &core.qregs[q].c, &core.qregs[q].d})
                *r = RationalSurd(5 * q + 1, q - 3);
        for (int q = 0; q < 2; q++)
            for (auto* r : {&core.qregs[q].a, &core.qregs[q].b, &core.qregs[q].c, &core.qregs[q].d})
                std::cin >> r->a >> r->b;
        core.regs[rd] = RationalSurd(7, 7);
        core.regs[(rd + 1) % NUM_REGS] = RationalSurd(9, 9);
        core.call_stack = {19, 23};
        core.snap_failures = 2;
        core.load({(0x15ULL << 56) | ((uint64_t)rd << 48) | (1ULL << 8)});
        std::ostringstream sink;
        auto* saved = std::cout.rdbuf(sink.rdbuf());
        try { core.step(); } catch (const VmFault&) {}
        std::cout.rdbuf(saved);
        std::cout << (core.fault_kind.empty() ? "OK" : core.fault_kind) << " " << core.pc << " "
                  << core.halted << " " << core.step_count << " " << core.snap_failures << " "
                  << core.call_stack.size();
        for (int x : core.call_stack) std::cout << " " << x;
        for (auto& r : core.regs) std::cout << " " << r.a << " " << r.b;
        for (auto& q : core.qregs)
            for (auto* r : {&q.a, &q.b, &q.c, &q.d}) std::cout << " " << r->a << " " << r->b;
        std::cout << "\n";
    }
}
