// Compile-time inclusion exercises the maintained VM and its source assembler.
#define main spu_vm_cli_main
#include "../vm/spu_vm.cpp"
#undef main

int main(int argc, char**) {
    try {
        std::ostringstream source;
        source << std::cin.rdbuf();
        std::vector<uint64_t> words;
        if (argc > 2) {
            std::istringstream tokens(source.str());
            uint64_t word;
            while (tokens >> std::hex >> word) words.push_back(word);
        } else words = assemble_source(source.str());
        if (argc == 1) {
            for (auto w : words) std::cout << "WORD " << std::hex << w << "\n";
            return 0;
        }
        SPUCore core(256, false);
        core.load(words);
        if (argc > 2) {
            core.regs[1] = RationalSurd(9, -3);
            core.qregs[2].a = RationalSurd(13);
            try { core.run(); }
            catch (const std::runtime_error&) {
                std::cout << "REJECTED " << core.pc << " " << core.halted << " "
                          << core.regs[1].a << " " << core.regs[1].b << " " << core.qregs[2].a.a << "\n";
                return 0;
            }
            return 2;
        }
        core.run();
        for (int i = 0; i < NUM_REGS; ++i)
            std::cout << "R " << i << " " << core.regs[i].a << " " << core.regs[i].b << "\n";
        for (int i = 0; i < 13; ++i) {
            const auto& q = core.qregs[i];
            std::cout << "Q " << i;
            for (auto c : {q.a, q.b, q.c, q.d}) std::cout << " " << c.a << " " << c.b;
            std::cout << "\n";
        }
        std::cout << "CONTROL " << core.pc << " " << core.halted << " " << core.call_stack.size() << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << "\n";
        return 1;
    }
}
