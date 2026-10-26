#!/usr/bin/env python3
"""SIM-CAP1 gram_v1 SPREAD: C++ VM vs an independent unbounded oracle.

Contract (research/sim_cap1_spread/GRAM_V1_CONTRACT.md): exact wide intermediates, int32
range checks on the FINAL N/D only; OVERFLOW iff an oracle coefficient is outside int32;
refusals are atomic. Legacy mode must stay bit-identical.
"""

import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software" / "tests"))
from gram_v1_oracle import bilinear, oracle  # noqa: E402

LIM = 2**31
NUM_REGS = 26


def parse(res):
    f = res.split()
    kind, pc, halted, steps, snap, ncs = f[0], int(f[1]), int(f[2]), int(f[3]), int(f[4]), int(f[5])
    cs = tuple(int(x) for x in f[6:6 + ncs])
    rest = [int(x) for x in f[6 + ncs:]]
    regs = [(rest[2 * i], rest[2 * i + 1]) for i in range(NUM_REGS)]
    q = rest[2 * NUM_REGS:]
    qregs = [tuple(q[8 * i:8 * i + 8]) for i in range(13)]
    return kind, pc, halted, steps, snap, cs, regs, qregs


def seed(v, w, rd):
    """Pre-instruction state the driver seeds (must match gram_v1_spread_cpp.cpp)."""
    regs = [(100 + i, -i) for i in range(NUM_REGS)]
    regs[rd], regs[(rd + 1) % NUM_REGS] = (7, 7), (9, 9)
    qregs = [tuple(x for pq in v for x in pq), tuple(x for pq in w for x in pq)]
    qregs += [tuple(x for _ in range(4) for x in (5 * q + 1, q - 3)) for q in range(2, 13)]
    return regs, qregs


def line(mode, rd, v, w):
    return f"{mode} {rd} " + " ".join(f"{p} {q}" for p, q in v + w)


def main():
    u, wv = (708158977, 408855776), (708158977, -408855776)
    z = (0, 0)
    t3 = lambda x, c: (c * x[0], c * x[1])
    fixed = [([(c, 0), z, z, z], [(c, 0), z, z, z]) for c in (124, 125)]
    fixed += [([(1, c), z, z, z], [(1, c), z, z, z]) for c in (71, 72)]
    fixed += [([t3(u, 3), z, z, z], [t3(wv, 3), z, z, z]),
              ([z, t3(u, 3), z, z], [z, t3(wv, 3), z, z]),
              ([t3(u, -3), z, z, z], [t3(wv, 3), z, z, z]),
              ([(1, 0)] * 4, [(1, 0), z, z, z]), ([z] * 4, [(1, 0), z, z, z]),
              ([(1, 0), z, z, z], [(2, 3)] * 4),
              ([(-LIM, -LIM)] * 4, [(LIM - 1, LIM - 1), z, z, z])]
    rng = random.Random(20261025)
    rand = []
    for _ in range(4000):
        r = rng.choice([3, 30, 70, 200, 2000, 40000, LIM - 1])
        rand.append(([(rng.randint(-r, r), rng.randint(-r, r)) for _ in range(4)],
                     [(rng.randint(-r, r), rng.randint(-r, r)) for _ in range(4)]))
    cases = [(v, w, 10) for v, w in fixed + rand]
    cases += [(v, w, 25) for v, w in fixed]
    with tempfile.TemporaryDirectory(prefix="gram_v1_") as d:
        binary = Path(d) / "gram_cpp"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-fsanitize=undefined",
                        "-fno-sanitize-recover=undefined",
                        str(ROOT / "software/tests/gram_v1_spread_cpp.cpp"), "-o", str(binary)],
                       check=True)
        stdin = "\n".join(line("g", rd, v, w) for v, w, rd in cases) + "\n"
        proc = subprocess.run([str(binary)], input=stdin, text=True, capture_output=True)
        assert proc.returncode == 0, proc.stdout[:200]
        out = proc.stdout.split("\n")[:-1]
        assert len(out) == len(cases)
        seen = {"OK": 0, "OVERFLOW": 0, "DEGENERATE_METRIC": 0}
        for (v, w, rd), res in zip(cases, out):
            kind, pc, halted, steps, snap, cs, regs, qregs = parse(res)
            want = oracle(v, w)
            regs0, qregs0 = seed(v, w, rd)
            # Whole-state contract: nothing but the destination pair may ever differ, and the
            # call stack, snap counter and QRs are always preserved.
            assert qregs == qregs0 and cs == (19, 23) and snap == 2, ("state drift", res)
            if want is None or any(x < -LIM or x >= LIM for x in (*want[0], *want[1])):
                assert kind == ("DEGENERATE_METRIC" if want is None else "OVERFLOW"), (v, w, res, want)
                assert (pc, halted, steps) == (0, 1, 0), ("pc/steps/halt", res)
                assert regs == regs0, ("registers changed on refusal", rd, res)
            else:
                assert kind == "OK" and (pc, halted, steps) == (1, 0, 1), (v, w, res, want)
                expect = list(regs0)
                expect[rd], expect[(rd + 1) % NUM_REGS] = want[0], want[1]
                assert regs == expect, (v, w, rd, res, want)
            seen[kind] += 1
        assert all(seen.values()), seen
        # --- mandatory Pell cancellation witness (separate from boundary/random coverage) ---
        pell = [fixed[4], fixed[5], fixed[6]]
        assert all(abs(c) < LIM for v, w in pell for pq in v + w for c in pq), "witness lanes must fit int32"
        assert max(abs(c) for v, w in pell[:1] for c in (*bilinear(v, v), *bilinear(w, w))) >= LIM, \
            "witness is only a cancellation test if B itself exceeds int32"
        pin = "\n".join(line("g", 10, v, w) for v, w in pell) + "\n"
        pres = subprocess.run([str(binary)], input=pin, text=True, capture_output=True,
                              check=True).stdout.split("\n")[:-1]
        for (v, w), res in zip(pell, pres):
            kind, pc, halted, steps, snap, cs, regs, qregs = parse(res)
            assert (kind, pc, halted, steps) == ("OK", 1, 0, 1), res
            assert regs[10] == (0, 0) and regs[11] == (729, 0), ("Pell witness N=(0,0) D=(729,0)", res)
        # --- boundary pairs: just fits / just overflows (D.p = 9c^4 at c=124/125, and q-lane 71/72) ---
        for i, expect in ((0, "OK"), (1, "OVERFLOW"), (2, "OK"), (3, "OVERFLOW")):
            assert out[i].split()[0] == expect, (i, out[i])
        # --- legacy mode: bit-identical historical values, no fault on zero-metric ---
        legacy = [((1, 0, 0, 0), (1, 0, 0, 0), (8, 9)), ((1, 0, 0, 0), (0, 1, 0, 0), (9, 9)),
                  ((2, 0, 0, 0), (0, 0, 1, 1), (48, 48)), ((3, 1, 0, 0), (1, 2, 0, 5), (1319, 1344))]
        lin = "\n".join(line("l", 10, [(x, 0) for x in a], [(x, 0) for x in b]) for a, b, _ in legacy) + "\n"
        lin += line("l", 10, [(1, 0)] * 4, [(1, 0), z, z, z]) + "\n"
        lo = subprocess.run([str(binary)], input=lin, text=True, capture_output=True,
                            check=True).stdout.split("\n")[:-1]
        for (_, _, (n, dn)), res in zip(legacy, lo):
            kind, pc, halted, steps, snap, cs, regs, qregs = parse(res)
            assert kind == "OK" and (regs[10][0], regs[11][0]) == (n, dn), (res, n, dn)
        assert parse(lo[4])[0] == "OK" and parse(lo[4])[6][11][0] == 0, lo[4]
        proof_check(d)
    print(f"PASS: gram_v1 SPREAD C++ conformance ({len(cases)} gram cases {seen}, Pell witness, 5 legacy cases, proof)")


def proof_check(tmp):
    """--proof under gram_v1 must print the three B values the result is computed from."""
    vm = Path(tmp) / "spu_vm_proof"
    subprocess.run(["g++", "-std=c++17", "-O1", "-o", str(vm), str(ROOT / "software/vm/spu_vm.cpp")],
                   check=True)
    for a, b in (((1, 0, 0, 0), (0, 1, 0, 0)), ((3, 1, 0, 0), (1, 2, 0, 5))):
        src = "".join(f"LD R{i}, {a[i]}, 0\n" for i in range(4)) + \
              "".join(f"LD R{4 + i}, {b[i]}, 0\n" for i in range(4)) + \
              "QLOAD QR0, R0\nQLOAD QR1, R4\nSPREAD R10, QR0, QR1\nHALT\n"
        sas = Path(tmp) / "proof.sas"
        sas.write_text(src)
        v, w = [(x, 0) for x in a], [(x, 0) for x in b]
        out = subprocess.run([str(vm), str(sas), "--quiet", "--proof", "--metric-semantics=gram_v1"],
                             capture_output=True, text=True, check=True).stdout
        want = "B(v,v)=({},{}) B(w,w)=({},{}) B(v,w)=({},{})".format(
            *bilinear(v, v), *bilinear(w, w), *bilinear(v, w))
        assert want in out, (want, out)
        n, d = oracle(v, w)
        assert n[1] == 0 and d[1] == 0
        assert f"numerator={n[0]} denominator={d[0]}" in out, out


main()
