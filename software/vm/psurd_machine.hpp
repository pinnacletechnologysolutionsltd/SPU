// psurd_machine.hpp — EXPERIMENTAL programmable-surd machine (SPU-V03-SIM-0). Not Gen-1; not frozen.
// Specification: docs/design/SPU_V03_CONTRACT_CANDIDATE.md (FROZEN v0.3 ISA; image revision 0x03).
// Reserved (BAD_ENCODING): SRD 0x72 (retired in v0.3; gen1-surd keeps it), SSTAT 0x77, SMOV 0x7C, 0x7D-0x7F.
#ifndef SPU_PSURD_MACHINE_HPP
#define SPU_PSURD_MACHINE_HPP
#include "psurd_arith.hpp"
#include <array>
#include <vector>

namespace psurd {

enum Cause { HALT = 0, BAD_ENCODING = 1, INVALID = 2, ENGINE_FAULT = 3, BAD_TARGET = 4, PC_OVERRUN = 5, BUDGET = 6 };

struct Machine {
    std::vector<uint64_t> image;               // loaded words, 1 <= L <= 256
    bool image_valid = false;                  // contract §10: cleared by any refused LOAD
    std::array<Tuple, 8> s{};
    uint8_t init = 0, rcv = 0, st_target = 0, status = 0;
    std::array<uint32_t, 6> stage{};
    bool Z = 0, N = 0, P = 0, CV = 0, R = 0, RS = 0;
    uint32_t pc = 0, retired = 0, budget = 0;  // pc is the 9-bit architectural PC (0..256)
    Cause cause = HALT;

    void start(uint32_t b) {                   // draft §3.1 clean start
        s.fill(Tuple{0, 0, 1}); init = rcv = st_target = status = 0; stage.fill(0);
        Z = N = P = CV = R = RS = false; pc = retired = 0; budget = b;
    }
    bool rd(unsigned i) const { return (init >> i) & 1; }

    // Draft §2 exact field checks. Returns false for BAD_ENCODING.
    static bool well_formed(uint64_t w) {
        unsigned op = unsigned(w >> 56), r1 = unsigned((w >> 48) & 0xff), r2 = unsigned((w >> 40) & 0xff);
        uint64_t lo40 = w & ((1ULL << 40) - 1), lo24 = w & 0xffffffULL, b39_32 = (w >> 32) & 0xff, sb = (w >> 24) & 0xff;
        switch (op) {
            case 0x70: return r1 < 8 && r2 < 6 && (w & 0xff) == 0;                     // SLI
            case 0x71: return r1 < 8 && r2 == 0 && lo40 == 0;                           // SLD
            case 0x73: case 0x74: case 0x75:                                            // SMUL SADD SSUB
                return r1 < 8 && r2 < 8 && b39_32 == 0 && sb < 8 && lo24 == 0;
            case 0x76: return r1 < 8 && r2 < 8 && lo40 == 0;                            // SNORM
            case 0x78: return r1 < 8 && r2 == 0 && (w & 0xff) == 0;                     // SLIK
            case 0x79: return r1 == 0 && r2 < 8 && lo40 == 0;                           // STST
            case 0x7A: return r1 <= 9 && r2 == 0 && lo24 == 0;                          // BR
            case 0x7B: return w == 0x7B00000000000000ULL;                               // HALT
            default: return false;                                                      // incl. 0x72, 0x77, 0x7C-0x7F
        }
    }

    bool fault(Cause c) { cause = c; return false; }

    // Executes the word at pc. Returns true to continue; false when the run has ended (cause set).
    bool step() {
        uint64_t w = image[pc];
        if (!well_formed(w)) return fault(BAD_ENCODING);
        unsigned op = unsigned(w >> 56), d = unsigned((w >> 48) & 0xff), a = unsigned((w >> 40) & 0xff);
        unsigned b = unsigned((w >> 24) & 0xff);
        uint32_t next = pc + 1;
        switch (op) {
            case 0x70:                                                                  // SLI: staging only
                if (rcv && st_target != d) return fault(INVALID);
                st_target = uint8_t(d); stage[a] = uint32_t(w >> 8); rcv |= uint8_t(1u << a); break;
            case 0x71: {                                                                // SLD: atomic commit
                bool ok = rcv == 0x3f && st_target == d && (stage[4] | stage[5]) != 0;
                if (!ok) return fault(INVALID);
                s[d] = Tuple{stage[0] | uint64_t(stage[1]) << 32, stage[2] | uint64_t(stage[3]) << 32,
                             stage[4] | uint64_t(stage[5]) << 32};
                init |= uint8_t(1u << d); rcv = 0; stage.fill(0); break;
            }
            case 0x73: case 0x74: case 0x75: case 0x76: {                              // R-marked arithmetic
                if (!rd(a) || (op != 0x76 && !rd(b))) return fault(INVALID);
                Tuple out{};
                gen1::Status st = op == 0x73 ? gen1::smul(s[a], s[b], out)
                                : op == 0x76 ? norm(s[a], out) : add_sub(s[a], s[b], op == 0x75, out);
                status = uint8_t(st); R = st != gen1::OK; RS = RS || R;
                if (!R) { s[d] = out; init |= uint8_t(1u << d); }
                break;
            }
            case 0x78:                                                                  // SLIK
                s[d] = Tuple{uint64_t(int64_t(int32_t(uint32_t(w >> 8)))), 0, 1}; init |= uint8_t(1u << d); break;
            case 0x79: {                                                                // STST
                if (!rd(a)) return fault(INVALID);
                int g = sign(s[a]); Z = g == 0; N = g < 0; P = g > 0; CV = true; break;
            }
            case 0x7A: {                                                                // BR cc, t
                uint32_t t = uint32_t((w >> 24) & 0xffff);
                if (t >= image.size()) return fault(BAD_TARGET);
                if (d >= 1 && d <= 6 && !CV) return fault(INVALID);
                const bool take[10] = {true, Z, !Z, N, !N, P, !P, R, !R, RS};
                if (take[d]) next = t;
                break;
            }
            case 0x7B: ++retired; cause = HALT; return false;                          // HALT retires
        }
        ++retired; pc = next;
        return true;
    }

    void run(uint32_t b) {                     // draft §5.3-5.4; budget checked before PC_OVERRUN
        start(b);
        for (;;) {
            if (retired == budget) { cause = BUDGET; return; }
            if (pc >= image.size()) { cause = PC_OVERRUN; return; }
            if (!step()) return;
        }
    }

    // Contract §11 result record (provisional layout): 213 bytes.
    std::vector<uint8_t> record() const {
        std::vector<uint8_t> r = {0xA5, 0x03, 0x01, uint8_t(cause), uint8_t(pc), uint8_t(pc >> 8),
            uint8_t(Z | N << 1 | P << 2 | CV << 3 | R << 4 | RS << 5), status};
        auto le = [&](uint64_t v, int n) { for (int i = 0; i < n; ++i) r.push_back(uint8_t(v >> 8 * i)); };
        le(retired, 4); le(budget, 4); r.push_back(init);
        for (unsigned i = 0; i < 8; ++i) { const Tuple& t = s[i]; bool v = rd(i);
            le(v ? t.a : 0, 8); le(v ? t.b : 0, 8); le(v ? t.d : 0, 8); }
        le(gen1::crc32(r.data(), r.size()), 4);
        return r;
    }
};

}  // namespace psurd
#endif
