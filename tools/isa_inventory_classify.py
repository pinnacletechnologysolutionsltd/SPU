#!/usr/bin/env python3
"""ISA-V02-O6 discrepancy classification over raw extractor records.

Coverage differences are not defects unless a contract claims otherwise (matrix row,
or the assembler header "must stay in sync with spu_vm.py").
"""
import re
from collections import defaultdict

import isa_inventory_extract as ex

CONFLICT = "CONFIRMED_ENCODING_CONFLICT"
MISSING = "MISSING_IN_CLAIMED_PROFILE"
EXTENSION = "DOCUMENTED_PROFILE_EXTENSION"
UNDOC = "UNDOCUMENTED_IMPLEMENTATION"
UNOWNED = "UNRESOLVED_PROFILE_OWNERSHIP"
SOFTWARE = ("python_vm", "cpp_vm", "assembler")


def _finding(cls, opcode, mnemonic, detail, refs):
    return {"class": cls, "opcode": None if opcode is None else f"0x{opcode:02X}",
            "mnemonic": mnemonic, "detail": detail, "refs": refs}


def _ref(r):
    return f"{r['source']}:{r['file']}:{r['line']}"


def isa_a_findings(records):
    isa_a = [r for r in records if r["profile"] == "ISA-A"]
    found, by_src_op, by_src_name = [], defaultdict(list), defaultdict(list)
    for r in isa_a:
        by_src_name[(r["source"], r["mnemonic"])].append(r)
        by_src_op[(r["source"], r["opcode"])].append(r)
    for (src, name), rs in by_src_name.items():
        if name and len({r["opcode"] for r in rs}) > 1:
            found.append(_finding(CONFLICT, None, name, f"{src} defines {name} with values "
                          + ",".join(f"0x{r['opcode']:02X}" for r in rs) + " (later entry wins in a dict)",
                          [_ref(r) for r in rs]))
    spec = {r["mnemonic"]: r for r in isa_a if r["source"] == "spec"}
    for r in isa_a:
        s = spec.get(r["mnemonic"])
        if r["source"] != "spec" and s and s["opcode"] != r["opcode"]:
            found.append(_finding(CONFLICT, r["opcode"], r["mnemonic"],
                          f"{r['source']} has 0x{r['opcode']:02X}, spec has 0x{s['opcode']:02X}", [_ref(r), _ref(s)]))
    spec_ops = {r["opcode"] for r in isa_a if r["source"] == "spec"}
    names_by_op = defaultdict(set)
    for r in isa_a:
        if r["source"] in ("spec", "python_vm", "assembler", "cpp_vm") and r["mnemonic"]:
            names_by_op[r["opcode"]].add(r["mnemonic"])
    for op, names in names_by_op.items():
        if len(names) > 1 and op in spec_ops:
            found.append(_finding(CONFLICT, op, "/".join(sorted(names)), "one value, several mnemonics", []))
    return found, spec_ops


def coverage_findings(records, spec_ops, matrix_cells):
    isa_a = [r for r in records if r["profile"] == "ISA-A"]
    have = defaultdict(set)
    for r in isa_a:
        have[r["source"]].add(r["opcode"])
    names = {r["opcode"]: r["mnemonic"] for r in isa_a if r["source"] in ("spec", "python_vm") and r["mnemonic"]}
    found = []
    for op in sorted(have["python_vm"] - have["assembler"]):
        found.append(_finding(MISSING, op, names.get(op), "assembler header claims sync with spu_vm.py OPCODES; "
                      "not in assembler table", [ex.ASM + ":56"]))
    for src, cell in matrix_cells:
        op, label, col = cell
        present = op in have[col]
        if label.startswith("implemented") and not present:
            found.append(_finding(MISSING, op, names.get(op), f"matrix says {col}='{label}' but opcode absent", []))
        if label.startswith("absent") and present:
            found.append(_finding(MISSING, op, names.get(op), f"matrix says {col}='absent' but opcode present", []))
    flagged = {(f["opcode"], "assembler") for f in found if f["class"] == MISSING}
    for op in sorted(spec_ops):
        absent = [s for s in SOFTWARE if op not in have[s] and (f"0x{op:02X}", s) not in flagged]
        if absent:
            found.append(_finding(EXTENSION, op, names.get(op), "in spec; no contract claims support in "
                          + ",".join(absent), []))
    return found


def matrix_cells(matrix, spec_names):
    """Expand matrix rows into (source,(opcode,label,column)) for rows with known mnemonics."""
    out, cols = [], {"python_vm": "python_vm", "cpp_vm": "cpp_vm", "assembler": "assembler"}
    for row in matrix:
        if "ISA-B" in row["family"]:
            continue
        for tok in re.findall(r"[A-Z][A-Z0-9_]+", row["family"]):
            if tok in spec_names:
                for col in cols:
                    out.append((row["line"], (spec_names[tok], row[col].lower(), col)))
    return out


def rtl_findings(records, spec_ops):
    found, seen = [], set()
    names = {r["opcode"]: r["mnemonic"] for r in records
             if r["source"] in ("spec", "python_vm") and r["profile"] == "ISA-A"}
    for r in records:
        if not r["source"].startswith("rtl:") or r["profile"] != "ISA-A":
            continue
        key = (r["source"], r["opcode"])
        if key in seen:
            continue
        seen.add(key)
        known = names.get(r["opcode"])
        if known and r["mnemonic"] and known != r["mnemonic"]:
            found.append(_finding(UNOWNED, r["opcode"], r["mnemonic"],
                          f"candidate overlap: {r['source']} names 0x{r['opcode']:02X} {r['mnemonic']}; "
                          f"spec/VM name it {known}", [_ref(r)]))
        elif not known:
            found.append(_finding(UNOWNED, r["opcode"], r["mnemonic"],
                          f"{r['source']} decodes opcode absent from spec/VM/assembler/C++", [_ref(r)]))
    return found


def isa_a_namespace_notes(records):
    isa_b = {r["opcode"] for r in records if r["profile"] == "ISA-B/WF"}
    isa_a = {r["opcode"] for r in records if r["profile"] == "ISA-A" and r["source"] == "spec"}
    return [_finding(UNOWNED, None, "ISA-B/WF namespace",
                     f"{len(isa_b & isa_a)} numeric values overlap ISA-A; treated as a distinct namespace, "
                     "no cross-profile conflict asserted", [ex.ISA_B_DEFS])]
