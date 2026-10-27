"""Host models and result-matrix builder for the NUM-SOM-1 SOM BMU probe.

Three references per case (all host-side; none is RTL evidence by itself):
  RTL         winner observed in the preserved Verilog simulation log
  emu         fixed-width host emulation of spu_som_bmu.v (18-bit differences, 36-bit products,
              32-bit accumulator) with the RTL comparator reading P as unsigned
  fwSgn       the same fixed-width keys under a hypothetical comparator that reads P as signed
  idNarr/idRaw  unbounded exact arithmetic on the narrowed (signed 18-bit) / original inputs,
              cross-checked against software/lib/rational_som.py::find_bmu
"""
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "software"))
from cases import CASES  # noqa: E402
from lib.rational_som import SomNode, find_bmu, rs  # noqa: E402

Z = (0, 0)
# spu_som_weight_bram.v initial block, as (P,Q) per feature
NODES = [[Z] * 4,
         [(2, 0), Z, Z, Z], [Z, (2, 0), Z, Z], [Z, Z, (2, 0), Z],
         [(-2, 0), Z, Z, Z], [Z, (-2, 0), Z, Z], [Z, Z, (-2, 0), (1, 1)]]
VERBOSE = {"W_witness", "QR0_reset"}


def sx(v, b):
    v &= (1 << b) - 1
    return v - (1 << b) if v >> (b - 1) else v


def fw_key(feats, node, wp, wq):
    pe = qe = 0
    qregs = []
    diffwrap = False
    for (fp, fq), (xp, xq) in zip(feats, NODES[node]):
        dp, dq = sx(fp - xp, 18), sx(fq - xq, 18)
        diffwrap |= dp != fp - xp or dq != fq - xq
        sqp, sqq = sx(dp * dp + 3 * dq * dq, 36), sx(2 * dp * dq, 36)
        wP, wQ = sx(sqp * wp + 3 * sqq * wq, 36), sx(sqp * wq + sqq * wp, 36)
        qregs.append((wP, wQ))
        pe += wP
        qe += wQ
    return pe & 0xFFFFFFFF, sx(qe, 32), pe, qe, qregs, diffwrap


def ideal_key(feats, node, wp, wq):
    p = q = 0
    for (fp, fq), (xp, xq) in zip(feats, NODES[node]):
        dp, dq = fp - xp, fq - xq
        sqp, sqq = dp * dp + 3 * dq * dq, 2 * dp * dq
        p += sqp * wp + 3 * sqq * wq
        q += sqp * wq + sqq * wp
    return p, q


def lt_exact(a, b):  # a < b for da + db*sqrt(3)
    da, db = a[0] - b[0], a[1] - b[1]
    if da == 0 and db == 0:
        return False
    if da <= 0 and db <= 0:
        return True
    if da >= 0 and db >= 0:
        return False
    return da * da > 3 * db * db if da < 0 else da * da < 3 * db * db


def lt_unsigned_p(a, b):
    return lt_exact((a[0] & 0xFFFFFFFF, sx(a[1], 32)), (b[0] & 0xFFFFFFFF, sx(b[1], 32)))


def lt_signed_p(a, b):
    return lt_exact((sx(a[0], 32), sx(a[1], 32)), (sx(b[0], 32), sx(b[1], 32)))


def winner(keys, lt):
    best = 0
    for n in range(1, 7):
        if lt(keys[n], keys[best]):
            best = n
    return best


def parse(text):
    out, cur = {}, None
    for ln in text.splitlines():
        ln = ln.strip()
        m = re.match(r"CASE (\d+) feats=([0-9a-f]+)", ln)
        if m:
            cur = int(m.group(1))
            out[cur] = dict(feats=int(m.group(2), 16), cmp=[], acc={}, qreg={})
            continue
        if cur is None:
            continue
        m = re.match(r"RES \d+ best=(\d+)", ln)
        if m:
            out[cur]["best"] = int(m.group(1))
        m = re.match(r"CMP st=(\d+) node=(\d+) lhs=([0-9a-f]+) rhs=([0-9a-f]+) lt=(\d)", ln)
        if m:
            out[cur]["cmp"].append((int(m.group(1)), int(m.group(2)), int(m.group(3), 16),
                                    int(m.group(4), 16), int(m.group(5))))
        m = re.match(r"ACC node=(\d+) pext=([0-9a-f]+) qext=([0-9a-f]+)", ln)
        if m:
            out[cur]["acc"][int(m.group(1))] = (int(m.group(2), 16), int(m.group(3), 16))
        m = re.match(r"QREG node=(\d+) f=(\d) .* q=([0-9a-f]+)$", ln)
        if m:
            out[cur]["qreg"][(int(m.group(1)), int(m.group(2)))] = int(m.group(3), 16)
    return out


def split(v):
    return (v >> 32) & 0xFFFFFFFF, v & 0xFFFFFFFF


def matrix(tag, log_text, wp, wq):
    """Return the result-matrix lines; raise AssertionError if host model and RTL log disagree internally."""
    log = parse(log_text)
    assert sorted(log) == list(range(len(CASES))), "case set differs from cases.py"
    lines = [f"=== {tag}: P-weight={wp} Q-weight={wq} ===",
             f"{'case':<12}{'RTL':>4}{'emu':>4}{'fwSgn':>6}{'idNarr':>7}{'idRaw':>6}"
             f"{'cmpBad':>7}{'keyDiff':>8}  narrowed  class"]
    for i, (name, feats) in enumerate(CASES):
        r = log[i]
        nf = [(sx(p, 18), sx(q, 18)) for p, q in feats]
        packed = 0
        for k, (p, q) in enumerate(nf):
            packed |= (((q & 0x3FFFF) << 18) | (p & 0x3FFFF)) << (36 * k)
        assert r["feats"] == packed, f"{name}: probe stimulus differs from cases.py"
        keys = [fw_key(nf, n, wp, wq) for n in range(7)]
        enc = [(k[0], k[1]) for k in keys]
        emu, fws = winner(enc, lt_unsigned_p), winner(enc, lt_signed_p)
        idn = winner([ideal_key(nf, n, wp, wq) for n in range(7)], lt_exact)
        idr = winner([ideal_key(feats, n, wp, wq) for n in range(7)], lt_exact)
        nodes = [SomNode(n, 0, 0, 0, tuple(rs(*w) for w in NODES[n])) for n in range(7)]
        assert find_bmu([rs(*x) for x in nf], nodes, [rs(wp, wq)] * 4).best_node_id == idn, \
            f"{name}: rational_som.py disagrees with exact model"
        for n in range(7):
            assert r["acc"][n] == (keys[n][2] & (2**64 - 1), keys[n][3] & (2**64 - 1)), f"{name} node{n} accumulator"
            for fi in range(4):
                wP, wQ = keys[n][4][fi]
                assert r["qreg"][(n, fi)] == ((wP & (2**36 - 1)) << 36) | (wQ & (2**36 - 1)), f"{name} node{n} f{fi} product"
        assert r["best"] == emu, f"{name}: host emulation winner {emu} != RTL {r['best']}"
        for st, node, lhs, rhs, lt in r["cmp"]:
            assert bool(lt) == lt_unsigned_p(split(lhs), split(rhs)), f"{name}: comparator decision differs from model"
        cmp_bad = sum(bool(c[4]) != lt_signed_p(split(c[2]), split(c[3])) for c in r["cmp"])
        key_diff = sum((k[2], k[3]) != ideal_key(nf, n, wp, wq) for n, k in enumerate(keys))
        cls = []
        if r["best"] != idn:
            if fws != idn:
                cls.append("arithmetic")
            if r["best"] != fws:
                cls.append("comparator")
        if idn != idr:
            cls.append("narrowing")
        lines.append(f"{name:<12}{r['best']:>4}{emu:>4}{fws:>6}{idn:>7}{idr:>6}{cmp_bad:>7}{key_diff:>8}"
                     f"  {str(idn != idr):<8}  {','.join(cls) or 'agree'}")
        if name in VERBOSE:
            lines.append("  node: mathematical (P',Q') | encoded P32,Q32 hex")
            for n in range(7):
                ik = ideal_key(nf, n, wp, wq)
                lines.append(f"    node{n}: ({ik[0]},{ik[1]}) | {keys[n][0]:08x},{keys[n][1] & 0xFFFFFFFF:08x}")
            lines.append("  comparator log (st 3=vs best, 5=vs second): cand lhs(P,Q) rhs(P,Q) rtl_lt signedP_lt")
            for st, node, lhs, rhs, lt in r["cmp"]:
                a, b = split(lhs), split(rhs)
                lines.append(f"    st={st} node{node} {a[0]:08x},{a[1]:08x} {b[0]:08x},{b[1]:08x} "
                             f"{lt} {int(lt_signed_p(a, b))}")
    return lines
