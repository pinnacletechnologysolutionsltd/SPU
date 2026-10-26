"""Validation B: bit-accurate references for davis_gate_dsp (SIM and GW5A paths) + domain analysis.
 gen   : write vectors.hex (static directed + seeded random + dynamic stream)
 check : compare RTL observations (obs_SIM.txt, obs_GW5A.txt) against references; separate valid/invalid domains.
Reference semantics are derived from the RTL text (widths): see comments. The 11585 bound is derived, not assumed."""
import argparse, json, os, random

M16 = 0xFFFF; M32 = 0xFFFFFFFF
def s16(x): x &= M16; return x - 0x10000 if x & 0x8000 else x
def s32(x): x &= M32; return x - (1 << 32) if x & (1 << 31) else x
def pack(c): return ((c[0] & M16) << 48) | ((c[1] & M16) << 32) | ((c[2] & M16) << 16) | (c[3] & M16)
def unpack(q): return [s16(q >> 48), s16(q >> 32), s16(q >> 16), s16(q)]
PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
def gasket(c): return sum(c) & M16                       # 16-bit wire, wraps
def ref_sim(c):   # SIM: 32-bit signed diffs (no slice), 32-bit products via 32-bit context, accumulate mod 2^32
    iv = sum(((c[i] - c[j]) ** 2) for i, j in PAIRS) & M32
    g = s16(gasket(c)); return (iv + g * g) & M32, iv      # $signed(gasket_sum)*$signed(gasket_sum) in 32-bit
def ref_gw(c):    # GW5A: diff sliced to [15:0] then sign-extended from bit 15 (18b), square mod 2^32 per multiplier
    iv = sum(s16(c[i] - c[j]) ** 2 for i, j in PAIRS) & M32
    g = s16(gasket(c)); return (iv + g * g) & M32, iv
def ref_rot(c): return pack([c[1], c[2], c[3], c[0]])

def zero_sum(rng, M):
    while True:
        a, b, c = (rng.randint(-M, M) for _ in range(3)); d = -(a + b + c)
        if -M <= d <= M: return [a, b, c, d]
def vectors():
    st, rng = [], random.Random(20261021)
    for v in [[0,0,0,0],[4,3,2,1],[1,-1,0,0],[1,1,-1,-1],[2,-1,-1,0],
              [32767,-32768,0,0],[-32768,32767,0,0],[32767,32767,-32767,-32767],[-32768,-32768,32767,32767],
              [32767,32767,32767,32767],[-32768,-32768,-32768,-32768],[16384,16384,16384,16384],     # gasket aliasing (sum 65536)
              [20000,-20000,0,0],[11585,11585,-11585,-11585],[11586,11586,-11586,-11586],
              [16383,16383,-16383,-16383],[16384,16384,-16384,-16384],[32767,0,0,-32768],[1,2,3,4],[1,1,1,0]]:
        st.append(v)
    for M in (100, 3000, 11585, 16383, 32767):
        for _ in range(60): st.append(zero_sum(rng, M))
    for _ in range(80): st.append([rng.randint(-32768, 32767) for _ in range(4)])
    dyn = [zero_sum(rng, 5000) for _ in range(64)]
    return st, dyn

def gen(out):
    st, dyn = vectors()
    with open(out + "/vectors.hex", "w") as f:
        f.write(f"{len(st):016x}\n{len(dyn):016x}\n")
        for v in st + dyn: f.write(f"{pack(v):016x}\n")
    json.dump({"static": st, "dynamic": dyn}, open(out + "/vectors.json", "w"))
    print("RESULT " + json.dumps({"id": "B.gen", "ok": True, "detail": {"static": len(st), "dynamic": len(dyn)}}))

def emit(i, ok, d): print("RESULT " + json.dumps({"id": "B." + i, "ok": ok, "detail": d}, default=str))
def rd(path):
    rows = []
    for l in open(path):
        t = l.split()
        if t and t[0] in "SD": rows.append((t[0], int(t[1]), int(t[2], 16), int(t[3], 16), int(t[4], 16), int(t[5], 16), int(t[6], 16)))
    return rows

def check(work):
    vj = json.load(open(work + "/vectors.json")); st, dyn = vj["static"], vj["dynamic"]
    # --- domain derivation (independent of the report's claim) ---
    # (1) exhaustive small-M proof that max 4*sum(c^2) over zero-sum |c|<=M is 16 M^2 (vertex (M,M,-M,-M))
    ok1 = True
    for M in range(1, 8):
        mx = max(4 * sum(x * x for x in (a, b, c, -(a + b + c))) for a in range(-M, M+1) for b in range(-M, M+1) for c in range(-M, M+1) if abs(a+b+c) <= M)
        ok1 &= (mx == 16 * M * M)
    lim_signed32 = max(M for M in range(1, 40000) if 16 * M * M < (1 << 31))      # quadrance read as signed 32
    lim_unsigned32 = max(M for M in range(1, 40000) if 16 * M * M < (1 << 32))
    lim_diff16 = max(M for M in range(1, 40000) if 2 * M <= 32767)                # pairwise diff must fit signed 16 on GW path
    emit("domain_bound_derivation", ok1, {"max_Q_is_16M2_for_M<8_exhaustive": ok1, "M_signed32": lim_signed32, "M_unsigned32": lim_unsigned32,
         "M_diff_fits_s16": lim_diff16, "reported_bound": 11585, "reported_bound_matches_signed32": lim_signed32 == 11585,
         "note": "extension beyond M=7 rests on convexity (max at polytope vertex)"})
    for dev, ref in (("SIM", ref_sim), ("GW5A", ref_gw)):
        rows = rd(f"{work}/obs_{dev}.txt")
        S = [r for r in rows if r[0] == "S"]; D = [r for r in rows if r[0] == "D"]
        emit(f"{dev}.obs_count", len(S) == len(st) and len(D) == len(dyn), {"static": len(S), "dynamic": len(D)})
        bad = {"valid": [], "invalid": []}; cat = {"valid": 0, "invalid": 0}
        for (k, i, qv, quad, ivm, gs, qr), v in zip(S, st):
            vs = sum(v) == 0 and all(-32768 <= x <= 32767 for x in v)
            tag = "valid" if vs else "invalid"; cat[tag] += 1
            eq, ei = ref(v)
            if (quad, ivm, gs, qr) != (eq, ei, gasket(v), ref_rot(v)): bad[tag].append({"v": v, "obs": [quad, ivm, gs, qr], "ref": [eq, ei, gasket(v), ref_rot(v)]})
        emit(f"{dev}.rtl_matches_bitaccurate_ref", not bad["valid"] and not bad["invalid"], {"cases": cat, "mismatch_valid": len(bad["valid"]), "mismatch_invalid": len(bad["invalid"]), "examples": (bad["valid"] + bad["invalid"])[:3]})
        # true-math comparison: where does the output differ from exact 4*sum(c^2) (zero-sum) / exact Q?
        dev_from_math = {"valid_within_11585": 0, "valid_11586_to_16383": 0, "valid_above_16383": 0}; n_in = n_a = n_b = 0
        for (k, i, qv, quad, ivm, gs, qr), v in zip(S, st):
            if sum(v) != 0 or not all(-32768 <= x <= 32767 for x in v): continue
            exact = 4 * sum(x * x for x in v); m = max(abs(x) for x in v)
            wrong = (ivm != exact % (1 << 32)) or (quad != exact % (1 << 32))
            sgn_wrong = s32(quad) != exact
            key = "valid_within_11585" if m <= 11585 else ("valid_11586_to_16383" if m <= 16383 else "valid_above_16383")
            dev_from_math[key] += int(wrong)
            n_in += (m <= 11585) and sgn_wrong
        emit(f"{dev}.zero_sum_wrong_vs_exact_mod2^32", dev_from_math["valid_within_11585"] == 0, {"wrong_by_magnitude_class": dev_from_math, "signed_misread_within_11585": n_in})
        # gasket aliasing: off-hyperplane sum wraps
        alias = [v for v in st if sum(v) != 0 and s16(gasket(v)) != sum(v)]
        emit(f"{dev}.gasket_sum_wraps_off_hyperplane", len(alias) > 0, {"examples": alias[:3], "note": "defect only if an accepted path can supply off-hyperplane input (see val_e)"})
        # pipeline alignment (dynamic stream). Hypotheses derived from RTL register chain.
        if dev == "GW5A":
            def exp(k, lag_ivm, lag_gs):
                if k - max(lag_ivm, lag_gs) < 0: return None
                ci, cg = dyn[k - lag_ivm], dyn[k - lag_gs]
                return (ref_gw(ci)[1] + s16(gasket(cg)) ** 2) & M32
            for name, li, lg in (("ivm_lag1_gs_lag2_(RTL_chain_reading)", 1, 2), ("aligned_lag1_lag1", 1, 1), ("aligned_lag2_lag2", 2, 2)):
                mism = sum(1 for (_, k, _, quad, *_r) in D if exp(k, li, lg) is not None and quad != exp(k, li, lg))
                emit(f"GW5A.dynamic_quadrance_hypothesis_{name}", mism == 0, {"mismatches": mism, "of": len(D)})
        else:
            mism = sum(1 for (_, k, _, quad, *_r) in D if quad != ref_sim(dyn[k])[0])
            emit("SIM.dynamic_combinational", mism == 0, {"mismatches": mism, "of": len(D)})

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("mode"); p.add_argument("--out"); p.add_argument("--work"); a = p.parse_args()
    gen(a.out) if a.mode == "gen" else check(a.work)
