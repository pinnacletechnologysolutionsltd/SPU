// psurd_cli.hpp — command line for the EXPERIMENTAL programmable-surd profile (SPU-V03-SIM-0).
// Image envelope (draft §8.1, provisional SIM-0 layout), all integers little-endian except words:
//   "SPUI" | profile 0x01 | contract revision 0x03 | L (u16) | CRC-32 of the word bytes (u32) | L words, big-endian.
// Output: one result-record hex line per START (contract §11). Exit 0 = record(s) produced, 1 = refused/usage.
// Session mode (--do load:PATH | --do start, repeatable): one line per step; refusals are responses (exit 0).
#ifndef SPU_PSURD_CLI_HPP
#define SPU_PSURD_CLI_HPP
#include "gen1_cli.hpp"
#include "psurd_machine.hpp"

namespace psurd {

inline std::string manifest() {   // docs/SIMULATOR_INTEGRATION_POLICY.md schema; certifies nothing
    const char* spec = "\"docs/design/SPU_V03_CONTRACT_CANDIDATE.md (FROZEN v0.3 ISA 2026-11-11; image revision 0x03)\"";
    // physical: docs/hardware_evidence.md §3.53 (one RTL-0C session, one unit; a silicon observation, not a
    // qualification). Each string states what that session executed; nothing outside it is claimed.
    auto row = [&](const char* name, const char* physical, const char* extra) {
        return std::string("\"") + name + "\":{\"support\":\"experimental\",\"semantic_contract\":" + spec +
               ",\"tests\":[\"psurd_sim0\"],\"conformance\":\"not_run\",\"evidence\":null,"
               "\"rtl_functional\":\"not_run\",\"physical\":\"" + physical + "\"" + extra + "}";
    };
    std::ostringstream o;
    o << "{\"schema_version\":1,\"implementation\":\"spu-vm-cpp\",\"profile\":\"programmable-surd\","
      << "\"status\":\"experimental\",\"gen1_conformant\":false,\"isa_frozen\":true,\"rtl_qualified\":false,\"fpga_demonstrated\":true,"
      << "\"fpga_evidence\":\"docs/hardware_evidence.md §3.53 (single session, one unit; not a qualification)\",\"image_revision\":3,"
      << "\"source_revision\":\"" << GEN1_SOURCE_REVISION << "\",\"source_sha256\":\"" << GEN1_SOURCE_SHA256
      << "\",\"build_id\":\"" << GEN1_BUILD_ID << "\",\"capabilities\":{"
      << row("cpu.psurd.registers-s0-s7", "partial: §3.53 wrote S0-S5 and S7; S6 not exercised", "") << ","
      << row("cpu.psurd.arith-smul-sadd-ssub-snorm",
             "partial: §3.53 executed SMUL and SSUB, including recoverable OVERFLOW (R and RS); SADD and SNORM not executed",
             ",\"refusal\":\"recoverable OVERFLOW (R, sticky RS)\"") << ","
      << row("cpu.psurd.sign-test-and-branch",
             "partial: §3.53 executed STST and BR AL, EQ, LT, GT, RF, RS; NE, GE, LE, NR not exercised", "") << ","
      << row("cpu.psurd.image-load-v0", "observed: §3.53 loads accepted; wrong CRC and revision 0x02 refused", "") << ","
      << row("cpu.psurd.result-record-v0", "observed: §3.53 returned 19 records over UART, byte-identical to expectations",
             ",\"hardware_observable\":true")
      << "},\"unsupported\":[\"SRD (0x72, retired in v0.3)\",\"SMOV (0x7C)\",\"SSTAT (0x77)\",\"domains other than Q(sqrt3)\"]}";
    return o.str();
}

inline int fail(const std::string& m) { std::cerr << "programmable-surd: " << m << "\n"; return 1; }

// Loader (draft §8.1): framing, length, identity and CRC. Instructions are NOT decoded here.
inline bool load(const std::vector<unsigned char>& f, Machine& m, std::string& why) {
    m.image_valid = false;                       // any recognized LOAD attempt invalidates the old image
    if (f.size() < 12 || std::string(f.begin(), f.begin() + 4) != "SPUI") { why = "bad framing"; return false; }
    if (f[4] != 0x01 || f[5] != 0x03) { why = "architecture identity mismatch"; return false; }   // 0x02 (SIM-0, SRD) refused
    size_t L = f[6] | size_t(f[7]) << 8;
    if (L < 1 || L > 256 || f.size() != 12 + 8 * L) { why = "bad length"; return false; }
    uint32_t crc = f[8] | uint32_t(f[9]) << 8 | uint32_t(f[10]) << 16 | uint32_t(f[11]) << 24;
    if (gen1::crc32(f.data() + 12, 8 * L) != crc) { why = "CRC mismatch"; return false; }
    m.image.assign(L, 0);
    for (size_t i = 0; i < L; ++i)
        for (int k = 0; k < 8; ++k) m.image[i] = (m.image[i] << 8) | f[12 + 8 * i + k];
    m.image_valid = true;
    return true;
}

inline std::string hexrec(const std::vector<uint8_t>& r) {
    std::string h; char b[3];
    for (uint8_t x : r) { std::snprintf(b, 3, "%02x", x); h += b; }
    return h;
}

inline bool read_file(const std::string& p, std::vector<unsigned char>& out) {
    std::ifstream f(p, std::ios::binary);
    if (!f) return false;
    out.assign((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    return true;
}

// Contract §9-§10 session: LOAD/START responses in order on one machine (runs are synchronous here,
// so LOAD/START-while-busy cannot arise in software; that case is an RTL-0 requirement).
inline int session(const std::vector<std::string>& steps, uint32_t budget) {
    Machine m; std::vector<unsigned char> bytes; std::string why;
    for (const std::string& s : steps) {
        if (s == "start") {
            if (!m.image_valid) { std::cout << "START REFUSED: no valid image\n"; continue; }
            m.run(budget); std::cout << hexrec(m.record()) << "\n";
        } else if (s.rfind("load:", 0) == 0) {
            if (!read_file(s.substr(5), bytes)) return fail("cannot open " + s.substr(5));
            if (load(bytes, m, why)) std::cout << "LOAD OK\n"; else std::cout << "LOAD REFUSED: " << why << "\n";
        } else return fail("bad --do step '" + s + "'");
    }
    return 0;
}

inline int cli(const std::vector<std::string>& args) {   // args exclude argv[0] and --profile
    std::string path, rec_out; long long budget = -1, repeat = 1; bool caps = false;
    std::vector<std::string> steps;
    for (size_t i = 0; i < args.size(); ++i) {
        const std::string& a = args[i];
        if (a == "--capabilities") caps = true;
        else if ((a == "--budget" || a == "--repeat") && i + 1 < args.size()) {
            try { size_t n; long long v = std::stoll(args[++i], &n); if (n != args[i].size()) throw 0;
                  (a == "--budget" ? budget : repeat) = v; } catch (...) { return fail("bad number for " + a); }
        } else if (a == "--record-out" && i + 1 < args.size()) rec_out = args[++i];
        else if (a == "--do" && i + 1 < args.size()) steps.push_back(args[++i]);
        else if (!a.empty() && a[0] != '-' && path.empty()) path = a;
        else return fail("unsupported or repeated argument '" + a + "'");
    }
    if (caps) {
        if (!path.empty() || budget >= 0 || !rec_out.empty()) return fail("--capabilities takes no other arguments");
        std::cout << manifest() << "\n"; return 0;
    }
    if (!steps.empty()) {
        if (!path.empty() || !rec_out.empty() || repeat != 1) return fail("--do excludes IMAGE, --record-out and --repeat");
        if (budget < 1 || budget > 0xffffffffLL) return fail("START refused: budget must be 1..2^32-1");
        return session(steps, uint32_t(budget));
    }
    if (path.empty() || budget < 0)
        return fail("usage: spu_vm --profile programmable-surd IMAGE --budget B [--repeat N] [--record-out F]");
    if (budget < 1 || budget > 0xffffffffLL) return fail("START refused: budget must be 1..2^32-1");
    if (repeat < 1 || repeat > 16) return fail("--repeat must be 1..16");
    std::vector<unsigned char> bytes;
    if (!read_file(path, bytes)) return fail("cannot open " + path);
    Machine m; std::string why;
    if (!load(bytes, m, why)) return fail("image refused: " + why);
    std::vector<uint8_t> last;
    for (long long k = 0; k < repeat; ++k) {     // each START is a clean start of the same machine
        m.run(uint32_t(budget)); last = m.record();
        std::cout << hexrec(last) << "\n";
    }
    if (!rec_out.empty()) {
        std::ofstream o(rec_out, std::ios::binary);
        o.write(reinterpret_cast<const char*>(last.data()), std::streamsize(last.size()));
        if (!o) return fail("cannot write " + rec_out);
    }
    return 0;
}

// Claims only an unambiguous, single "--profile programmable-surd". Everything else (absent, other,
// duplicate or malformed profiles) returns -1 so gen1::dispatch handles it unchanged.
inline int dispatch(int argc, char** argv) {
    std::vector<std::string> rest; int found = 0; bool mine = false;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--profile" || a.rfind("--profile=", 0) == 0) {
            ++found;
            std::string v = a == "--profile" ? (i + 1 < argc ? argv[++i] : "") : a.substr(10);
            mine = v == "programmable-surd";
        } else rest.push_back(a);
    }
    if (found != 1 || !mine) return -1;
    return cli(rest);
}

}  // namespace psurd
#endif
