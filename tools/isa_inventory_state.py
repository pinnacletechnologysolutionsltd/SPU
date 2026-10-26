#!/usr/bin/env python3
"""ISA-V02-O6 architectural-state inventory: documented registers, flags, faults.

Per-profile entries carry file:line references. Anything not directly evidenced
in that profile's own source is UNRESOLVED; nothing is inferred from a similarly
named item in another implementation.
"""
import re
import isa_inventory_extract as ex

UNRESOLVED = "UNRESOLVED"


def _grep(rel, pattern):
    return [(n, m) for n, t in enumerate(ex._lines(rel), 1) for m in [re.search(pattern, t)] if m]


def _entry(profile, item, value, refs, note=""):
    return {"profile": profile, "item": item, "value": value, "refs": refs, "note": note}


def registers():
    out = []
    for rel, prof in ((ex.PY_VM, "python_vm"), (ex.CPP_VM, "cpp_vm")):
        for n, m in _grep(rel, r"NUM_REGS\s*=\s*(\d+)"):
            out.append(_entry(prof, "scalar registers", f"R0..R{int(m[1]) - 1}", [f"{rel}:{n}"]))
    for n, m in _grep(ex.SPEC, r"Destination register \(scalar (R0.R\d+) or (QR0.QR\d+)\)"):
        out.append(_entry("spec", "scalar / quadray registers", f"{m[1]} / {m[2]}", [f"{ex.SPEC}:{n}"]))
    for n, m in _grep(ex.SPEC, r"Eight independent (S0.S7) entries"):
        out.append(_entry("spec", "surd tuple registers (ENABLE_SURD_CPU)", m[1], [f"{ex.SPEC}:{n}"]))
    out.append(_entry("rtl:spu13_core.v", "register file widths", UNRESOLVED, [],
                      "not extracted; multi-core RTL register organisation needs its own audit"))
    return out


def flags():
    out = []
    for n, t in enumerate(ex._lines(ex.SPEC), 1):
        m = re.match(r"\|\s*\**(\d)\**\s*\|\s*\**([A-Z_]+)\**\s*\|\s*\**([^|]+?)\**\s*\|", t)
        if m and m[2] in {"Z", "C", "V", "MISALIGNED", "OVERFLOW", "INEXACT"}:
            out.append(_entry("spec", f"FLAGS[{m[1]}] {m[2]}", f"set by {m[3]}", [f"{ex.SPEC}:{n}"]))
    for rel, prof in ((ex.PY_VM, "python_vm"), (ex.CPP_VM, "cpp_vm")):
        has = _grep(rel, r"\bself\.flags\b|\bflags\s*=|FLAGS\s*=")
        out.append(_entry(prof, "FLAGS word readable via SNAP",
                          "present" if has else UNRESOLVED, [f"{rel}:{n}" for n, _ in has],
                          "" if has else "spec says SNAP reads FLAGS; this VM's SNAP is a Davis-gate "
                          "scan with no FLAGS word"))
    for n, m in _grep("hardware/rtl/core/spu13/spu13_fp4_inverter.v", r"output reg\s+flags_v"):
        out.append(_entry("rtl:spu13_fp4_inverter.v", "flags_v (zero-norm)", "output pin",
                          [f"hardware/rtl/core/spu13/spu13_fp4_inverter.v:{n}"],
                          "no opcode routes this to FLAGS[2]; A31 inverse has no encoding in any ISA-A table"))
    return out


def faults():
    out = []
    for n, m in _grep(ex.CPP_VM, r'VmFault\("([A-Z_]+)"'):
        out.append(_entry("cpp_vm", "fault kind", m[1], [f"{ex.CPP_VM}:{n}"]))
    for n, m in _grep(ex.PY_VM, r'fault_kind\s*=\s*"([A-Z_]+)"'):
        out.append(_entry("python_vm", "fault kind", m[1], [f"{ex.PY_VM}:{n}"]))
    for n, m in _grep(ex.PY_VM, r"^class (\w+(?:Error))\("):
        out.append(_entry("python_vm", "exception class", m[1], [f"{ex.PY_VM}:{n}"]))
    for n, m in _grep(ex.SPEC, r"Status codes: (.+?)\."):
        out.append(_entry("spec", "surd SSTAT codes", m[1], [f"{ex.SPEC}:{n}"]))
    out.append(_entry("python_vm/cpp_vm", "fault precedence and refusal post-state per opcode", UNRESOLVED, [],
                      "only Gram v1 SPREAD has a frozen contract (research/sim_cap1_spread)"))
    return out


def transitions():
    return [_entry("all", "machine-state transition table (fetch/PC/stack/halt)", UNRESOLVED, [],
                   "core fetch/PC/stack not established in inspected main RTL core per ISA_IMPLEMENTATION_MATRIX.md")]


def state_inventory():
    return {"registers": registers(), "flags": flags(), "faults": faults(), "transitions": transitions()}
