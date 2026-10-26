#!/usr/bin/env python3
"""QROT-1 reproduction: exact characterization of the implemented QROT (opcode 0x11).

  python3 -I tools/qrot1_repro.py          # Python VM only (exact sweep + scenarios)
  python3 -I tools/qrot1_repro.py --cpp    # also builds the C++ VM in a temp dir and compares

Prints PASS/FAIL per check; exit 1 on any mismatch. Changes nothing in the repository.
Vectors come from a fixed LCG (no dependence on Python's random module).
"""
import contextlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "software"))
sys.path.insert(0, str(ROOT / "tools"))
from spu_vm import OPCODES, SPUCore, assemble_source  # noqa: E402
from spu_vm import QuadrayVector as QV, RationalSurd as RS  # noqa: E402
from qrot1_scenarios import EXPECT_NONADD, SCEN  # noqa: E402

U, U2, U4 = RS(2, 1), RS(7, 4), RS(97, 56)
BAD = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" " + detail if detail else ""))
    if not ok:
        BAD.append(name)


def eq(x, y):
    return (x.a, x.b) == (y.a, y.b)


def key(v):
    return tuple((x.a, x.b) for x in v.components())


def gram(v, w):
    s, sv, sw = RS(0, 0), RS(0, 0), RS(0, 0)
    for x, y in zip(v.components(), w.components()):
        s, sv, sw = s + x * y, sv + x, sw + y
    return RS(4 * s.a, 4 * s.b) - sv * sw


def gauge_equiv(v, w):
    d = [x - y for x, y in zip(v.components(), w.components())]
    return all(eq(d[0], e) for e in d)


def vectors():
    x = 20261026

    def nxt():
        nonlocal x
        x = (x * 1103515245 + 12345) % 2**31
        return (x >> 16) % 101 - 50
    fixed = [(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1), (1, 1, 1, 1),
             (-3, 5, -7, 2), (127, -128, 127, -128), (10**6, -10**6, 3, 5)]
    out = [QV(*[RS(c, 0) for c in t]) for t in fixed]
    out.append(QV(RS(1, 2), RS(-1, 1), RS(0, 0), RS(3, -1)))
    return out + [QV(*[RS(nxt(), nxt()) for _ in range(4)]) for _ in range(300)]


def sweep():
    vs, bad = vectors(), {}

    def chk(n, ok):
        bad[n] = bad.get(n, 0) + (not ok)
    for i, v in enumerate(vs):
        r, c = v.rotate(), RS(i % 19 - 9, i % 7 - 3)
        chk("Q(rot v) = u^2 Q(v)", eq(r.quadrance(), U2 * v.quadrance()))
        chk("Q(v) = B(v,v)", eq(v.quadrance(), gram(v, v)))
        chk("Pell norm of quadrance invariant", (lambda p, q: p.a**2 - 3 * p.b**2 == q.a**2 - 3 * q.b**2)(
            r.quadrance(), v.quadrance()))
        chk("rot(v + c.1) == rot(v) literally", key(QV(*[x + c for x in v.components()]).rotate()) == key(r))
        chk("rot(v) ~ u*v (gauge class)", gauge_equiv(r, QV(*[x * U for x in v.components()])))
        chk("class inverse = multiply by 2-sqrt3", gauge_equiv(QV(*[x * RS(2, -1) for x in r.components()]), v))
    nonadd = 0
    for v in vs[:60]:
        for w in vs[60:90]:
            a, b, s = v.rotate(), w.rotate(), (v + w).rotate()
            chk("B(rot v, rot w) = u^2 B(v,w)", eq(gram(a, b), U2 * gram(v, w)))
            n1 = v.quadrance() * w.quadrance() - gram(v, w) * gram(v, w)
            n2 = a.quadrance() * b.quadrance() - gram(a, b) * gram(a, b)
            chk("spread N and D scale by u^4", eq(n2, U4 * n1) and eq(a.quadrance() * b.quadrance(),
                                                                       U4 * (v.quadrance() * w.quadrance())))
            chk("rot(v+w) ~ rot v + rot w (gauge class)", gauge_equiv(s, a + b))
            nonadd += key(s) != key(a + b)
    for n, f in sorted(bad.items()):
        check("sweep: " + n, f == 0, f"failures={f}")
    print(f"INFO vectors={len(vs)} pairs=1800 literal-additivity-violations={nonadd}")
    check("sweep: literal additivity violation count", nonadd == EXPECT_NONADD, f"got={nonadd} expect={EXPECT_NONADD}")


def py_after_qrot(src):
    c, prog, snap = SPUCore(verbose=False, max_steps=2000), assemble_source(src), None
    c.load(prog)
    with contextlib.redirect_stdout(io.StringIO()):
        while not c.halted:
            op = (prog[c.pc] >> 56) & 0xFF if 0 <= c.pc < len(prog) else None
            if not c.step():
                break
            if op == OPCODES["QROT"]:
                snap = tuple((x.a, x.b) for x in c.qregs[0].components())
    return snap


def cpp_qlog(binary, src):
    p = Path(binary).with_suffix(".sas")
    p.write_text(src + "QLOG QR0\nHALT\n")
    out = subprocess.run([str(binary), str(p), "--steps", "5000"], capture_output=True, text=True).stdout
    m = re.findall(r"QLOG QR0=\[(.*?)\] Q=", out)
    items = re.findall(r"\(\s*(-?\d+) \+ (-?\d+)·√3\)|(-?\d+)", m[-1]) if m else []
    return tuple((int(a), int(b)) if a else (int(i), 0) for a, b, i in items)


def cpp_overflow(binary, tmp):
    for n in (10, 14):
        p = Path(tmp) / f"ovf{n}.sas"
        p.write_text("QLDI QR0, 100,0,0,0\n" + "QROT QR0\n" * n + "HALT\n")
        r = subprocess.run(["stdbuf", "-o0", str(binary), str(p)], capture_output=True, text=True)
        txt = r.stdout + r.stderr
        if n == 10:
            check("C++ 10x QROT: all complete, uncaught abort in end-of-run display (rc -6, after 'Quadray Registers')",
                  r.returncode == -6 and "Quadray Registers" in txt and "signed32 coefficient overflow" in txt)
        else:
            check("C++ 14th QROT refused: rc 1, 'Execution rejected: signed32 coefficient overflow'",
                  r.returncode == 1 and "Execution rejected: signed32 coefficient overflow" in txt)


def main():
    sweep()
    for name, src, want in SCEN:
        got = py_after_qrot(src)
        check("python-vm " + name, got == want, f"got={got}")
    if "--cpp" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "spu_vm_cpp"
            subprocess.run(["g++", "-std=c++17", "-O1", "-o", str(binary), str(ROOT / "software/vm/spu_vm.cpp")], check=True)
            for name, src, want in SCEN:
                check("cpp-vm " + name, cpp_qlog(binary, src) == want)
            if shutil.which("stdbuf"):
                cpp_overflow(binary, tmp)
    print("RESULT: " + ("FAIL " + str(BAD) if BAD else "PASS"))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
