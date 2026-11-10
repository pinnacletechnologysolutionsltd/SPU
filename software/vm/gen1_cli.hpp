// gen1_cli.hpp — explicit profile selection and the gen1-surd command line (SPU-GEN1-SIM-IMPL-0).
// Architectural interface: one 66-hex-character frame line on stdout (and optional raw 33 bytes).
// Diagnostic interface: optional JSON, labelled hardware_observable=false. Exit 0 = frame produced
// (success OR fault frame; inspect byte 2), 1 = usage or input error.
#ifndef SPU_GEN1_CLI_HPP
#define SPU_GEN1_CLI_HPP
#include "gen1_surd.hpp"
#include <cstdio>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

#ifndef GEN1_SOURCE_REVISION
#define GEN1_SOURCE_REVISION "unversioned"
#endif
#ifndef GEN1_SOURCE_SHA256
#define GEN1_SOURCE_SHA256 "unknown"
#endif
#ifndef GEN1_BUILD_ID
#define GEN1_BUILD_ID "unknown"
#endif

namespace gen1 {

inline std::string manifest() {   // docs/SIMULATOR_INTEGRATION_POLICY.md schema; certifies nothing
    const char* contract = "\"docs/GEN1_ARCHITECTURAL_CONTRACT.md@5948d8d5 sha256:"
                           "0e1c1566a52e24a9124165a19c4b1ac0a272cc8932a84a7e45d64782d08f2a2e\"";
    const char* rtl = "\"pass-scoped: RTL simulation of the frozen RTL, hardware/tests/spu13/gen1_integration "
                      "(599dbd0a; fixture sha256 3268eed2b374c5fdea7e3ac9ca78ac119fad059c8d1d0c98b4f8dfdefa01b832)\"";
    auto row = [&](const char* name, const char* support, bool impl, const char* physical, const char* extra) {
        std::ostringstream o;
        o << "\"" << name << "\":{\"support\":\"" << support << "\",\"semantic_contract\":"
          << (impl ? contract : "null") << ",\"tests\":[" << (impl ? "\"gen1_sim_conformance\"" : "")
          << "],\"conformance\":\"not_run\",\"evidence\":null,\"rtl_functional\":"
          << (impl && *physical ? rtl : "\"not_run\"") << ",\"physical\":"
          << (*physical ? physical : "\"not_run\"") << extra << "}";
        return o.str();
    };
    const char* phys = "\"observation (single-unit; success frames only): docs/hardware_evidence.md "
                       "3.40, 3.41, 3.43, 3.47, 3.49, 3.51\"";
    std::ostringstream o;
    o << "{\"schema_version\":1,\"implementation\":\"spu-vm-cpp\",\"profile\":\"gen1-surd\","
      << "\"source_revision\":\"" << GEN1_SOURCE_REVISION << "\",\"source_sha256\":\"" << GEN1_SOURCE_SHA256
      << "\",\"build_id\":\"" << GEN1_BUILD_ID << "\",\"capabilities\":{"
      << row("cpu.gen1-surd.fixed-rom-v1", "implemented", true, phys,
             ",\"instruction_patterns\":[\"SLI S0,s (70 00 0s pppppppp 00, s<6)\",\"SLD S0 (7100000000000000)\","
             "\"SMUL S0,S0,S0 (7300000000000000)\",\"SRD S0,s (72 00 0s 0000000000, s<6)\"]") << ","
      << row("uart.gen1-frame-v1", "implemented", true, phys, "") << ","
      << row("diagnostics.gen1-v1", "implemented", true, "", ",\"hardware_observable\":false") << ","
      << row("cpu.gen1-surd.registers-s1-s7", "unsupported", false, "", "") << ","
      << row("cpu.surd.sadd-ssub-snorm-sstat", "unsupported", false, "", "") << ","
      << row("cpu.control-flow", "unsupported", false, "", "") << ","
      << row("cpu.runtime-program-loading", "unsupported", false, "", "")
      << "},\"not_applicable\":{\"board.flash-boot\":\"FPGA configuration property, not a simulator "
         "capability; see docs/hardware_evidence.md\"}}";
    return o.str();
}

inline std::string diagnostics(const Run& r) {
    std::ostringstream o;
    auto sgn = [](uint64_t v) { return std::to_string(int64_t(v >> 63 ? -int64_t(~v) - 1 : int64_t(v))); };
    o << "{\"hardware_observable\":false,\"profile\":\"gen1-surd\",\"fault\":" << (r.fault ? "true" : "false")
      << ",\"pc\":" << r.pc << ",\"cause\":" << (r.cause.empty() ? "null" : "\"" + r.cause + "\"")
      << ",\"retires\":[";
    for (size_t i = 0; i < r.retires.size(); ++i)
        o << (i ? "," : "") << "[" << r.retires[i][0] << "," << r.retires[i][1] << "]";
    o << "],\"s0\":{\"initialized\":" << (r.s0_init ? "true" : "false") << ",\"a\":\"" << sgn(r.s0.a)
      << "\",\"b\":\"" << sgn(r.s0.b) << "\",\"d\":\"" << std::to_string(r.s0.d) << "\"}}";
    return o.str();
}

inline int fail(const std::string& m) { std::cerr << "gen1-surd: " << m << "\n"; return 1; }

inline int cli(const std::vector<std::string>& args) {   // args exclude argv[0] and --profile
    std::string rom_path, frame_out, diag_out;
    bool caps = false;
    for (size_t i = 0; i < args.size(); ++i) {
        const std::string& a = args[i];
        if (a == "--capabilities") caps = true;
        else if ((a == "--frame-out" || a == "--diag-out") && i + 1 < args.size())
            (a == "--frame-out" ? frame_out : diag_out) = args[++i];
        else if (!a.empty() && a[0] != '-' && rom_path.empty()) rom_path = a;
        else return fail("unsupported or repeated argument '" + a + "'");
    }
    if (caps) {
        if (!rom_path.empty() || !frame_out.empty() || !diag_out.empty())
            return fail("--capabilities takes no other arguments");
        std::cout << manifest() << "\n";
        return 0;
    }
    if (rom_path.empty()) return fail("usage: spu_vm --profile gen1-surd ROM.bin [--frame-out F] [--diag-out F]");
    std::ifstream f(rom_path, std::ios::binary);
    if (!f) return fail("cannot open " + rom_path);
    std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (bytes.size() != 128) return fail("ROM image must be exactly 128 bytes (16 big-endian words)");
    std::array<uint64_t, 16> rom{};
    for (int i = 0; i < 16; ++i)
        for (int k = 0; k < 8; ++k) rom[i] = (rom[i] << 8) | bytes[8 * i + k];
    Run r = execute(rom);
    char hex[67];
    for (int i = 0; i < 33; ++i) std::snprintf(hex + 2 * i, 3, "%02x", r.frame[i]);
    if (!frame_out.empty()) {
        std::ofstream o(frame_out, std::ios::binary);
        o.write(reinterpret_cast<const char*>(r.frame.data()), 33);
        if (!o) return fail("cannot write " + frame_out);
    }
    if (!diag_out.empty()) {
        std::ofstream o(diag_out);
        o << diagnostics(r) << "\n";
        if (!o) return fail("cannot write " + diag_out);
    }
    std::cout << hex << "\n";
    return 0;
}

// Strict selection. Returns -1 to continue the legacy path (argv possibly rewritten for
// "--profile legacy"); any other value is the process exit code. Never falls through silently.
inline int dispatch(int& argc, char**& argv, std::vector<char*>& keep) {
    std::vector<std::string> rest; std::string profile; int found = 0;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--profile" || a.rfind("--profile=", 0) == 0) {
            ++found;
            if (a == "--profile") { if (i + 1 >= argc) return fail("--profile requires a value"); profile = argv[++i]; }
            else profile = a.substr(10);
        } else rest.push_back(a);
    }
    if (found == 0) return -1;
    if (found > 1) return fail("--profile given more than once");
    if (profile == "gen1-surd") return cli(rest);
    if (profile != "legacy") return fail("unknown profile '" + profile + "' (known: legacy, gen1-surd)");
    keep.assign(1, argv[0]);
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--profile") { ++i; continue; }
        if (a.rfind("--profile=", 0) == 0) continue;
        keep.push_back(argv[i]);
    }
    keep.push_back(nullptr);
    argc = int(keep.size()) - 1; argv = keep.data();
    return -1;
}

}  // namespace gen1
#endif
