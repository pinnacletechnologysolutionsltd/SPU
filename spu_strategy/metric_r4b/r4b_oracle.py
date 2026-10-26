"""SPU-METRIC-R4B oracle. Two independent models, exact integers only.
 INTENDED : Q12 surd z=(a+b*sqrt3)/4096 with raw int32 fields (a,b). N(z)=a*a-3*b*b (scale 2^24, exact, unbounded Python int).
            P0 nonzero: (a,b)!=(0,0).  P1 laminar_N: N>0.  P2 totally_positive: N>0 and a>0 (both real embeddings positive).
 CURRENT  : bit-accurate model of spu_cross_rotor (inferred signed 32x32->64, SIM/A7 path) followed by davis_gate_dsp SIM path
            and spu13_core's  axis_stable = (quadrance > 0)  with rplu_dissoc=0.
Modes:  gen --out DIR   write vectors.hex, fixtures.json (inputs + expected)      [pure Python, no RTL]
        check --dir DIR compare RTL observations obs.txt against CURRENT model    [post-run only]"""
import argparse, json, os
M16, M32, M64 = 0xFFFF, 0xFFFFFFFF, (1 << 64) - 1
def s(x, b): x &= (1 << b) - 1; return x - (1 << b) if x >> (b - 1) else x
def cross_rotor(a, b, ra, rb):
    aa, bb, ab, ba = (a * ra) & M64, (b * rb) & M64, (a * rb) & M64, (b * ra) & M64
    nA = (aa + ((bb << 1) + bb)) & M64          # prod_aa + 3*prod_bb
    nB = (ab + ba) & M64
    return s(nA >> 12, 32), s(nB >> 12, 32)    # bits [43:12] -> 32-bit field
def pack(a, b): return ((a & M32) << 32) | (b & M32)
def lanes(w): return [s(w >> 48, 16), s(w >> 32, 16), s(w >> 16, 16), s(w, 16)]
def gate_sim(w):
    c = lanes(w); iv = sum((c[i] - c[j]) ** 2 for i in range(4) for j in range(i + 1, 4)) & M32
    gs = s(sum(c), 16); return (iv + gs * gs) & M32, iv, gs & M16
def intended(a, b):
    N = a * a - 3 * b * b
    return {"nonzero": (a, b) != (0, 0), "laminar_N": N > 0, "totally_positive": N > 0 and a > 0, "N": N, "N_fits_int64": -(1 << 63) <= N < (1 << 63)}
FIX = [  # id, name, a_raw, b_raw, rotor_a, rotor_b   (Q12: 1.0 = 0x1000)
 ("F00", "zero",                         0, 0, 0x1000, 0),
 ("F01", "one (1.0) baseline",           0x1000, 0, 0x1000, 0),
 ("F02", "eight (8.0) alias",            0x8000, 0, 0x1000, 0),
 ("F03", "1+sqrt3 (negative norm)",      0x1000, 0x1000, 0x1000, 0),
 ("F04", "minus one (positive norm, a<0)", -0x1000, 0, 0x1000, 0),
 ("F05", "sqrt3 (negative norm)",        0, 0x1000, 0x1000, 0),
 ("F06", "reset seed prime 2",           0x2000, 0, 0x1000, 0),
 ("F07", "reset seed prime 37",          0x25000, 0, 0x1000, 0),
 ("F08", "reset seed prime 41",          0x29000, 0, 0x1000, 0),
 ("F09", "a=-2^31 (min int32)",          -(1 << 31), 0, 0x1000, 0),
 ("F10", "b=-2^31 (width stress on N)",  0, -(1 << 31), 0x1000, 0),
 ("F11", "a=2^31-1",                     (1 << 31) - 1, 0, 0x1000, 0),
 ("F12", "a=b=0x40004000 (lane alias, negative norm)", 0x40004000, 0x40004000, 0x1000, 0),
 ("F13", "1.0 with Pell rotor 2+sqrt3 (N(r)=1)", 0x1000, 0, 0x2000, 0x1000),
 ("F14", "1.0 with manual rotor 1+sqrt3 (N(r)<0)", 0x1000, 0, 0x1000, 0x1000),
 ("F15", "8.0 with Pell rotor",          0x8000, 0, 0x2000, 0x1000),
 ("F16", "raw a=1 (tiny)",               1, 0, 0x1000, 0),
 ("F17", "raw b=1 (tiny, negative norm)", 0, 1, 0x1000, 0),
]
def model(a, b, ra, rb):
    a2, b2 = cross_rotor(a, b, ra, rb); w = pack(a2, b2); q, iv, gs = gate_sim(w)
    return {"in_N": intended(a, b), "rot_a": a2, "rot_b": b2, "rot_word": f"{w:016x}", "rot_N": intended(a2, b2),
            "ivm": iv, "gasket": gs, "quadrance": q, "axis_stable_current": q > 0}
def gen(out):
    os.makedirs(out, exist_ok=True); rows = []
    with open(out + "/vectors.hex", "w") as f:
        f.write(f"{len(FIX):016x}\n")
        for i, n, a, b, ra, rb in FIX:
            f.write(f"{pack(a, b):016x}\n{pack(ra, rb):016x}\n"); rows.append({"id": i, "name": n, "a": a, "b": b, "ra": ra, "rb": rb, **model(a, b, ra, rb)})
    json.dump(rows, open(out + "/fixtures.json", "w"), indent=1)
    print("%-4s %-44s %-5s %-5s %-5s %-6s %s" % ("id", "name", "P0", "P1", "P2", "CUR", "quadrance(rotated) | N(rotated axis)"))
    for r in rows:
        n = r["rot_N"]; print("%-4s %-44s %-5s %-5s %-5s %-6s %d | %d%s" % (r["id"], r["name"][:44], n["nonzero"], n["laminar_N"], n["totally_positive"], r["axis_stable_current"], r["quadrance"], n["N"], "" if n["N_fits_int64"] else "  (N exceeds int64)"))
def check(d):
    rows = json.load(open(d + "/fixtures.json")); obs = {}; lat = {}
    for l in open(d + "/obs.txt"):
        t = l.split()
        if t and t[0] == "F": obs[t[1]] = [int(x, 16) for x in t[2:]]
        if t and t[0] == "L": lat[t[1]] = [int(x, 16) for x in t[2:]]
    bad = 0; prev = 0                                   # quadrance before the first fixture = reset state (word 0)
    for r in rows:                                      # cycle boundary: s0 stale (previous), s1 and s2 fresh (1-edge latency)
        o = lat.get(r["id"]); exp = [prev, r["quadrance"], r["quadrance"]]; ok = o == exp; bad += not ok; prev = r["quadrance"]
        print("RESULT " + json.dumps({"id": "R4B.latency." + r["id"], "ok": ok, "detail": {"obs": o, "exp": exp}}))
    for r in rows:
        o = obs.get(r["id"]); exp = [int(r["rot_word"], 16), r["ivm"], r["gasket"], r["quadrance"], int(r["axis_stable_current"])]
        ok = o == exp; bad += not ok
        print("RESULT " + json.dumps({"id": "R4B." + r["id"], "ok": ok, "detail": {"obs": o, "exp": exp}}))
    print("RESULT " + json.dumps({"id": "R4B.all", "ok": bad == 0, "detail": {"mismatches": bad, "of": len(rows)}}))
if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("mode"); p.add_argument("--out"); p.add_argument("--dir"); a = p.parse_args()
    gen(a.out) if a.mode == "gen" else check(a.dir)
