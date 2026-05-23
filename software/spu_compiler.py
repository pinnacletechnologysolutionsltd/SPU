#!/usr/bin/env python3
"""
spu_compiler.py — Lithic-L Curve Expansion Pass (v1.0)

Compiles high-level rational curve constructs into SPU-13 .sas assembly.
The output feeds directly into spu13_asm.py for final encoding.

Constructs:
    arc      center=<QR> point=<QR> axis=<int> steps=<int>
    chain    base=<QR> joints=[(axis,F,G,H), ...]
    nlrep    a=<int> b=<int> t_num=<int> t_den=<int> -> <reg>
    snap
    delta    Q1=<int> Q2=<int> steps=<int> -> <QR>

Usage:
    python3 spu_compiler.py input.lith              → stdout (.sas)
    python3 spu_compiler.py input.lith -o output.sas → file

CC0 1.0 Universal.
"""

import sys
import re
import shlex
from pathlib import Path

# ── Pell orbit lookup (must match spu_quadray.h PELL_ORBIT) ──────────────

PELL_ORBIT = [
    (1, 0, +1),     # r^0
    (2, 1, +1),     # r^1
    (7, 4, +1),     # r^2
    (26, 15, +1),   # r^3
    (97, 56, -1),   # r^4
    (362, 209, -1), # r^5
    (1351, 780, -1),# r^6
    (5042, 2911, -1),# r^7
]

# ── F,G,H coefficient table for tetrahedral angles ───────────────────────
# Each entry: (angle_name, F, G, H) as (num, den) triples
# Values from Thomson Quadray-Rotors-v5 Table 2 / spu13_rotor_core.v

# Extended table: 64 entries covering tetrahedral, octahedral, and icosahedral groups.
# Entries 0-5: tetrahedral C₃ subgroup (D-axis)
# Entries 6-11: full A₄ tetrahedral group
# Entries 12-23: octahedral/cube S₄ group (placeholder — extended set)
# Entries 24-63: icosahedral/dodecahedral A₅ and Thomson dynamic systems (placeholder)

CIRCULANT_TABLE = {
    # ── Tetrahedral C₃ (D-axis) ──────────────────────────────────────
    0:    ("0°",    (1,1), (0,1), (0,1)),
    1:    ("60°",   (2,3), (2,3), (-1,3)),
    2:    ("120°",  (-1,3), (2,3), (2,3)),
    3:    ("180°",  (-1,3), (-1,3), (-1,3)),
    4:    ("240°",  (2,3), (-1,3), (2,3)),
    5:    ("300°",  (2,3), (2,3), (-1,3)),
    # ── A₄ group (other vertex axes) ────────────────────────────────
    6:    ("120°A", (2,3), (-1,3), (2,3)),
    7:    ("240°A", (2,3), (2,3), (-1,3)),
    8:    ("120°B", (-1,3), (2,3), (2,3)),
    9:    ("240°B", (2,3), (2,3), (-1,3)),
    10:   ("120°C", (2,3), (-1,3), (2,3)),
    11:   ("240°C", (-1,3), (2,3), (2,3)),
    # ── Platonic (extended — requires flash-loaded F,G,H) ────────────
    12:   ("cube90",    (0,1), (0,1), (0,1)),     # placeholder
    15:   ("ico60",     (0,1), (0,1), (0,1)),     # placeholder (Q(√5))
    19:   ("VE",        (0,1), (0,1), (0,1)),     # cuboctahedron placeholder
    24:   ("RD",        (0,1), (0,1), (0,1)),     # rhombic dodecahedron placeholder
}

# ── Register allocator ──────────────────────────────────────────────────

class RegisterPool:
    """Manages temporary register allocation during expansion."""
    def __init__(self):
        self._qr_temps = list(range(4, 13))  # QR[4..12] available
        self._r_temps  = list(range(8, 16))  # R[8..15] available
        self._qr_next  = 0
        self._r_next   = 0

    def alloc_qr(self) -> int:
        if self._qr_next >= len(self._qr_temps):
            raise RuntimeError("Out of Quadray temporary registers")
        r = self._qr_temps[self._qr_next]
        self._qr_next += 1
        return r

    def alloc_r(self) -> int:
        if self._r_next >= len(self._r_temps):
            raise RuntimeError("Out of scalar temporary registers")
        r = self._r_temps[self._r_next]
        self._r_next += 1
        return r

    def reset(self):
        self._qr_next = 0
        self._r_next = 0


# ── Parser ──────────────────────────────────────────────────────────────

def parse_int(s: str) -> int:
    """Parse signed integer or simple expression."""
    s = s.strip()
    if s.startswith('-'):
        return -parse_int(s[1:])
    return int(s)

def parse_register(s: str) -> tuple:
    """Parse 'QR[3]' → ('QR', 3) or 'R[5]' → ('R', 5)."""
    s = s.strip()
    m = re.match(r'(QR|R)\[(\d+)\]', s)
    if not m:
        raise ValueError(f"Invalid register: {s}")
    return (m.group(1), int(m.group(2)))

def parse_rational(s: str) -> tuple:
    """Parse '2/3' → (2,3) or '1' → (1,1)."""
    s = s.strip()
    if '/' in s:
        num, den = s.split('/')
        return (int(num), int(den))
    return (int(s), 1)

# ── Code emitter ────────────────────────────────────────────────────────

class AsmEmitter:
    """Emits .sas assembly lines with labels and comments."""

    def __init__(self):
        self.lines = []
        self.label_counter = 0

    def emit(self, line: str):
        self.lines.append(line)

    def comment(self, text: str):
        self.emit(f"    ; {text}")

    def label(self, name: str = None) -> str:
        if name is None:
            self.label_counter += 1
            name = f"_L{self.label_counter}"
        self.emit(f"{name}:")
        return name

    def instr(self, mnemonic: str, *args):
        arg_str = ", ".join(str(a) for a in args)
        self.emit(f"    {mnemonic} {arg_str}")

    def blank(self):
        self.emit("")

    def get(self) -> str:
        return "\n".join(self.lines)


# ── Curve expanders ─────────────────────────────────────────────────────

def expand_arc(emitter: AsmEmitter, regs: RegisterPool,
               center_reg: tuple, point_reg: tuple,
               axis: int, steps: int):
    """
    Generate a circular arc of `steps` Pell rotations around a center point.

    center = QR[c], point = QR[p]
    offset = point - center  →  QR[tmp]
    For k in 1..steps:
        QR[tmp] = QROT(QR[tmp])     ; Pell-rotate the offset
        QR[out] = QADD(QR[tmp], QR[c])  ; new point = center + offset
    """
    c_reg = f"QR{center_reg[1]}"
    p_reg = f"QR{point_reg[1]}"

    tmp_offset = regs.alloc_qr()
    tmp_result = regs.alloc_qr()
    r_pell = regs.alloc_r()

    emitter.comment(f"── circular_arc: {steps} Pell steps around {c_reg}, axis {axis} ──")

    # Load Pell rotor scalar r = (2, 1)
    emitter.instr("LD", f"R{r_pell}", "2", "1")
    emitter.comment(f"R{r_pell} = Pell rotor (2+√3)")

    # offset = point - center
    emitter.instr("QSUB", f"QR{tmp_offset}", p_reg, c_reg)
    emitter.comment(f"QR{tmp_offset} = offset = {p_reg} - {c_reg}")

    # Emit start point
    emitter.instr("QLOG", p_reg)
    emitter.comment(f"step 0: start point")

    # Generate arc steps
    for k in range(1, steps + 1):
        emitter.comment(f"step {k}")
        # Rotate offset by Pell rotor
        emitter.instr("QROT", f"QR{tmp_offset}", f"R{r_pell}")
        # new_point = center + rotated_offset
        emitter.instr("QADD", f"QR{tmp_result}", f"QR{tmp_offset}", c_reg)
        # Output
        emitter.instr("QLOG", f"QR{tmp_result}")

    emitter.blank()
    return tmp_result


def expand_chain(emitter: AsmEmitter, regs: RegisterPool,
                 base_reg: tuple, joints: list):
    """
    Forward kinematics chain: apply F,G,H circulant rotations in sequence.

    base = QR[b]
    current = QR[b]
    For each joint (axis_id, F, G, H):
        current = circulant_rotate(current, F, G, H)  ; B',C',D' transform, A invariant

    F,G,H are rational fractions. For 60°: F=2/3, G=2/3, H=-1/3.
    For 120°: F=-1/3, G=2/3, H=2/3 (the permutation case).

    Since the SPU doesn't have a native CIR opcode, we expand to:
        MUL R[tmpF], B, R[f] ; ... 9 surd multiplies + 6 adds for B',C',D'
    But we can use the F,G,H values directly as RationalSurd constants.
    For the assembler, we load them with LD: LD R[tmp], num, den → but wait,
    LD loads (a, b) where a+b√3. F=2/3 needs a rational coefficient.
    We scale by 3: LD R[f3], 2, 0 (represents 2), then scale results by 1/3.

    Simplification for v1.0: use the bypass_p5 optimization for 120°
    (pure permutation) and the general path for 60°.
    """
    b_reg = f"QR{base_reg[1]}"
    current_qr = base_reg[1]
    tmp_qr = regs.alloc_qr()

    emitter.comment(f"── fk_chain: {len(joints)} joints from {b_reg} ──")

    for i, joint in enumerate(joints):
        axis_id = joint["axis"]
        F_num, F_den = joint["F"]
        G_num, G_den = joint["G"]
        H_num, H_den = joint["H"]

        emitter.comment(f"joint {i}: axis={axis_id}, F={F_num}/{F_den}, "
                        f"G={G_num}/{G_den}, H={H_num}/{H_den}")

        # Determine ROTC angle from F,G,H values
        angle = None
        if F_num == 1 and F_den == 1 and G_num == 0 and H_num == 0:
            angle = 0   # 0° identity
        elif F_num == 2 and F_den == 3 and G_num == 2 and H_num == -1:
            angle = 1   # 60° (or 300°)
        elif F_num == -1 and F_den == 3 and G_num == 2 and H_num == 2:
            angle = 2   # 120°
        elif F_num == -1 and F_den == 3 and G_num == -1 and H_num == -1:
            angle = 3   # 180°
        elif F_num == 2 and F_den == 3 and G_num == -1 and H_num == 2:
            angle = 4   # 240°

        if angle is not None:
            emitter.instr("ROTC", f"QR{current_qr}", f"QR{current_qr}", str(angle))
            emitter.comment(f"{angle*60}° circulant rotation")
        else:
            emitter.comment("circulant_rotate: custom F,G,H not in table")
            r_pell = regs.alloc_r()
            emitter.instr("LD", f"R{r_pell}", "2", "1")
            emitter.instr("QROT", f"QR{current_qr}", f"R{r_pell}")
            emitter.comment("placeholder — custom angle needs ROTC table extension")

    emitter.blank()
    return current_qr


def expand_nlrep(emitter: AsmEmitter, step_a: int, step_b: int,
                 t_num: int, t_den: int, dest_reg: str):
    """
    Cayley NLERP between two Pell rotors at steps a and b.
    Interpolates step count: step_interp = a + (b-a)*t_num/t_den.
    Looks up (p, q, polarity) from Pell orbit vault.
    """
    step_interp = step_a + (step_b - step_a) * t_num // t_den
    sm = step_interp % 8
    p, q, polarity = PELL_ORBIT[sm]

    emitter.comment(f"── cayley_nlrep: step {step_a}→{step_b} "
                    f"at t={t_num}/{t_den} → step {step_interp} ──")
    emitter.instr("LD", dest_reg, str(p), str(q))
    emitter.comment(f"Pell rotor r^{step_interp} = ({p}+{q}√3), "
                    f"polarity={'+' if polarity>0 else '−'}")
    emitter.blank()


def expand_snap(emitter: AsmEmitter):
    """Davis Gate laminar check — Σ quadrance over 13 axes == 0."""
    emitter.comment("── davis_snap: laminar check ──")
    emitter.instr("SNAP")
    emitter.instr("EQUIL")
    emitter.blank()


def expand_delta(emitter: AsmEmitter, regs: RegisterPool,
                 Q1: int, Q2: int, steps: int, dest_qr: int):
    """
    Delta curve: parameterize Q₃ as spread varies s = k/steps for k=0..steps.
    Uses the DELTA opcode (0x1E) which computes the full triple quadrance
    parameterization in one instruction: stores q_sum + rhs² in QRdest.
    """
    Qsum = Q1 + Q2
    emitter.comment(f"── delta_curve: Q1={Q1}, Q2={Q2}, {steps} steps ──")
    emitter.instr("DELTA", f"QR{dest_qr}", str(Q1), str(Q2), str(steps))
    emitter.comment(f"Q₃ = {Qsum} ± √(4·{Q1}·{Q2}·(steps−k)/{steps})")
    emitter.blank()


# ── Polyhedron table ──────────────────────────────────────────────────
# Maps polyhedron names to { rotation_set, seed_abcd }
# rotation_set: list of ROTC angle indices (0-63)
# seed_abcd: initial (A_p,A_q, B_p,B_q, C_p,C_q, D_p,D_q) in Q(√3)

POLYHEDRON_TABLE = {
    # Vector Equilibrium (cuboctahedron): 12 vertices from A₄ orbit
    # Zero-sum Quadray coordinates (A+B+C+D=0, centered at origin).
    # Permutations of (-1,0,0,1): 12 vertices, Davis-laminar.
    "VE": {
        "rotations": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "seed_abcd": (1, 0, 0, 0, 0, 0, 0, 0),
        "vertices": [
            (-1,  0,  0,  1), (-1,  0,  1,  0), (-1,  1,  0,  0),
            ( 0, -1,  0,  1), ( 0, -1,  1,  0), ( 0,  0, -1,  1),
            ( 0,  0,  1, -1), ( 0,  1, -1,  0), ( 0,  1,  0, -1),
            ( 1, -1,  0,  0), ( 1,  0, -1,  0), ( 1,  0,  0, -1),
        ],
    },
    # Tetrahedron: 4 vertices from A₄ orbit of (1,0,0,0)
    # The 4 basis Quadray vectors, generated by all 12 A₄ elements.
    "tetrahedron": {
        "rotations": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "seed_abcd": (1, 0, 0, 0, 0, 0, 0, 0),
        "vertices": [
            (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1),
        ],
    },
    # Octahedron: 6 vertices in zero-sum Quadray
    # Permutations of (1,-1,0,0), sum=0.
    "octahedron": {
        "rotations": [],
        "seed_abcd": (0, 0, 0, 0, 0, 0, 0, 0),
        "vertices": [
            (1, -1,  0,  0), (1,  0, -1,  0), (1,  0,  0, -1),
            (0,  1, -1,  0), (0,  1,  0, -1), (0,  0,  1, -1),
        ],
    },
    # Rhombic Dodecahedron: 14 vertices (8 cube + 6 octahedron)
    # Dual of cuboctahedron. All Q(√3), zero-sum.
    "RD": {
        "rotations": [],
        "seed_abcd": (0, 0, 0, 0, 0, 0, 0, 0),
        "vertices": [
            ( 3, -1, -1, -1), (-1,  3, -1, -1),
            (-1, -1,  3, -1), (-1, -1, -1,  3),
            (-3,  1,  1,  1), ( 1, -3,  1,  1),
            ( 1,  1, -3,  1), ( 1,  1,  1, -3),
            ( 1, -1,  0,  0), ( 1,  0, -1,  0),
            ( 1,  0,  0, -1), ( 0,  1, -1,  0),
            ( 0,  1,  0, -1), ( 0,  0,  1, -1),
        ],
    },
    # Icosahedron: 20 vertices (A₅ symmetry) — placeholder
    "icosahedron": {
        "rotations": [],
        "seed_abcd": (0, 0, 0, 0, 0, 0, 0, 0),
    },
}


def expand_polyhedron(emitter: AsmEmitter, regs: RegisterPool,
                      name: str, seed_reg: tuple, dest_base: tuple):
    """Generate vertices of a polyhedron via A₄ ROTC orbit.

    Applies each rotation in the polyhedron's rotation set to the seed,
    storing results in consecutive QR registers starting from dest_base.
    """
    name_upper = name.upper()
    # Case-insensitive lookup
    info = None
    for key, val in POLYHEDRON_TABLE.items():
        if key.upper() == name_upper:
            info = val
            break
    if info is None:
        emitter.comment(f";; Unknown polyhedron: {name}")
        emitter.comment(f";; Known: {', '.join(sorted(POLYHEDRON_TABLE.keys()))}")
        return
    vertices = info.get("vertices", None)

    if vertices:
        # Pre-computed integer vertices — emit QLDI directly
        emitter.comment(f"── {name}: {len(vertices)} vertices ──")
        for i, (A, B, C, D) in enumerate(vertices):
            qr_idx = dest_base[1] + i
            if qr_idx > 12:
                qr_idx = qr_idx % 13
            emitter.instr("QLDI", f"QR{qr_idx}", str(A), str(B), str(C), str(D))
            emitter.comment(f"vertex {i}: ({A},{B},{C},{D})")
        emitter.blank()
        emitter.comment(f";; {len(vertices)} vertices loaded in "
                        f"QR{dest_base[1]}–QR{dest_base[1] + len(vertices) - 1}")
        return

    rotations = info["rotations"]
    if not rotations:
        emitter.comment(f";; {name} — rotation set not populated (needs vertex ROM)")
        return

    seed_abcd = info["seed_abcd"]
    seed_qr = seed_reg[1]
    dest_qr = dest_base[1]

    emitter.comment(f"── {name}: {len(rotations)} vertices via A₄ ROTC ──")

    # Initialize seed register with the seed Quadray vector
    if seed_abcd != (1, 0, 0, 0, 0, 0, 0, 0):
        # Custom seed: load components
        Ap, Aq, Bp, Bq, Cp, Cq, Dp, Dq = seed_abcd
        emitter.instr("IDNT", f"QR{seed_qr}")  # start from identity
        # Load B,C,D components explicitly (placeholder for full seed loading)
        emitter.comment(f";; seed = ({Ap}+{Aq}√3, {Bp}+{Bq}√3, "
                        f"{Cp}+{Cq}√3, {Dp}+{Dq}√3)")
        # In a full implementation, LD each component from Pell vault or constants
    else:
        emitter.instr("IDNT", f"QR{seed_qr}")
        emitter.comment(f";; seed QR{seed_qr} = (1,0,0,0)")

    emitter.blank()

    # Generate orbit: apply each rotation to the seed
    for i, rot in enumerate(rotations):
        qr_dest = dest_qr + i
        if qr_dest > 12:
            qr_dest = qr_dest % 13  # wrap around
        angle_name = CIRCULANT_TABLE.get(rot, (f"@{rot*60}°",))[0]
        emitter.instr("ROTC", f"QR{qr_dest}", f"QR{seed_qr}", str(rot))
        emitter.comment(f"vertex {i}: ROTC angle {rot} ({angle_name}) → QR{qr_dest}")

    emitter.blank()
    emitter.comment(f";; {len(rotations)} vertices generated in "
                    f"QR{dest_qr}–QR{dest_qr + len(rotations) - 1}")


# ── Main compiler ───────────────────────────────────────────────────────

def compile_lith(source: str, filename: str = "<input>") -> str:
    """Compile Lithic-L source to .sas assembly."""
    emitter = AsmEmitter()
    regs = RegisterPool()

    emitter.comment(f";; Generated by spu_compiler.py from {filename}")
    emitter.comment(";; Lithic-L → SPU-13 .sas assembly")
    emitter.blank()

    lines = source.split('\n')
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith(';'):
            emitter.emit(raw)
            continue

        # Split into tokens — preserve key=value pairs
        tokens = shlex.split(line)
        if not tokens:
            continue

        cmd = tokens[0].lower()

        # Rejoin remainder for key=value parsing
        remainder = ' '.join(tokens[1:])

        def parse_kwargs(text: str) -> dict:
            """Parse key=value pairs from a string like 'center=QR[0] point=QR[1] axis=3 steps=12'."""
            kwargs = {}
            for match in re.finditer(r'(\w+)=(\[?[\w\[\]/.-]+\]?)', text):
                kwargs[match.group(1)] = match.group(2)
            return kwargs

        try:
            if cmd == 'arc':
                kwargs = parse_kwargs(remainder)
                center = parse_register(kwargs.get('center', 'QR[0]'))
                point  = parse_register(kwargs.get('point', 'QR[1]'))
                axis   = int(kwargs.get('axis', 0))
                steps  = int(kwargs.get('steps', 1))
                expand_arc(emitter, regs, center, point, axis, steps)

            elif cmd == 'chain':
                # chain base=QR[n] joints=[(axis,F,G,H),(axis,F,G,H)]
                # Parse base from remainder
                m = re.search(r'base=(QR\[\d+\])', remainder)
                base = parse_register(m.group(1)) if m else ('QR', 0)

                # Parse joints=[...]
                joints = []
                m = re.search(r'joints=\[(.+)\]', remainder)
                if m:
                    joint_strs = re.findall(r'\((\d+),([^,)]+),([^,)]+),([^,)]+)\)',
                                            m.group(1))
                    for axis_s, F_s, G_s, H_s in joint_strs:
                        joints.append({
                            "axis": int(axis_s),
                            "F": parse_rational(F_s),
                            "G": parse_rational(G_s),
                            "H": parse_rational(H_s),
                        })
                expand_chain(emitter, regs, base, joints)

            elif cmd == 'nlrep':
                kwargs = parse_kwargs(remainder)
                a = int(kwargs.get('a', 0))
                b = int(kwargs.get('b', 1))
                tn = int(kwargs.get('t_num', 1))
                td = int(kwargs.get('t_den', 2))
                dest = kwargs.get('dest', 'R[0]')
                expand_nlrep(emitter, a, b, tn, td, dest)

            elif cmd == 'snap':
                expand_snap(emitter)

            elif cmd == 'delta':
                kwargs = parse_kwargs(remainder)
                Q1 = int(kwargs.get('Q1', 3))
                Q2 = int(kwargs.get('Q2', 4))
                steps = int(kwargs.get('steps', 4))
                dest = int(kwargs.get('dest', '0'))
                expand_delta(emitter, regs, Q1, Q2, steps, dest)

            elif cmd == 'polyhedron' or cmd == 'polyhedron:':
                # polyhedron: <name> [seed=QR[n]] [dest=QR[m]]
                kwargs = parse_kwargs(remainder)
                name = tokens[1] if len(tokens) > 1 else remainder.strip()
                name = name.rstrip(':')
                seed = parse_register(kwargs.get('seed', 'QR[0]'))
                dest_base = parse_register(kwargs.get('dest', 'QR[1]'))
                expand_polyhedron(emitter, regs, name, seed, dest_base)

            elif cmd in (';', ';;'):
                emitter.emit(raw)

            else:
                # Pass-through: unknown commands go to .sas as-is
                emitter.emit(raw)

        except Exception as e:
            raise RuntimeError(
                f"{filename}:{line_no}: {e}\n  {raw}"
            ) from e

    return emitter.get()


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Lithic-L Curve Expansion Compiler")
    ap.add_argument("input", help="Input .lith file")
    ap.add_argument("-o", "--output", help="Output .sas file (default: stdout)")
    ap.add_argument("--print", action="store_true",
                    help="Print compiled .sas to stdout")
    args = ap.parse_args()

    source = Path(args.input).read_text()
    result = compile_lith(source, filename=args.input)

    if args.output:
        Path(args.output).write_text(result + "\n")
        print(f"Compiled {args.input} → {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
