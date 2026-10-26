"""Pinned reference loading and the contract §4 field mappings. References are read-only and hash-verified."""
import hashlib
import json
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # research/qcg_0
PINS = {
    "QUINTIC_FIXTURE_VALUES.json": "8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34",
    "REVISION2_FIXTURE_VALUES.json": "a66af3d68da5a7dba439818778af9e8fe70244e3dc2d8250ea891354124a0b46",
    "P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json": "9422d7617c65a9a3fc2fa1ab19af7ce7ea634721cfeb251096cd3821534237a0",
    "P0_CONTRACT_R2_LEDGER_STAGE_EXPECTATIONS.json": "093b006b4b11e289066265a9021fba92c28ec252b8df44eac06a48f8eeca75bb",
    "P0_CONTRACT_R2_REMAINING_CELL_A_STAGE_EXPECTATIONS.json": "d231a81305f975727b82431bb04a51dff41fbc55a85708a8521c63c36edf6a0a",
}
_cache = {}


def load(name):
    if name not in _cache:
        raw = (ROOT / name).read_bytes()
        got = hashlib.sha256(raw).hexdigest()
        if got != PINS[name]:
            raise RuntimeError("reference pin mismatch: %s" % name)
        _cache[name] = json.loads(raw)
    return _cache[name]


def source(curve):
    """Certified generator (U, V) as lists of [n, d] pairs; h = 1, r_0 = (0, 0)."""
    p = load("QUINTIC_FIXTURE_VALUES.json")[curve]
    return {"U": p["U"], "V": p["V"]}


def poly(curve, name):
    return load("QUINTIC_FIXTURE_VALUES.json")[curve][name]


def phi():
    c = load("QUINTIC_FIXTURE_VALUES.json")["cell_B"]
    return {"phi": c["phi"], "phi_prime": c["phi_prime"]}


def cell_a_ref():
    """Per query: (t pair, 9 output pairs with the TRUE curvature numerator at index 7, ok).
    Primary: the Revision 2 adapted file (already doubled; never doubled again). Cross-check: the original file
    with raw N at index 7 doubled exactly once. The two must agree."""
    ad = load("REVISION2_FIXTURE_VALUES.json")["CellA_adapted_true_curvature_pair"]
    og = load("QUINTIC_FIXTURE_VALUES.json")["cell_A"]
    rows = []
    for a, o in zip(ad, og):
        v = [tuple(x) for x in o["values"]]
        n, d = v[7]
        g = gcd(abs(2 * n), d)
        v[7] = (2 * n // g, d // g)                         # double the original raw N exactly once (canonical form)
        assert [tuple(x) for x in a["values"]] == v and a["t"] == o["t"], "Cell A reference mapping disagrees"
        rows.append((tuple(a["t"]), [tuple(x) for x in a["values"]], a["D_nonzero"]))
    return rows


def cell_b_ref():
    return [(tuple(r["t"]), [tuple(x) for x in r["values"]]) for r in load("QUINTIC_FIXTURE_VALUES.json")["cell_B"]["rows"]]


def seq_ref(curve):
    """Rows k = 0..16: S1 (x, y); S2_add (x', y', sigma, Tx, Ty); the true curvature quotient; next increment (or None)."""
    return load("QUINTIC_FIXTURE_VALUES.json")["sequential"][curve]


def stage_cell_a():
    """Reviewer-certified W31 first refusals for Cell A (read from the pinned JSON; never derived here)."""
    return load("P0_CONTRACT_R2_LEDGER_STAGE_EXPECTATIONS.json"), load("P0_CONTRACT_R2_REMAINING_CELL_A_STAGE_EXPECTATIONS.json")
