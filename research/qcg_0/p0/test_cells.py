"""EQ-1..EQ-3, hand counts, certified W31 Cell A events, oracles (contract §7/§8). Collected by test_p0.py."""
from fractions import Fraction as F
import campaign, conform, o1, o2, refs
from events import P4096, W31
from test_lu import test


@test
def eq3_cells_p4096():
    a, _ = campaign.cell_a(P4096)
    assert [r["mismatches"] for r in a] == [0] * 7, [(r["arm"], r["mismatches"]) for r in a]
    assert [r["mismatches"] for r in campaign.cell_b(P4096)] == [0] * 5
    s = campaign.seq(P4096)
    assert len(s) == 48 and sum(r["mismatches"] for r in s) == 0 and all(r["prep"] is None for r in s)


@test
def hand_counts_and_equivalence():
    a, _ = campaign.cell_a(P4096)
    by = {r["arm"]: r for r in a}
    assert conform.prep_targets(a) == []
    q = {n: (by[n]["Q"]["M"], by[n]["Q"]["A"], by[n]["Q"]["S"], by[n]["Q"]["K"]) for n in by}
    assert q["B-Horner"] == (28 * 16, 27 * 16, 0, 16) and q["B-PH"] == (26 * 16, 23 * 16, 2 * 16, 16)
    for k in ("P", "Q", "peaks", "attempt"):
        assert by["C1"][k] == by["B-PH"][k], k                               # EQ-1
    assert conform.q_division_free(a) == [] and by["B-FD"]["statuses"] == ["NOT_APPLICABLE"] * 16
    b = {r["arm"]: r for r in campaign.cell_b(P4096)}
    assert (b["B-COMP"]["Q"]["M"], b["B-COMP"]["Q"]["A"]) == (21 * 16, 18 * 16)
    assert (b["C1"]["Q"]["M"], b["C1"]["Q"]["A"], b["C1"]["Q"]["S"]) == (33 * 16, 31 * 16, 16)


@test
def eq2_sequential():
    s = campaign.seq(P4096)
    for curve in ("PH3", "PH5"):
        for tape in ("S1", "S2", "S3"):
            by = {r["arm"]: r for r in s if r["curve"] == curve and r["tape"] == tape}
            for k in ("P", "Q", "peaks", "attempt"):
                assert by["C1"][k] == by["PHFD"][k], (curve, tape, k)


@test
def w31_cell_a_certified_events():
    assert conform.w31_cell_a() == []
    s = campaign.seq(W31)
    assert all(r["mismatches"] == 0 for r in s)            # a halted tape never emits a wrong-grid OK sample


@test
def oracles_agree_with_pinned_rows():
    s = refs.source("PH5")
    for t, vals, _ in refs.cell_a_ref():
        for o in (o1, o2):
            assert o.cell_a(s["U"], s["V"], F(*t)) == [F(*v) for v in vals]
    s, phi = refs.source("PH3"), refs.phi()["phi"]
    for t, vals in refs.cell_b_ref():
        for o in (o1, o2):
            assert o.cell_b(s["U"], s["V"], phi, F(*t)) == [F(*v) for v in vals]
