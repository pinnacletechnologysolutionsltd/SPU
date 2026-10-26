#!/usr/bin/env python3
"""ISA-V02-O6 inventory tests: extractor fidelity, classifier controls, frozen inventory.

Existing discrepancies are recorded, not suppressed: the live CONFLICT set is
asserted equal to a known list, so repairing (or adding) one fails this test until
docs/isa/isa_v02_o6_inventory.json is deliberately regenerated:

  python3 tools/isa_inventory.py --out docs/isa/isa_v02_o6_inventory.json

Run:  python3 software/tests/test_isa_inventory.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import isa_inventory as inv  # noqa: E402
import isa_inventory_classify as cls  # noqa: E402
import isa_inventory_extract as ex  # noqa: E402

FROZEN = ROOT / "docs/isa/isa_v02_o6_inventory.json"
KNOWN_CONFLICTS = {
    ("POLY_STEP", None), ("POLY_STEP", "0xE0"),
}


def rec(source, op, name, profile="ISA-A", line=1):
    return {"source": source, "profile": profile, "opcode": op, "mnemonic": name, "file": "f", "line": line}


def classes(findings):
    return [f["class"] for f in findings]


def test_extractor_keeps_duplicate_keys():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.py"
        p.write_text('OPCODES = {"A": 0x01, "B": 0x02, "A": 0x03}\n')
        out = ex._dict_records(str(p), "OPCODES", "python_vm", "ISA-A")
    assert [(r["mnemonic"], r["opcode"]) for r in out] == [("A", 1), ("B", 2), ("A", 3)], out


def test_classifier_flags_in_source_duplicate_and_spec_mismatch():
    recs = [rec("spec", 0x60, "X"), rec("python_vm", 0x60, "X"), rec("python_vm", 0xE0, "X")]
    found, _ = cls.isa_a_findings(recs)
    assert classes(found).count(cls.CONFLICT) == 2, found  # duplicate + spec mismatch


def test_classifier_quiet_on_consistent_records():
    recs = [rec("spec", 1, "ADD"), rec("python_vm", 1, "ADD"), rec("assembler", 1, "ADD"), rec("cpp_vm", 1, "ADD")]
    found, _ = cls.isa_a_findings(recs)
    assert found == [], found


def test_one_value_two_mnemonics_is_conflict():
    recs = [rec("spec", 5, "P"), rec("python_vm", 5, "Q")]
    found, _ = cls.isa_a_findings(recs)
    assert cls.CONFLICT in classes(found)


def test_missing_vs_extension_separation():
    recs = [rec("spec", 7, "OP"), rec("python_vm", 7, "OP")]
    found = cls.coverage_findings(recs, {7}, [])
    kinds = {(f["class"], f["detail"].split(" in ")[-1]) for f in found}
    assert (cls.MISSING, "assembler header claims sync with spu_vm.py OPCODES; not in assembler table") in {
        (f["class"], f["detail"]) for f in found}
    assert any(c == cls.EXTENSION for c, _ in kinds), found  # cpp_vm absence is not a defect


def test_matrix_claim_mismatch_detected():
    recs = [rec("spec", 9, "R"), rec("python_vm", 9, "R")]
    claims = [(1, (9, "implemented", "cpp_vm")), (1, (9, "absent", "python_vm"))]
    details = " ".join(f["detail"] for f in cls.coverage_findings(recs, {9}, claims))
    assert "cpp_vm='implemented' but opcode absent" in details
    assert "python_vm='absent' but opcode present" in details


def test_isa_b_namespace_not_cross_compared():
    recs = [rec("spec", 0x20, "CALL"), rec("assembler_wf", 0x20, "QADD", "ISA-B/WF")]
    found, _ = cls.isa_a_findings(recs)
    assert found == [], found


def test_live_conflicts_are_the_known_set():
    live = {(f["mnemonic"], f["opcode"]) for f in inv.build()["findings"] if f["class"] == cls.CONFLICT}
    assert live == KNOWN_CONFLICTS, live


def test_live_sources_nonempty():
    assert len(ex.spec_records()) > 40 and len(ex.vm_records()) > 35
    assert len(ex.cpp_records()) > 20 and len(ex.asm_records()) > 80 and len(ex.matrix_rows()) == 15
    ops = {r["opcode"] for r in ex.asm_records() if r["source"] == "assembler"}
    assert {0x70, 0x77} <= ops  # **SURD_OPCODES spread is resolved


def test_frozen_inventory_unchanged():
    assert json.loads(FROZEN.read_text()) == json.loads(json.dumps(inv.build())), \
        "inventory changed; regenerate docs/isa/isa_v02_o6_inventory.json deliberately"


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                failed += 1
                print("FAIL", name, e)
    print("FAIL" if failed else "PASS", f"{failed} failed")
    sys.exit(1 if failed else 0)
