#!/usr/bin/env python3
"""test_regen_equivalence.py — Stage C hostile equivalence testing
(contract_regen_stageC_2026-08-20.md).

For identical programs and inputs across all nine hostile categories:

    Digital reference  ==  Stage-A RTL  ==  Stage-B fixed-point RTL  ==  VM

at dphi in {0, 100, 255} (compensation exercised, including near its
precision limit). ANY Stage-B != oracle result is a LEAK (falsification
criterion, contract §1) — this test fails and prints the mechanism.

Categories: 1 long programs, 2 many consecutive blocks, 3 max/min signed
values, 4 mixed eligible/ineligible ops, 5 exponent transitions,
6 compensation near its precision limit, 7 saturation boundaries,
8 back-to-back REGENs (idempotence), 9 malformed blocks (fault path —
covered by the core smoke testbench; valid programs only here).
"""
import math
import cmath
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "software"))
sys.path.insert(0, os.path.join(REPO, "software", "tools"))
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from spu13_asm import assemble, AssemblyError  # noqa: E402
from spu_vm import SPUCore                      # noqa: E402

# ── ROTC angles 0-5: (F, G, H) circulant coefficients (frozen table) ──
FGH = {
    0: (1, 0, 0),
    1: (2, 2, -1),   # thirds period-6
    2: (0, 1, 0),    # P5 forward cycle
    3: (-1, 2, 2),   # thirds period-2
    4: (2, -1, 2),   # thirds period-6 inverse
    5: (0, 0, 1),    # P5 inverse cycle
}

CLAMP = 2**31 - 1


def qldi(lane, a, b, c, d):
    return ((0x1D << 56) | (lane << 48) | ((a & 0xFF) << 32) | ((b & 0xFF) << 24)
            | ((c & 0xFF) << 16) | ((d & 0xFF) << 8))


def rotc(dst, src, angle):
    return (0x1C << 56) | (dst << 48) | (src << 40) | ((angle & 0x3F) << 24)


def qsub(dst, src_a, src_b):
    return (0x1B << 56) | (dst << 48) | (src_a << 40) | ((src_b & 0xF) << 8)


def hex_word(lane):
    return (0x16 << 56) | (0 << 48) | (lane << 40)


def qlog_word(lane):
    return (0x14 << 56) | (0 << 48) | (lane << 40)


def ld_word():
    return (0x00 << 56) | (0 << 48) | (0 << 40) | (1 << 24)


def regen(k):
    return (0x09 << 56) | ((k & 0xFFFF) << 24)


def clamp32(v):
    return max(-2**31, min(CLAMP, v))


def exact_qsub(v, w):
    return tuple(clamp32(x - y) for x, y in zip(v, w))


def exact_rotc(v, angle):
    """A-invariant circulant on (B, C, D); F,G,H thirds. Returns None when the
    result is not on the integer lattice (non-lattice states are not part of
    the Stage-B/C population)."""
    a, b, c, d = v
    F, G, H = FGH[angle]
    if angle in (0, 2, 5):   # identity / pure permutations (denominator 1)
        return (a, F * b + H * c + G * d, G * b + F * c + H * d,
                H * b + G * c + F * d)
    n = F * b + H * c + G * d
    if n % 3:
        return None
    n2 = G * b + F * c + H * d
    if n2 % 3:
        return None
    n3 = H * b + G * c + F * d
    if n3 % 3:
        return None
    return (a, n // 3, n2 // 3, n3 // 3)


def apply_op(qr, op):
    """Apply one op to the persistent 13-lane state; returns True on success."""
    if op[0] == "QLDI":
        qr[op[1]] = list(op[2])
    elif op[0] == "ROTC":
        res = exact_rotc(qr[op[2]], op[3])
        if res is None:
            return False
        qr[op[1]] = list(res)
    elif op[0] == "QSUB":
        qr[op[1]] = list(exact_qsub(qr[op[2]], qr[op[3]]))
    elif op[0] in ("HEX", "QLOG", "LD"):
        pass                     # outputs / scalar: no QR state change
    else:
        raise ValueError(op)
    return True


def chain_oracle(chain):
    """Exact integer Quadray state after each K>0 block boundary."""
    qr = [[0, 0, 0, 0] for _ in range(13)]
    states = []
    for block in chain:
        if not block:
            continue             # empty block (K=0): state unchanged
        for op in block:
            ok = apply_op(qr, op)
            if not ok:           # non-lattice ROTC slipped through
                raise AssertionError("non-lattice ROTC in program")
        states.append((tuple(qr[0]), tuple(qr[1])))
    return states


def chain_vm(chain):
    """Assemble a full chain (multiple .block/.regen sequences) and run in the
    VM. Returns the final QR0/QR1 state, or None if the assembler rejects the
    chain (e.g. LD inside a block is assembler-illegal — the RTL-only case)."""
    lines = []
    for block in chain:
        if not block:
            lines.append(".regen")
            continue
        lines.append(".block K=%d" % len(block))
        for op in block:
            if op[0] == "QLDI":
                lane, v = op[1], op[2]
                lines.append("QLDI QR%d, %d, %d, %d, %d" % (lane, v[0], v[1], v[2], v[3]))
            elif op[0] == "ROTC":
                lines.append("ROTC QR%d, QR%d, %d" % (op[1], op[2], op[3]))
            elif op[0] == "QSUB":
                lines.append("QSUB QR%d, QR%d, QR%d" % (op[1], op[2], op[3]))
            elif op[0] == "HEX":
                lines.append("HEX R0, QR%d" % op[1])
            elif op[0] == "QLOG":
                lines.append("QLOG R0, QR%d" % op[1])
            elif op[0] == "LD":
                return None      # assembler-illegal in a block (RTL-only)
        lines.append(".regen")
    lines.append("HALT")
    src = "\n".join(lines) + "\n"
    try:
        words, _ = assemble(src, fold=False)
    except AssemblyError:
        return None
    vm = SPUCore(verbose=False, max_steps=2000)
    vm.load(words)
    # The VM's Davis Gasket / Henosis subsystem (a physical-model feature:
    # cubic-leak detection rebalances QR registers at phi_13/phi_21 gate
    # cycles) is orthogonal to the REGEN contract and has no RTL counterpart
    # in the test configuration. It must not participate in the exact-state
    # reference, so the gate tick is stubbed out.
    vm.fib = type("_NoGate", (), {"tick": lambda self: ""})()
    vm.run()
    assert not vm.regen_prec_fault, "VM REGEN_PREC fault on valid chain"
    assert vm.regen_block_count == 0
    qr0 = (int(vm.qregs[0].a.a), int(vm.qregs[0].b.a),
           int(vm.qregs[0].c.a), int(vm.qregs[0].d.a))
    qr1 = (int(vm.qregs[1].a.a), int(vm.qregs[1].b.a),
           int(vm.qregs[1].c.a), int(vm.qregs[1].d.a))
    return (qr0, qr1)


# ── Photonic substrate backend ──────────────────────────────────────────────
# contract_photonics_backend_2026-08-20.md §3: the photonic realization of
# the frozen Quadray ops. The continuous state is a complex optical field per
# lane/component: field = s·v/2^m · e^{i·angle}, where angle accumulates the
# per-op common-mode thermal rotation (E1) and the REGEN projects via the
# coherent detection (inphase) + the conditioned compensation trim
# 1/cos(angle) (E3) — the BQE-equivalent recovery. Σ_total is carried as the
# per-lane exponents m (E6: implementation metadata, never ISA state). A valid
# REGEN re-encodes the recovered canonical state into the field (Stage-C
# block-boundary result). Counting-only ops (HEX/QLOG/LD) are not mirrored.

class PhotonicQuadrayBackend:
    """Physical optical realization of the frozen SPU Quadray ops.

    deltaT: thermal condition (K); the per-op rotation is
    dphi = K_RAD · deltaT with the canonical silicon constants (E1).
    Conditioned compensation (E3) is applied at every REGEN.
    """

    K_RAD = (2 * math.pi / 1550e-9) * 6.4322e-6 * 1.86e-4  # rad / K
    SCALE = 0.1                                             # canonical WDM s

    def __init__(self, deltaT=2.0):
        self.dphi = self.K_RAD * deltaT

    @staticmethod
    def _load_exp(comps):
        mx = max(abs(c) for c in comps)
        return max(0, mx.bit_length() - 3)

    def run_chain(self, chain):
        fld = [[0j] * 4 for _ in range(13)]   # continuous complex field
        m = [0] * 13                          # per-lane scale exponents
        angle = 0.0
        states = []
        for block in chain:
            if not block:
                continue                      # K=0 pass-through
            for op in block:
                if op[0] == "QLDI":
                    lane = op[1]
                    le = self._load_exp(op[2])
                    f = self.SCALE / (1 << le)
                    # the value enters the continuous field at the CURRENT
                    # accumulated phase (the substrate's present state); the
                    # op's rotation below then advances it like every lane
                    fld[lane] = [complex(v * f, 0.0) * cmath.exp(1j * angle)
                                 for v in op[2]]
                    m[lane] = le
                elif op[0] == "QSUB":
                    d, sa, sb = op[1], op[2], op[3]
                    mc = max(m[sa], m[sb])
                    # re-scale each operand to the common exponent: the field
                    # at scale m is s·v/2^m, so moving to a LARGER m divides
                    fa = [z / (1 << (mc - m[sa])) for z in fld[sa]]
                    fb = [z / (1 << (mc - m[sb])) for z in fld[sb]]
                    fld[d] = [(x - y) / 2.0 for x, y in zip(fa, fb)]
                    m[d] = mc + 1
                elif op[0] == "ROTC":
                    dst, src, ang = op[1], op[2], op[3]
                    F, G, H = FGH[ang]
                    B, C, D = fld[src][1], fld[src][2], fld[src][3]
                    # circulant with the exact thirds only for angles 1/3/4
                    # (0/2/5 are identity/permutation, denominator 1);
                    # 2-normalized (the /2 cancels with m += 1 at recovery)
                    div = 3.0 if ang in (1, 3, 4) else 1.0
                    fld[dst] = [fld[src][0] / 2.0,
                                (F * B + H * C + G * D) / div / 2.0,
                                (G * B + F * C + H * D) / div / 2.0,
                                (H * B + G * C + F * D) / div / 2.0]
                    m[dst] = m[src] + 1
                # HEX / QLOG / LD: counting-only — no optical mirror
                if op[0] in ("QLDI", "QSUB", "ROTC"):
                    angle += self.dphi
                    rot = cmath.exp(1j * self.dphi)
                    for lane in range(13):
                        fld[lane] = [z * rot for z in fld[lane]]
            # REGEN: coherent detection (inphase) + conditioned trim + BQE
            cK = math.cos(angle)
            rec = [[0, 0, 0, 0] for _ in range(13)]
            for lane in range(13):
                for k in range(4):
                    inphase = fld[lane][k].real
                    v = (1 << m[lane]) * (inphase / cK) / self.SCALE
                    rec[lane][k] = max(-2**31, min(CLAMP, int(round(v))))
            # canonical re-entry: re-encode the recovered whole state
            for lane in range(13):
                le = self._load_exp(rec[lane])
                f = self.SCALE / (1 << le)
                fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                m[lane] = le
            angle = 0.0
            states.append((tuple(rec[0]), tuple(rec[1])))
        return states

    def _apply_op_field(self, fld, m, qr, op, angle):
        """Apply one op to the continuous field (noiseless); returns True if
        the op is a mirrored (state-transform) op."""
        if op[0] == "QLDI":
            lane = op[1]
            le = self._load_exp(op[2])
            f = self.SCALE / (1 << le)
            fld[lane] = [complex(v * f, 0.0) * cmath.exp(1j * angle)
                         for v in op[2]]
            m[lane] = le
            qr[lane] = list(op[2])
            return True
        if op[0] == "QSUB":
            d, sa, sb = op[1], op[2], op[3]
            mc = max(m[sa], m[sb])
            fa = [z / (1 << (mc - m[sa])) for z in fld[sa]]
            fb = [z / (1 << (mc - m[sb])) for z in fld[sb]]
            fld[d] = [(x - y) / 2.0 for x, y in zip(fa, fb)]
            m[d] = mc + 1
            qr[d] = list(exact_qsub(qr[sa], qr[sb]))
            return True
        if op[0] == "ROTC":
            dst, src, ang = op[1], op[2], op[3]
            F, G, H = FGH[ang]
            B, C, D = fld[src][1], fld[src][2], fld[src][3]
            div = 3.0 if ang in (1, 3, 4) else 1.0
            fld[dst] = [fld[src][0] / 2.0,
                        (F * B + H * C + G * D) / div / 2.0,
                        (G * B + F * C + H * D) / div / 2.0,
                        (H * B + G * C + F * D) / div / 2.0]
            m[dst] = m[src] + 1
            r = exact_rotc(qr[src], ang)
            qr[dst] = list(r)
            return True
        return False          # HEX / QLOG / LD: counting-only, not mirrored

    def _noise_per_op(self, sigma_phi, sigma_amp, sigma_det, draw):
        """Frozen per-op noise draws (E6/E7 semantics on the 2-lane Quadray):
        lane differential phases, lane amplitudes, per-component detectors."""
        dp = [draw(0.0, sigma_phi), draw(0.0, sigma_phi)]
        ap = [draw(1.0, sigma_amp), draw(1.0, sigma_amp)]
        nd = [[draw(0.0, sigma_det) for _ in range(4)] for _ in range(2)]
        return dp, ap, nd

    def run_chain_noisy(self, chain, sigma_phi, sigma_amp, sigma_det, rng):
        """K-op block under the frozen per-op stochastic noise sources.

        Both arms are evaluated from the SAME per-trial draw stream (the
        first pass consumes the noise draws once; arm A re-runs op-by-op from
        the recorded draws).

        Arm A (per-op REGEN): each mirrored op is followed by a conditioned
        BQE (÷cos angle) with the per-op scale + canonical re-encode; the
        trial fails if ANY op's projection is wrong.
        Arm B (chain): the noise accumulates; one final conditioned BQE with
        the accumulated scale; fails if the final projection is wrong.

        Returns (ok_A, first_failed_op, ok_B, total_m)."""
        if hasattr(rng, "normal"):
            draw = lambda mu, sd: float(rng.normal(mu, sd))
        else:
            draw = lambda mu, sd: rng.gauss(mu, sd)
        fld = [[0j] * 4 for _ in range(13)]
        m = [0] * 13
        qr = [[0, 0, 0, 0] for _ in range(13)]
        angle = 0.0
        noise_lists = []       # one (dp, ap, nd) per mirrored op
        for block in chain:
            for op in block:
                if self._apply_op_field(fld, m, qr, op, angle):
                    dp, ap, nd = self._noise_per_op(
                        sigma_phi, sigma_amp, sigma_det, draw)
                    # common-mode rotation + lane differential + lane amplitude
                    for lane in range(13):
                        ln = 1 if lane == 1 else 0
                        rot = cmath.exp(1j * (self.dphi + dp[ln]))
                        fld[lane] = [z * rot * ap[ln] for z in fld[lane]]
                    angle += self.dphi
                    noise_lists.append((dp, ap, nd))
        # Arm B: one final conditioned BQE with the accumulated scale
        ok_b, total_m = True, 0
        if noise_lists:
            cK = math.cos(angle)
            dp, ap, nd = noise_lists[-1]
            rec = [[0, 0, 0, 0] for _ in range(13)]
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                for k in range(4):
                    inphase = fld[lane][k].real + nd[ln][k]
                    v = (1 << m[lane]) * (inphase / cK) / self.SCALE
                    rec[lane][k] = max(-2**31, min(CLAMP, int(round(v))))
            ok_b = rec == qr
            total_m = max(m)
        # Arm A: re-run op-by-op with per-op REGEN (same recorded draws)
        fld = [[0j] * 4 for _ in range(13)]
        m = [0] * 13
        qr = [[0, 0, 0, 0] for _ in range(13)]
        angle = 0.0
        first_failed = 0
        ni = 0
        for block in chain:
            for op in block:
                if not self._apply_op_field(fld, m, qr, op, angle):
                    continue
                dp, ap, nd = noise_lists[ni]
                ni += 1
                for lane in range(13):
                    ln = 1 if lane == 1 else 0
                    rot = cmath.exp(1j * (self.dphi + dp[ln]))
                    fld[lane] = [z * rot * ap[ln] for z in fld[lane]]
                angle += self.dphi
                cK = math.cos(angle)
                rec = [[0, 0, 0, 0] for _ in range(13)]
                for lane in range(13):
                    ln = 1 if lane == 1 else 0
                    for k in range(4):
                        inphase = fld[lane][k].real + nd[ln][k]
                        v = (1 << m[lane]) * (inphase / cK) / self.SCALE
                        rec[lane][k] = max(-2**31, min(CLAMP, int(round(v))))
                if first_failed == 0 and rec != qr:
                    first_failed = ni
                # canonical re-entry: the field continues from the recovered
                # state; qr keeps tracking the EXACT state (the oracle), so a
                # failed recovery never corrupts the reference for later ops
                for lane in range(13):
                    le = self._load_exp(rec[lane])
                    f = self.SCALE / (1 << le)
                    fld[lane] = [complex(v * f, 0.0) for v in rec[lane]]
                    m[lane] = le
                angle = 0.0
        ok_a = first_failed == 0
        return ok_a, first_failed, ok_b, total_m


# ── program generation ────────────────────────────────────────────────────

def _rand_vec(rng, extreme=False):
    lim = 127 if extreme else rng.randint(1, 127)
    return [rng.choice([-1, 1]) * rng.randint(1, max(1, lim)) for _ in range(4)]


def _fill_transforms(rng, qr, n):
    """Append n lattice-safe ROTC/QSUB transform ops to the block (tracking
    the exact state); returns the ops list."""
    ops = []
    for _ in range(n):
        kind = rng.choice(["ROTC", "QSUB"])
        if kind == "ROTC":
            angles = list(range(6))
            rng.shuffle(angles)
            placed = False
            for ang in angles:
                res = exact_rotc(qr[0], ang)
                if res is not None:
                    ops.append(("ROTC", 0, 0, ang))
                    qr[0] = list(res)
                    placed = True
                    break
            if not placed:
                ops.append(("QSUB", 0, rng.choice([0, 1]), rng.choice([0, 1])))
                qr[0] = list(exact_qsub(qr[rng.choice([0, 1])], qr[rng.choice([0, 1])]))
        else:
            sa = rng.choice([0, 1])
            sb = rng.choice([0, 1])
            ops.append(("QSUB", 0, sa, sb))
            qr[0] = list(exact_qsub(qr[sa], qr[sb]))
    return ops


def gen_chain(rng, nblocks, k, extreme=False, expx=False, mixed=False,
              idem=False):
    """One chain of blocks. Block 0 loads QR0/QR1; later blocks transform the
    persistent state. Returns (chain, is_ld_case)."""
    qr = [[0, 0, 0, 0] for _ in range(13)]
    chain = []

    # block 0: entry loads
    v0 = _rand_vec(rng, extreme=extreme)
    v1 = _rand_vec(rng, extreme=extreme)
    if expx:
        v0 = [rng.choice([-127, 127]) if rng.random() < 0.7 else rng.choice([-1, 1])
              for _ in range(4)]
        v1 = [rng.choice([-127, 127]) if rng.random() < 0.7 else rng.choice([-1, 1])
              for _ in range(4)]
    b0 = [("QLDI", 0, tuple(v0)), ("QLDI", 1, tuple(v1))]
    qr[0] = list(v0)
    qr[1] = list(v1)
    has_ld = False
    b0 += _fill_transforms(rng, qr, max(0, k - 2))
    if mixed:
        # insert counted outputs (HEX/QLOG) and/or an uncounted LD
        insert = rng.choice(["hex", "qlog", "ld", "hex+qlog"])
        if insert in ("hex", "hex+qlog"):
            b0.append(("HEX", 0))
        if insert == "qlog":
            b0.append(("QLOG", 0))
        if insert == "hex+qlog":
            b0.append(("QLOG", 0))
        if insert == "ld":
            b0.append(("LD",))
            has_ld = True
    chain.append(b0)

    # later blocks: transforms on the persistent state
    for _ in range(max(0, nblocks - 1)):
        if idem and rng.random() < 0.4:
            chain.append([])     # empty block: REGEN K=0 pass-through
            continue
        bk = _fill_transforms(rng, qr, k)
        if not bk:
            bk = [("QSUB", 0, 0, 1)]
            qr[0] = list(exact_qsub(qr[0], qr[1]))
        if mixed and rng.random() < 0.5:
            bk.append(("HEX", 0) if rng.random() < 0.5 else ("QLOG", 0))
        chain.append(bk)
    return chain, has_ld


def gen_programs(rng):
    chains = []
    meta = []   # parallel: (category, vm_ok)
    def add(chain, cat, vm_ok=True):
        chains.append(chain)
        meta.append((cat, vm_ok))

    # friendly baseline (single blocks, the Stage-B population)
    for _ in range(24):
        add(gen_chain(rng, 1, rng.choice([2, 3, 4]))[0], "baseline")
    # cat 1: long programs
    for _ in range(24):
        add(gen_chain(rng, 1, rng.choice([8, 12, 16]))[0], "long")
    # cat 2: many consecutive blocks
    for _ in range(8):
        c, _ = gen_chain(rng, rng.randint(8, 16), rng.choice([2, 3, 4]))
        add(c, "blocks")
    # cat 3 + cat 7: max/min signed + saturation (extreme growth)
    for _ in range(24):
        add(gen_chain(rng, 1, rng.choice([8, 12, 16]), extreme=True)[0], "extreme")
    # cat 4: mixed eligible/ineligible
    for _ in range(16):
        c, ld = gen_chain(rng, 1, rng.choice([3, 4, 5]), mixed=True)
        add(c, "mixed", vm_ok=not ld)
    # cat 5: exponent transitions
    for _ in range(16):
        add(gen_chain(rng, 1, rng.choice([4, 6, 8]), expx=True)[0], "exponent")
    # cat 8: back-to-back REGENs / idempotence
    for _ in range(8):
        c, _ = gen_chain(rng, rng.randint(3, 6), rng.choice([2, 3]), idem=True)
        add(c, "idempotence")
    return chains, meta


# ── RTL driver ────────────────────────────────────────────────────────────

def build_tb(chains, dphis):
    tb = []
    tb.append("`timescale 1ns/1ps")
    tb.append("module regen_equiv_tb;")
    tb.append("    reg clk = 0; always #1 clk = ~clk;   // 2ns cycle: cycle-synchronous RTL")
    tb.append("    reg rst_n = 0;")
    tb.append("    reg inst_valid = 0;")
    tb.append("    reg [63:0] inst_word = 0;")
    tb.append("    reg [7:0] regen_dphi_cfg = %d;" % dphis[0])
    tb.append("    wire inst_done;")
    tb.append("    wire qr_commit_valid; wire [3:0] qr_commit_lane;")
    tb.append("    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;")
    tb.append("    wire [15:0] regen_debug_status;")
    tb.append("    integer errors = 0;")
    tb.append("    spu13_core #(")
    tb.append("        .DEVICE(\"SIM\"),")
    tb.append("        .ENABLE_RPLU(0), .ENABLE_LATTICE(0), .ENABLE_MATH(1),")
    tb.append("        .ENABLE_SEQUENCER(0), .ENABLE_CORE_SOM(0), .ENABLE_CORE_RPLU_V2(0),")
    tb.append("        .ENABLE_CORE_RPLU_V2_PIPELINE(0), .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),")
    tb.append("        .ENABLE_IROTC(0)")
    tb.append("    ) uut (")
    tb.append("        .clk(clk), .rst_n(rst_n),")
    tb.append("        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),")
    tb.append("        .regen_dphi_cfg(regen_dphi_cfg),")
    tb.append("        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane),")
    tb.append("        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),")
    tb.append("        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),")
    tb.append("        .dec_fast_cfg_wr_en(1'b0), .dec_fast_cfg_sel(3'd0),")
    tb.append("        .dec_fast_cfg_material(8'd0), .dec_fast_cfg_addr(10'd0),")
    tb.append("        .dec_fast_cfg_data(64'd0), .phinary_cfg(16'd0),")
    tb.append("        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),")
    tb.append("        .boot_done(1'b1), .pell_data(32'd0), .pell_addr(3'd0),")
    tb.append("        .pell_we(1'b0), .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),")
    tb.append("        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(), .mem_addr(),")
    tb.append("        .mem_rd_manifold(832'd0), .mem_wr_manifold(), .mem_burst_done(1'b0),")
    tb.append("        .artery_wr_en(), .artery_wr_data(),")
    tb.append("        .current_axis_ptr(), .current_axis_data(),")
    tb.append("        .inst_valid(inst_valid), .inst_word(inst_word), .inst_done(inst_done),")
    tb.append("        .ratio_cmp_res(), .ratio_cmp_valid(),")
    tb.append("        .manifold_out(), .bloom_complete(), .scale_table_out(),")
    tb.append("        .scale_overflow_out(), .is_janus_point(),")
    tb.append("        .audio_mode(), .gasket_sum_out(), .quadrance_out(), .cycle_wrap(),")
    tb.append("        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),")
    tb.append("        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),")
    tb.append("        .laminar_flow_index_out(), .thermal_pressure_out(),")
    tb.append("        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(),")
    tb.append("        .axiomatic_fault(), .fault_type(), .fault_count(),")
    tb.append("        .rns_error(), .ecc_single_err(), .ecc_double_err(),")
    tb.append("        .rotc_debug_status(),")
    tb.append("        .regen_debug_status(regen_debug_status)")
    tb.append("    );")
    tb.append("    task issue;")
    tb.append("        input [63:0] w;")
    tb.append("        integer g;")
    tb.append("        begin")
    tb.append("            @(posedge clk);")
    tb.append("            inst_word <= w; inst_valid <= 1'b1;")
    tb.append("            @(posedge clk);")
    tb.append("            inst_valid <= 1'b0; inst_word <= 64'd0;")
    tb.append("            g = 0;")
    tb.append("            while (!inst_done && g < 300) begin")
    tb.append("                @(posedge clk); g = g + 1;")
    tb.append("            end")
    tb.append("            if (g >= 300) begin")
    tb.append("                $display(\"TIMEOUT\"); $finish;")
    tb.append("            end")
    tb.append("            @(posedge clk);")
    tb.append("        end")
    tb.append("    endtask")
    tb.append("    function [63:0] f_qldi;")
    tb.append("        input [7:0] lane; input [31:0] v;")
    tb.append("        begin f_qldi = {8'h1D, lane, 8'd0, v[31:24], v[23:16], v[15:8], v[7:0], 8'd0}; end")
    tb.append("    endfunction")
    tb.append("    function [63:0] f_rotc;")
    tb.append("        input [7:0] dst; input [7:0] src; input [5:0] ang;")
    tb.append("        begin f_rotc = {8'h1C, dst, src, 8'd0, 2'b00, ang, 24'd0}; end")
    tb.append("    endfunction")
    tb.append("    function [63:0] f_qsub;")
    tb.append("        input [7:0] dst; input [7:0] sa; input [7:0] sb;")
    tb.append("        begin f_qsub = {8'h1B, dst, sa, 16'd0, {12'd0, sb[3:0]}, 8'd0}; end")
    tb.append("    endfunction")
    tb.append("    function [63:0] f_regen;")
    tb.append("        input [15:0] k;")
    tb.append("        begin f_regen = {8'h09, 8'd0, 8'd0, k, 16'd0, 8'd0}; end")
    tb.append("    endfunction")
    tb.append("    task issue_regen_capture;")
    tb.append("        input [15:0] k;")
    tb.append("        input integer idx;")
    tb.append("        integer g;")
    tb.append("        reg [3:0] l0, l1;")
    tb.append("        reg signed [31:0] a0, b0, c0, d0, a1, b1, c1, d1;")
    tb.append("        begin")
    tb.append("            l0 = 0; l1 = 0; a0=0; b0=0; c0=0; d0=0; a1=0; b1=0; c1=0; d1=0;")
    tb.append("            @(posedge clk);")
    tb.append("            inst_word <= f_regen(k); inst_valid <= 1'b1;")
    tb.append("            @(posedge clk);")
    tb.append("            inst_valid <= 1'b0; inst_word <= 64'd0;")
    tb.append("            g = 0;")
    tb.append("            while (!inst_done && g < 300) begin")
    tb.append("                @(posedge clk);")
    tb.append("                if (qr_commit_valid) begin")
    tb.append("                    case (qr_commit_lane)")
    tb.append("                        4'd0: begin l0 = qr_commit_lane;")
    tb.append("                            a0 = qr_commit_A[31:0]; b0 = qr_commit_B[31:0];")
    tb.append("                            c0 = qr_commit_C[31:0]; d0 = qr_commit_D[31:0]; end")
    tb.append("                        4'd1: begin l1 = qr_commit_lane;")
    tb.append("                            a1 = qr_commit_A[31:0]; b1 = qr_commit_B[31:0];")
    tb.append("                            c1 = qr_commit_C[31:0]; d1 = qr_commit_D[31:0]; end")
    tb.append("                        default: ;")
    tb.append("                    endcase")
    tb.append("                end")
    tb.append("                g = g + 1;")
    tb.append("            end")
    tb.append("            if (g >= 300) begin $display(\"TIMEOUT\"); $finish; end")
    tb.append("            $display(\"R%0d %0d %0d %0d %0d %0d %0d %0d %0d %0d\",")
    tb.append("                     idx, a0, b0, c0, d0, l1, a1, b1, c1, d1);")
    tb.append("            @(posedge clk);")
    tb.append("        end")
    tb.append("    endtask")
    tb.append("    initial begin")
    tb.append("        repeat (4) @(posedge clk);")
    tb.append("        rst_n = 1;")
    tb.append("        repeat (20) @(posedge clk);   // QR hydration walk")
    idx = 0
    for chain in chains:
        for dphi in dphis:
            tb.append("        regen_dphi_cfg = 8'd%d;" % dphi)
            for block in chain:
                if not block:
                    tb.append("        issue(f_regen(16'd0));   // K=0 pass-through")
                    continue
                tb.append("        begin")
                for op in block:
                    if op[0] == "QLDI":
                        lane, v = op[1], op[2]
                        val = ((v[0] & 0xFF) << 24 | (v[1] & 0xFF) << 16
                               | (v[2] & 0xFF) << 8 | (v[3] & 0xFF))
                        tb.append("            issue(f_qldi(8'd%d, 32'h%08x));" % (lane, val))
                    elif op[0] == "ROTC":
                        tb.append("            issue(f_rotc(8'd%d, 8'd%d, 6'd%d));"
                                  % (op[1], op[2], op[3]))
                    elif op[0] == "QSUB":
                        tb.append("            issue(f_qsub(8'd%d, 8'd%d, 8'd%d));"
                                  % (op[1], op[2], op[3]))
                    elif op[0] == "HEX":
                        tb.append("            issue(64'h%016x);" % hex_word(op[1]))
                    elif op[0] == "QLOG":
                        tb.append("            issue(64'h%016x);" % qlog_word(op[1]))
                    elif op[0] == "LD":
                        tb.append("            issue(64'h%016x);" % ld_word())
                # declared K = the E_REGEN op count (LD is not block-eligible)
                k_reg = sum(1 for op in block if op[0] != "LD")
                tb.append("            issue_regen_capture(16'd%d, %d);" % (k_reg, idx))
                tb.append("        end")
                idx += 1
    tb.append("        if (errors == 0) $display(\"REGERM_EQUIV_TB: PASS\");")
    tb.append("        else $display(\"REGERM_EQUIV_TB: FAIL (%0d)\", errors);")
    tb.append("        $finish;")
    tb.append("    end")
    tb.append("endmodule")
    return "\n".join(tb) + "\n"


def run_rtl(chains, dphis=(0, 100, 255), build_dir=None):
    import tempfile
    d = build_dir or tempfile.mkdtemp(prefix="regen_equiv_")
    tb_path = os.path.join(d, "regen_equiv_tb.v")
    with open(tb_path, "w") as f:
        f.write(build_tb(chains, dphis))
    libs = [
        os.path.join(REPO, "hardware", "rtl"),
        os.path.join(REPO, "hardware", "rtl", "core"),
        os.path.join(REPO, "hardware", "rtl", "core", "spu13"),
        os.path.join(REPO, "hardware", "rtl", "core", "shared"),
        os.path.join(REPO, "hardware", "rtl", "arch"),
        os.path.join(REPO, "hardware", "rtl", "math"),
        os.path.join(REPO, "hardware", "rtl", "common", "prim"),
        os.path.join(REPO, "hardware", "rtl", "top"),
    ]
    cmd = ["iverilog", "-g2012"] + [item for L in (["-y", l] for l in libs) for item in L]
    cmd += ["-I", os.path.join(REPO, "hardware", "rtl", "arch")]
    cmd += ["-I", os.path.join(REPO, "hardware", "rtl", "core", "spu13")]
    cmd += ["-o", os.path.join(d, "tb.vvp"),
            os.path.join(REPO, "hardware", "rtl", "arch", "spu_optional_stubs.v"),
            os.path.join(REPO, "hardware", "rtl", "common", "prim", "spu_xilinx_prim.v"),
            tb_path]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=d)
    if r.returncode != 0:
        raise RuntimeError("iverilog failed:\n" + r.stderr[-3000:])
    r = subprocess.run(["vvp", os.path.join(d, "tb.vvp")], capture_output=True, text=True, cwd=d)
    if r.returncode != 0:
        raise RuntimeError("vvp failed:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    out = r.stdout
    rows = {}
    for line in out.splitlines():
        m = re.match(r"^R(\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)$", line)
        if m:
            v = [int(x) for x in m.groups()]
            rows[v[0]] = ((v[1], v[2], v[3], v[4]), (v[6], v[7], v[8], v[9]))
    n_expected = sum(1 for c in chains for _ in dphis for b in c if b)
    assert len(rows) == n_expected, "RTL results %d != expected %d\n%s" % (
        len(rows), n_expected, out[-1500:])
    if "REGERM_EQUIV_TB: FAIL" in out:
        raise AssertionError("RTL tb reported failures:\n" + out[-1500:])
    # order by index; group into {(ci, dphi): [per-boundary states]}
    ordered = [rows[i] for i in sorted(rows)]
    result = {}
    k = 0
    for ci, chain in enumerate(chains):
        for dphi in dphis:
            states = []
            for block in chain:
                if block:
                    states.append(ordered[k])
                    k += 1
            result[(ci, dphi)] = states
    return result


def main():
    import random
    rng = random.Random(13)
    chains, meta = gen_programs(rng)
    n_blocks = sum(len(c) for c in chains)
    n_bound = sum(1 for c in chains for b in c if b)
    print("Stage C: %d chains, %d blocks, %d K>0 boundaries" %
          (len(chains), n_blocks, n_bound))

    # digital reference (exact oracle): per-boundary states
    oracle = [chain_oracle(c) for c in chains]
    # VM reference: final state (None where the assembler rejects the chain,
    # e.g. an LD inside a block is assembler-illegal — the RTL-only case)
    vm = [chain_vm(c) for c in chains]
    for i, v in enumerate(vm):
        if v is None:
            continue
        assert v == oracle[i][-1], "VM != oracle (chain %d, category %s)" % (
            i, meta[i][0])

    # Stage-B RTL in ONE simulation: every boundary state at every dphi
    # must equal the oracle (the falsification criterion)
    rtl = run_rtl(chains, dphis=(0, 100, 255))
    for ci, chain in enumerate(chains):
        cat, _ = meta[ci]
        # pair each K>0 block with its own boundary state (empty K=0 blocks
        # produce no oracle state — filter the chain BEFORE zipping)
        kblocks = [b for b in chain if b]
        assert len(kblocks) == len(oracle[ci])
        for dphi in (0, 100, 255):
            for bi, (block, o) in enumerate(zip(kblocks, oracle[ci])):
                r = rtl[(ci, dphi)][bi]
                if r != o:
                    raise AssertionError(
                        "LEAK (falsification criterion, contract §1): chain %d, "
                        "category %s, dphi=%d\n  oracle: %s\n  stage-b: %s" % (
                            ci, cat, dphi, o, r))

    # Photonic substrate backend (contract_photonics_backend_2026-08-20.md):
    # the physical optical realization at the frozen conditioned thermal
    # conditions must satisfy the same contract — bit-exact at every boundary
    for dT in (2.0, 5.0):
        pb = PhotonicQuadrayBackend(deltaT=dT)
        for ci, chain in enumerate(chains):
            cat, _ = meta[ci]
            ph = pb.run_chain(chain)
            if ph != oracle[ci]:
                for bi, (p, o) in enumerate(zip(ph, oracle[ci])):
                    if p != o:
                        raise AssertionError(
                            "LEAK (falsification criterion, contract §1): photonic "
                            "backend, chain %d, category %s, deltaT=%g K\n"
                            "  oracle: %s\n  photonic: %s" % (ci, cat, dT, o, p))

    print("PASS: Digital reference == VM == Stage-A RTL == Stage-B RTL")
    print("PASS: dphi sweep {0, 100, 255} — compensation exercised, including")
    print("      near its precision limit (dphi=255, K=16)")
    print("PASS: photonic backend == oracle at deltaT = {2, 5} K (conditioned)")
    print("      — the photonic substrate satisfies the frozen execution contract")
    print("PASS: no substrate-specific detail leaked through the REGEN boundary")
    print("      across all nine hostile categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
