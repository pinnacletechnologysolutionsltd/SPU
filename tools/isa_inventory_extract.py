#!/usr/bin/env python3
"""ISA-V02-O6 source extractors: raw opcode/state records, no judgement.

Every extractor returns a list of plain dicts and keeps duplicate definitions
(dict-literal overwrite must not hide them). Classification lives in
tools/isa_inventory.py.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = "knowledge/isa_reference.md"
PY_VM = "software/spu_vm.py"
ASM = "software/tools/spu13_asm.py"
SURD_ENC = "software/tools/surd_cpu_encoding.py"
CPP_VM = "software/vm/spu_vm.cpp"
ISA_B_DEFS = "hardware/rtl/arch/spu_isa_defines.vh"
MATRIX = "docs/isa/ISA_IMPLEMENTATION_MATRIX.md"
RTL_CORE = "hardware/rtl/core/spu13/spu13_core.v"
RTL_SIDECARS = [
    "hardware/rtl/core/spu13/spu13_lucas_sidecar.v",
    "hardware/rtl/core/spu13/spu13_rplu2_sidecar.v",
    "hardware/rtl/core/spu13/spu13_rplu2_pade_sidecar.v",
    "hardware/rtl/core/spu13/spu13_neuro_sidecar_adapter.v",
    "hardware/rtl/core/spu13/spu13_su3_sidecar.v",
]


def _lines(rel):
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def _rec(source, profile, opcode, mnemonic, rel, line):
    return {"source": source, "profile": profile, "opcode": opcode,
            "mnemonic": mnemonic, "file": rel, "line": line}


def spec_records():
    out = []
    for n, text in enumerate(_lines(SPEC), 1):
        m = re.match(r"\|\s*\**0x([0-9A-Fa-f]{2})\**\s*\|\s*\**([A-Za-z0-9_]+)", text)
        if m:
            out.append(_rec("spec", "ISA-A", int(m[1], 16), m[2].upper(), SPEC, n))
    return out


def _dict_records(rel, varname, source, profile, surd=None):
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == varname:
            value = node.value
        elif isinstance(node, ast.Assign) and any(getattr(t, "id", "") == varname for t in node.targets):
            value = node.value
        else:
            continue
        for k, v in zip(value.keys, value.values):
            if k is None:  # `**SURD_OPCODES` spread
                out += [_rec(source, profile, op, name, SURD_ENC, line) for name, op, line in (surd or [])]
            else:
                out.append(_rec(source, profile, v.value, k.value, rel, k.lineno))
    return out


def surd_table():
    tree = ast.parse((ROOT / SURD_ENC).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "SURD_OPCODES":
            return [(k.arg, k.value.value, k.value.lineno) for k in node.value.keywords]
    return []


def vm_records():
    return _dict_records(PY_VM, "OPCODES", "python_vm", "ISA-A")


def asm_records():
    return (_dict_records(ASM, "OPCODES", "assembler", "ISA-A", surd_table())
            + _dict_records(ASM, "OPCODES_WF", "assembler_wf", "ISA-B/WF"))


def cpp_records():
    """`case 0xNN:` labels of the dispatch switch (after the register-validation switch)."""
    lines = _lines(CPP_VM)
    start = next(i for i, t in enumerate(lines) if "Build immediate" in t)
    out = []
    for i in range(start, len(lines)):
        if re.match(r"\s*default:", lines[i]) and "UNSUPPORTED" in "".join(lines[i:i + 3]):
            break
        m = re.search(r"case 0x([0-9A-Fa-f]{2}):\s*\{?\s*(?://\s*([A-Z0-9_]+))?", lines[i])
        if m:
            out.append(_rec("cpp_vm", "ISA-A", int(m[1], 16), m[2], CPP_VM, i + 1))
    return out


def rtl_records():
    out = []
    for rel in [RTL_CORE] + RTL_SIDECARS:
        for n, text in enumerate(_lines(rel), 1):
            m = re.search(r"localparam \[7:0\] OP_(\w+)\s*=\s*8'h([0-9A-Fa-f]{2})", text)
            if m:
                out.append(_rec("rtl:" + Path(rel).name, "ISA-A", int(m[2], 16), m[1], rel, n))
                continue
            m = re.search(r"63:56\]\s*==\s*8'h([0-9A-Fa-f]{2})\)?.*?(?://\s*([A-Z0-9_]+))?\s*$", text)
            if m and "[63:56] ==" in text.replace("  ", " "):
                out.append(_rec("rtl:" + Path(rel).name, "ISA-A", int(m[1], 16), m[2], rel, n))
    for n, text in enumerate(_lines(ISA_B_DEFS), 1):
        m = re.match(r"`define SPU_OP_(\w+)\s+8'h([0-9A-Fa-f]{2})", text)
        if m:
            out.append(_rec("rtl:spu_isa_defines.vh", "ISA-B/WF", int(m[2], 16), m[1], ISA_B_DEFS, n))
    return out


def matrix_rows():
    """Per-family claims: {line, family, mnemonics-cell, python_vm, cpp_vm, assembler}."""
    out = []
    for n, text in enumerate(_lines(MATRIX), 1):
        cells = [c.strip() for c in text.strip().strip("|").split("|")]
        if text.startswith("|") and len(cells) == 7 and not cells[0].startswith(("Feature", "---")):
            out.append({"line": n, "family": cells[0], "python_vm": cells[2],
                        "cpp_vm": cells[3], "assembler": cells[4]})
    return out
