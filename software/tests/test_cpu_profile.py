#!/usr/bin/env python3
"""
test_cpu_profile.py -- CPU-PROFILE-2: Base SPU CPU (ENABLE_REGEN=0) VM profile contract.

Scope (deliberately narrow, no full-ISA or timing claim):
  * default VM profile is "full" and its historical REGEN pass-through is unchanged;
  * profile "base" makes REGEN (0x09) unsupported for every K: the instruction
    completes, mutates no architectural state, and latches a sticky fault
    (RTL: regen_debug_status[9], tested by spu13_core_regen_off_tb[regen_off]);
  * QLDI/QSUB/ROTC give identical results in both profiles AND equal the values
    the RTL committed (build log of spu13_core_regen_off_tb, constants below);
  * the capability manifest is deterministic and states the profile difference.
Cycle-level fault timing is NOT compared (the RTL completes REGEN immediately
in base; the VM has no cycle model).
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from spu_vm import SPUCore, capability_manifest, VM_PROFILES  # noqa: E402

M64 = (1 << 64) - 1


def qldi(lane, a, b, c, d):
    return (0x1D << 56) | (lane << 48) | ((a & 255) << 32) | ((b & 255) << 24) | ((c & 255) << 16) | ((d & 255) << 8)


def qsub(d, a, b):
    return (0x1B << 56) | (d << 48) | (a << 40) | (b << 8)


def rotc(d, s, ang):
    return (0x1C << 56) | (d << 48) | (s << 40) | (ang << 24)


def regen(k):
    return (0x09 << 56) | ((k & 0xFFFF) << 24)


def run(words, profile="full"):
    core = SPUCore(verbose=False, profile=profile)
    core.load(words)
    while core.step():
        pass
    return core


def qr_state(core):
    return [tuple((c.a, c.b) for c in q.components()) for q in core.qregs]


def snapshot(core):
    return (qr_state(core), [(r.a, r.b) for r in core.regs], list(core.qr_doubled),
            list(core.call_stack), core.snap_failures)


PHASE_A = [qldi(0, 3, 1, 0, 2), qldi(1, 1, 2, 5, 0), qsub(2, 0, 1), rotc(3, 0, 1), rotc(4, 1, 5)]
# Values committed by the RTL in spu13_core_regen_off_tb phase A (identical for
# ENABLE_REGEN=0 and 1); the same constants are hard-coded in that testbench.
RTL_PHASE_A = {0: (3, 1, 0, 2), 1: (1, 2, 5, 0), 2: (2, -1, -5, 2), 3: (3, 2, 0, 1), 4: (1, 5, 0, 2)}

results = {}


def case(fn):
    try:
        fn()
        results[fn.__name__] = "pass"
        print("PASS:", fn.__name__)
    except Exception as e:  # noqa: BLE001
        results[fn.__name__] = f"fail: {e!r}"
        print("FAIL:", fn.__name__, repr(e))
    return fn


@case
def default_profile_is_full_and_compatible():
    assert SPUCore(verbose=False).profile == "full"
    c = run(PHASE_A + [regen(5)])               # 5 eligible ops, K=5 -> clean pass
    assert c.regen_prec_fault is False and c.regen_block_count == 0 and not c.regen_unsupported
    c = run(PHASE_A + [regen(4)])               # mismatch -> REGEN_PREC fault, counter cleared
    assert c.regen_prec_fault is True and c.regen_block_count == 0 and not c.regen_unsupported
    c = run([regen(0)])                         # empty block -> clean pass (idempotence)
    assert c.regen_prec_fault is False


@case
def full_regen_passthrough():
    c = run(PHASE_A + [regen(5)], "full")
    assert not c.regen_prec_fault
    before = run(PHASE_A, "full")
    assert qr_state(c) == qr_state(before), "full-profile REGEN pass-through changed state"


@case
def base_regen_faults():
    for label, prog, k_matching_full in (
        ("matching K", PHASE_A + [regen(5)], True),
        ("K=0 empty block", [regen(0)], True),
        ("mismatched K", PHASE_A + [regen(9)], False),
    ):
        pre = run(prog[:-1], "base")
        assert pre.regen_block_count == 0, f"{label}: base must not count E_REGEN ops"
        c = run(prog, "base")
        assert c.regen_prec_fault is True and c.regen_unsupported is True, label
        assert snapshot(c) == snapshot(pre), f"{label}: REGEN mutated architectural state"
        assert c.regen_block_count == 0, f"{label}: base has no counter"
        assert c.pc == len(prog) and not c.fault_kind, f"{label}: must complete, not halt-fault"
        if k_matching_full:
            full = run(prog, "full")
            assert full.regen_prec_fault is False, f"{label}: full profile would pass here"
    # sticky: later valid operations do not clear it; a later REGEN keeps it
    c = run([regen(0), qldi(5, 1, 1, 1, 1), regen(0)], "base")
    assert c.regen_prec_fault and c.regen_unsupported
    # load() (the VM's reset analogue) clears it
    c.load([qldi(0, 1, 0, 0, 0)])
    assert not c.regen_prec_fault and not c.regen_unsupported


@case
def base_ops_equal_full_ops():
    prog = PHASE_A + [qldi(6, 2, 2, 2, 2), qsub(7, 6, 0)]
    assert snapshot(run(prog, "base")) == snapshot(run(prog, "full"))


@case
def vm_matches_rtl_trace():
    for profile in VM_PROFILES:
        c = run(PHASE_A, profile)
        for lane, want in RTL_PHASE_A.items():
            got = tuple(comp.a for comp in c.qregs[lane].components())
            assert all(comp.b == 0 for comp in c.qregs[lane].components()), (profile, lane)
            assert got == want, (profile, lane, got, want)


@case
def unknown_profile_rejected():
    for bad in ("", "FULL", "regen", None):
        try:
            SPUCore(verbose=False, profile=bad)
        except ValueError:
            continue
        raise AssertionError(f"profile {bad!r} accepted")
    try:
        capability_manifest("nope")
    except ValueError:
        return
    raise AssertionError("manifest accepted unknown profile")


@case
def manifest_deterministic_and_distinguishes_profiles():
    full1, full2 = capability_manifest("full"), capability_manifest("full")
    base1 = capability_manifest("base")
    assert json.dumps(full1, sort_keys=True) == json.dumps(full2, sort_keys=True)
    for m in (full1, base1):
        for key in ("schema_version", "implementation", "profile", "source_revision", "build_id", "capabilities"):
            assert key in m, key
        assert m["source_revision"].startswith("sha256:")
        for name, cap in m["capabilities"].items():
            for f in ("support", "semantic_contract", "tests", "conformance", "evidence",
                      "rtl_functional", "physical"):
                assert f in cap, (name, f)
            assert cap["conformance"] == "not_run" and cap["evidence"] is None, name
            assert cap["support"] in ("implemented", "experimental", "unsupported"), name
    assert full1["capabilities"]["regen_opcode_0x09"]["support"] == "implemented"
    assert base1["capabilities"]["regen_opcode_0x09"]["support"] == "unsupported"
    assert base1["capabilities"]["regen_stage_b_recovery"]["support"] == "unsupported"
    assert full1["capabilities"]["regen_stage_b_recovery"]["support"] == "unsupported"  # VM never models it
    assert "Stage A" in full1["capabilities"]["regen_opcode_0x09"]["scope"]
    assert base1["capabilities"]["qldi_qsub_rotc"]["physical"]["status"] == "not_run"
    assert full1["profile"] == "full" and base1["profile"] == "base"
    # every listed test identifier exists in this file
    src = open(__file__).read()
    for m in (full1, base1):
        for cap in m["capabilities"].values():
            for t in cap["tests"]:
                assert t.split("::")[1] in src, t


if __name__ == "__main__":
    out = os.environ.get("CPU_PROFILE_CONFORMANCE_OUT")
    if out:
        ident = {p: capability_manifest(p)["source_revision"] for p in VM_PROFILES}
        with open(out, "w") as f:
            json.dump({"source_revision": ident, "results": results}, f, indent=2, sort_keys=True)
    failed = [k for k, v in results.items() if v != "pass"]
    print(f"test_cpu_profile: {len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)
