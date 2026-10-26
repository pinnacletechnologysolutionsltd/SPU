#!/usr/bin/env python3
"""ISA-V02-O6 inventory generator and discrepancy classifier.

  python3 tools/isa_inventory.py --out docs/isa/isa_v02_o6_inventory.json
  python3 tools/isa_inventory.py --check docs/isa/isa_v02_o6_inventory.json

Reads sources only; changes no opcode, RTL or document. Coverage differences
are not defects unless a contract claims otherwise (matrix row, or the
assembler header "must stay in sync with spu_vm.py").
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import isa_inventory_extract as ex  # noqa: E402
from isa_inventory_classify import (  # noqa: E402
    coverage_findings, isa_a_findings, isa_a_namespace_notes, matrix_cells, rtl_findings)
from isa_inventory_state import state_inventory  # noqa: E402


def support_table(records):
    """opcode -> {source: mnemonic-or-None} for ISA-A; the per-implementation claim surface."""
    table = defaultdict(dict)
    for r in records:
        if r["profile"] == "ISA-A":
            table[f"0x{r['opcode']:02X}"].setdefault(r["source"], r["mnemonic"])
    return dict(sorted(table.items()))


def build():
    records = (ex.spec_records() + ex.vm_records() + ex.asm_records()
               + ex.cpp_records() + ex.rtl_records())
    by_value = {}
    for r in records:
        if r["source"] in ("spec", "python_vm"):
            by_value.setdefault(r["opcode"], r["mnemonic"])
    for r in records:
        if r["source"].startswith("rtl:") and r["profile"] == "ISA-A" and not r["mnemonic"]:
            r["mnemonic"] = by_value.get(r["opcode"])
            r["mnemonic_source"] = "spec/python_vm-by-value" if r["mnemonic"] else "none"
    findings, spec_ops = isa_a_findings(records)
    spec_names = {r["mnemonic"]: r["opcode"] for r in records if r["source"] == "spec"}
    cells = matrix_cells(ex.matrix_rows(), spec_names)
    findings += coverage_findings(records, spec_ops, [(c[0], c[1]) for c in cells])
    findings += rtl_findings(records, spec_ops)
    findings += isa_a_namespace_notes(records)
    findings.sort(key=lambda f: (f["class"], f["opcode"] or "", f["mnemonic"] or ""))
    return {"schema": "isa-v02-o6/1", "records": records, "findings": findings, "support": support_table(records),
            "state": state_inventory(), "matrix_rows": ex.matrix_rows()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--check")
    args = ap.parse_args(argv)
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    if args.check:
        if Path(args.check).read_text(encoding="utf-8") != text:
            print("FAIL: inventory differs from frozen " + args.check)
            return 1
        print("PASS: inventory matches frozen " + args.check)
    if not (args.out or args.check):
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
