#!/usr/bin/env python3
"""
spu13_asm.py — SPU-13 Sovereign Assembler v3.1
ISA v1.2 — 23 opcodes, Q(√3) rational field

Encoding: [Op:8][R1:8][R2:8][P1_A:16][P1_B:16][Unused:8] = 64-bit word

Usage:
    python3 spu13_asm.py source.sas              # → source.bin (fold pass on)
    python3 spu13_asm.py source.sas output.bin   # explicit output
    python3 spu13_asm.py --hex source.sas        # print hex words
    python3 spu13_asm.py --no-fold source.sas    # skip constant-folding pass

Syntax:
    ; comment
    LABEL:
    LD   Rd, a, b          ; Rd = a + b·√3
    ADD  Rd, Rs1, Rs2      ; Rd = Rs1 + Rs2
    SUB  Rd, Rs1, Rs2
    MUL  Rd, Rs1, Rs2      ; Q(√3) polynomial multiply
    ROT  Rd, Rs            ; Pell step: Rd *= Rs
    LOG  Rd                ; print Rd
    JMP  LABEL             ; unconditional jump
    COND Rn, LABEL         ; jump if Q(Rn) == 0
    CALL LABEL             ; push PC, jump
    RET                    ; pop PC
    SNAP                   ; Davis Gate Q-check all regs
    NOP
    HALT
    QLOAD QRn, Rb          ; load QR[n] from R[b]..R[b+3]
    QLOG  QRn              ; print QR[n]
    QADD  QRd, QRs         ; QRd += QRs
    QROT  QRd, Rs          ; Pell-rotate each component by Rs
    QNORM QRn              ; normalize (min component → 0)
    HEX   Rd, QRn          ; Rd = hex_project(QR[n])
    SPREAD Rd, QRa, QRb    ; Rd = spread(QR[a], QR[b])
    EQUIL                  ; assert hex-sum of all QR = (0,0)
    IDNT  QRn              ; QRn ← [1,0,0,0]
    JINV  Rn               ; flip surd sign: a+b√3 → a-b√3
    ANNE  QRn              ; anneal: halve all components
"""

import sys
import struct
from pathlib import Path

# ---------------------------------------------------------------------------
# Opcode table — must stay in sync with spu_vm.py OPCODES dict
# ---------------------------------------------------------------------------
OPCODES: dict[str, int] = {
    # Scalar Q(√3) arithmetic
    "LD":     0x00, "ADD":    0x01, "SUB":    0x02,
    "MUL":    0x03, "ROT":    0x04, "LOG":    0x05,
    # Control flow
    "JMP":    0x06, "SNAP":   0x07, "COND":   0x20,
    "CALL":   0x21, "RET":    0x22, "HALT":   0x08,
    # Quadray IVM operations
    "QADD":   0x10, "QROT":   0x11, "QNORM":  0x12,
    "QLOAD":  0x13, "QLOG":   0x14,
    # Geometry output
    "SPREAD": 0x15, "HEX":    0x16,
    # v1.2 — Vector Equilibrium + Janus layer
    "EQUIL":  0x17, "IDNT":   0x18, "JINV":   0x19, "ANNE":   0x1A,
    # No-op
    "NOP":    0xFF,
}

# Opcodes that take no register/immediate arguments
_NO_ARGS  = {"NOP", "HALT", "RET", "SNAP", "EQUIL"}
# Opcodes where first arg is a QR register
_QR_FIRST = {"QLOAD", "QLOG", "QADD", "QROT", "QNORM", "HEX",
              "SPREAD", "IDNT", "ANNE"}


def _s16(val: int) -> int:
    """Sign-extend a 16-bit field to signed Python int."""
    val &= 0xFFFF
    return val - 0x10000 if val >= 0x8000 else val


def _u16(s: str) -> int:
    """Parse integer string → 16-bit unsigned (wraps)."""
    return int(s, 0) & 0xFFFF


def _parse_reg(tok: str) -> tuple[str, int]:
    """Return ('QR'|'R'|'IMM', index/value).

    Supports packed-phinary immediates with the PH0x... syntax.
    """
    t = tok.upper()
    if t.startswith('QR'):
        return 'QR', int(t[2:]) & 0xFF
    if t.startswith('R'):
        return 'R', int(t[1:]) & 0xFF
    if t.startswith('PH'):
        # PH0xNNNN -> immediate packed phinary word (placed into P1_A)
        return 'IMM', int(t[2:], 0)
    return 'IMM', int(tok, 0)


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------

class AssemblyError(Exception):
    pass


def _assemble_line(parts: list[str], labels: dict[str, int]) -> int:
    """
    Encode one instruction into a 64-bit word.
    parts[0] = mnemonic (already upper-cased), parts[1:] = args (no commas).
    """
    mnemonic = parts[0]
    opcode   = OPCODES[mnemonic]
    r1 = r2 = p1_a = p1_b = 0

    args = parts[1:]

    def resolve(tok: str) -> tuple[str, int]:
        t = tok.upper()
        if t in labels:
            return 'IMM', labels[t]
        return _parse_reg(tok)

    if mnemonic in _NO_ARGS:
        pass  # nothing to parse

    elif mnemonic == "LD":
        # LD Rd, a, b  →  r1=reg, p1_a=a (surd real), p1_b=b (surd coeff)
        _, r1   = _parse_reg(args[0])
        if len(args) > 1:
            kind, v = resolve(args[1])
            p1_a = v & 0xFFFF
        else:
            p1_a = 0
        if len(args) > 2:
            kind, v = resolve(args[2])
            p1_b = v & 0xFFFF
        else:
            p1_b = 0

    elif mnemonic in ("ADD", "SUB", "MUL"):
        # Op Rd, Rs1, Rs2
        _, r1 = _parse_reg(args[0])
        _, r2 = _parse_reg(args[1])
        if len(args) > 2:
            kind, v = resolve(args[2])
            if kind in ('R', 'QR'):
                p1_a = v
            else:
                p1_a = v & 0xFFFF

    elif mnemonic == "ROT":
        # ROT Rd [, Rs]  — if one arg, self-rotate (Rs = Rd)
        _, r1 = _parse_reg(args[0])
        _, r2 = _parse_reg(args[1]) if len(args) > 1 else (None, r1)

    elif mnemonic in ("LOG", "SNAP", "JINV"):
        # LOG Rd  /  JINV Rn
        if args:
            _, r1 = _parse_reg(args[0])

    elif mnemonic in ("JMP", "CALL"):
        # JMP LABEL / JMP addr
        kind, v = resolve(args[0])
        p1_a = v & 0xFFFF

    elif mnemonic == "COND":
        # COND Rn, LABEL
        _, r1    = _parse_reg(args[0])
        kind, v  = resolve(args[1])
        p1_a     = v & 0xFFFF

    elif mnemonic == "QLOAD":
        # QLOAD QRn, Rb  — load from R[b]..R[b+3]
        _, r1 = _parse_reg(args[0])   # QR index
        _, r2 = _parse_reg(args[1])   # base scalar reg

    elif mnemonic in ("QLOG", "QNORM", "IDNT", "ANNE"):
        # single QR arg
        _, r1 = _parse_reg(args[0])

    elif mnemonic == "QADD":
        # QADD QRd, QRs
        _, r1 = _parse_reg(args[0])
        _, r2 = _parse_reg(args[1])

    elif mnemonic == "QROT":
        # QROT QRd [, Rs]  — if one arg, use built-in Pell rotor (r2=0)
        _, r1 = _parse_reg(args[0])
        _, r2 = _parse_reg(args[1]) if len(args) > 1 else (None, 0)

    elif mnemonic == "HEX":
        # HEX Rd, QRn
        _, r1 = _parse_reg(args[0])
        _, r2 = _parse_reg(args[1])

    elif mnemonic == "SPREAD":
        # SPREAD Rd, QRa, QRb
        _, r1  = _parse_reg(args[0])
        _, r2  = _parse_reg(args[1])
        _, p1b = _parse_reg(args[2])
        p1_b   = p1b & 0xFFFF

    # Pack: [Op:8][R1:8][R2:8][P1_A:16][P1_B:16][00:8]
    return ((opcode & 0xFF) << 56 |
            (r1     & 0xFF) << 48 |
            (r2     & 0xFF) << 40 |
            (p1_a & 0xFFFF) << 24 |
            (p1_b & 0xFFFF) <<  8)


def _parse_ir(source: str, filename: str = "<input>") -> tuple[dict, list]:
    """
    Pass 1+2: collect labels and parse source into IR.

    Returns:
        labels  — dict[name: str → instruction_index: int]
        ir      — list of (lineno, mnemonic, args, orig_idx)
                  orig_idx is the instruction's position in the original IR;
                  it is preserved by the fold pass so that label remapping
                  remains correct even when instructions are transformed.
    """
    lines  = source.splitlines()
    labels: dict[str, int] = {}
    ir:     list            = []

    addr = 0
    for lineno, raw in enumerate(lines, 1):
        clean = raw.split(';')[0].strip()
        if not clean:
            continue
        tok = clean.split()[0].upper()
        if tok.endswith(':'):
            labels[tok[:-1]] = addr
        elif tok in OPCODES:
            addr += 1

    for lineno, raw in enumerate(lines, 1):
        clean = raw.split(';')[0].strip()
        if not clean:
            continue
        parts    = clean.replace(',', ' ').split()
        mnemonic = parts[0].upper()
        if mnemonic.endswith(':'):
            continue
        if mnemonic not in OPCODES:
            raise AssemblyError(f"{filename}:{lineno}: unknown mnemonic '{mnemonic}'")
        ir.append((lineno, mnemonic, parts[1:], len(ir)))

    return labels, ir


# ---------------------------------------------------------------------------
# Constant-folding pass
# ---------------------------------------------------------------------------

def _fold_pass(ir: list, labelled_positions: set) -> tuple[list, dict]:
    """
    Symbolic constant-folding over scalar Q(√3) registers.

    IR tuples are (lineno, mnemonic, args, orig_idx).  orig_idx is the
    instruction's position in the original, un-folded IR and is preserved
    (or inherited) through all transformations so that label remapping in
    assemble() stays correct even when instructions are rewritten or removed.

    Forward pass  — tracks known RationalSurd values per register.
                    Clears known-state at every labelled position (loop
                    headers and other jump targets) so that folding never
                    crosses a back-edge.  Also clears at control-flow
                    instructions.  Folds ADD / SUB / MUL / ROT / JINV on
                    all-known operands into a single LD of the exact result;
                    only when the result fits in int16.

    Backward pass — dead-store elimination: removes LD Rd where Rd is
                    unconditionally overwritten before any read.  Never
                    eliminates instructions whose orig_idx is a labelled
                    position (they may be jump targets).

    Returns (optimised_ir, {'folded': N, 'elim': N}).
    """
    _sw = Path(__file__).resolve().parent.parent
    if str(_sw) not in sys.path:
        sys.path.insert(0, str(_sw))
    from spu_vm import RationalSurd  # exact Q(√3) arithmetic

    CLEAR_FLOW = {'JMP', 'CALL', 'RET', 'COND', 'HALT'}
    stats      = {'folded': 0, 'elim': 0}

    def reg(tok: str) -> tuple[str, int]:
        t = tok.upper()
        if t.startswith('QR'): return 'QR', int(t[2:])
        if t.startswith('R'):  return 'R',  int(t[1:])
        return 'IMM', int(tok, 0)

    def s16(v: int) -> int:
        v &= 0xFFFF
        return v - 0x10000 if v >= 0x8000 else v

    def fits(v: int) -> bool:
        return -32768 <= v <= 32767

    # ── Forward: constant propagation + folding ──────────────────────────
    known:   dict[int, RationalSurd] = {}   # scalar reg → known surd value
    folded:  list                    = []

    for lineno, mn, args, oidx in ir:
        # Clear known-state at every labelled position: the register file may
        # hold any values from a previous iteration of a loop or a branch taken
        # from elsewhere in the program.
        if oidx in labelled_positions:
            known.clear()

        if mn in CLEAR_FLOW:
            known.clear()
            folded.append((lineno, mn, args, oidx))
            continue

        if mn == 'LD':
            _, rd = reg(args[0])
            a = s16(int(args[1], 0)) if len(args) > 1 else 0
            b = s16(int(args[2], 0)) if len(args) > 2 else 0
            known[rd] = RationalSurd(a, b)
            folded.append((lineno, mn, args, oidx))

        elif mn in ('ADD', 'SUB', 'MUL'):
            _, rd = reg(args[0])
            _, rs = reg(args[1])
            if rd in known and rs in known:
                vd, vs = known[rd], known[rs]
                res = vd + vs if mn == 'ADD' else vd - vs if mn == 'SUB' else vd * vs
                if fits(res.a) and fits(res.b):
                    known[rd] = res
                    folded.append((lineno, 'LD', [args[0], str(res.a), str(res.b)], oidx))
                    stats['folded'] += 1
                    continue
            known.pop(rd, None)
            folded.append((lineno, mn, args, oidx))

        elif mn == 'ROT':
            _, rd = reg(args[0])
            if rd in known:
                res = known[rd].rotate_phi()
                if fits(res.a) and fits(res.b):
                    known[rd] = res
                    folded.append((lineno, 'LD', [args[0], str(res.a), str(res.b)], oidx))
                    stats['folded'] += 1
                    continue
            known.pop(rd, None)
            folded.append((lineno, mn, args, oidx))

        elif mn == 'JINV':
            _, rd = reg(args[0])
            if rd in known:
                v   = known[rd]
                res = RationalSurd(v.a, -v.b)
                if fits(res.a) and fits(res.b):
                    known[rd] = res
                    folded.append((lineno, 'LD', [args[0], str(res.a), str(res.b)], oidx))
                    stats['folded'] += 1
                    continue
            folded.append((lineno, mn, args, oidx))

        else:
            # Conservatively invalidate any scalar destination we don't fold.
            if args:
                try:
                    kind, rd = reg(args[0])
                    if kind == 'R':
                        known.pop(rd, None)
                except (ValueError, IndexError):
                    pass
            folded.append((lineno, mn, args, oidx))

    # ── Backward: dead-store elimination ─────────────────────────────────
    # Scalar read/write sets per mnemonic (conservative for unknowns).
    def rw(mn: str, args: list) -> tuple[set, set]:
        reads, writes = set(), set()
        if not args:
            return reads, writes
        try:
            k0, i0 = reg(args[0])
        except (ValueError, IndexError):
            return reads, writes
        s0 = k0 == 'R'

        if mn == 'LD':
            if s0: writes.add(i0)
        elif mn in ('ADD', 'SUB', 'MUL'):
            if s0:
                reads.add(i0)           # in-place: Rd is also read
                writes.add(i0)
            if len(args) > 1:
                try:
                    k1, i1 = reg(args[1])
                    if k1 == 'R': reads.add(i1)
                except (ValueError, IndexError):
                    pass
        elif mn == 'ROT':
            if s0: reads.add(i0); writes.add(i0)
        elif mn in ('LOG', 'COND', 'JINV'):
            if s0: reads.add(i0)
        elif mn == 'QLOAD' and len(args) > 1:
            try:
                _, rb = reg(args[1])
                reads.update({rb, rb+1, rb+2, rb+3})
            except (ValueError, IndexError):
                pass
        elif mn in ('SPREAD', 'HEX'):
            if s0: writes.add(i0)
        elif mn == 'SNAP':
            reads.update(range(256))    # checks all regs
        return reads, writes

    # pending_ld[rd] = index into folded[] — candidate for dead-store removal.
    # Cleared (assumed live) at control-flow boundaries.
    # Labelled-position checks use orig_idx (folded[i][3]) so that the guard
    # still works after the forward pass has shifted instruction indices.
    pending_ld:   dict[int, int] = {}
    pending_used: set[int]       = set()
    dead:         set[int]       = set()

    for i, (lineno, mn, args, oidx) in enumerate(folded):
        if mn in CLEAR_FLOW:
            # Conservatively mark all pending LDs as live before a branch.
            pending_used.update(pending_ld.values())
            pending_ld.clear()
            continue

        reads, writes = rw(mn, args)

        for r in reads:
            if r in pending_ld:
                pending_used.add(pending_ld[r])

        if mn == 'LD' and writes:
            rd = next(iter(writes))
            prev = pending_ld.get(rd)
            if prev is not None and prev not in pending_used:
                # Guard: never eliminate an instruction that is a jump target.
                prev_oidx = folded[prev][3]
                if prev_oidx not in labelled_positions:
                    dead.add(prev)
                    stats['elim'] += 1
            pending_ld[rd] = i
        else:
            for r in writes:
                pending_ld.pop(r, None)

    # Any LD still pending at program end that was never read is dead.
    for rd, i in pending_ld.items():
        if i not in pending_used and folded[i][3] not in labelled_positions:
            dead.add(i)
            stats['elim'] += 1

    optimised = [insn for i, insn in enumerate(folded) if i not in dead]
    return optimised, stats


# ---------------------------------------------------------------------------
# Assembler (three-pass)
# ---------------------------------------------------------------------------

def assemble(source: str, filename: str = "<input>",
             fold: bool = True) -> tuple[list[int], dict]:
    """
    Three-pass assembler.  Returns (list[64-bit words], fold_stats).
    fold_stats is empty when fold=False.
    """
    labels, ir = _parse_ir(source, filename)

    fold_stats: dict = {}
    if fold:
        labelled = set(labels.values())
        ir, fold_stats = _fold_pass(ir, labelled)

        # Recompute label → new PC after the fold pass may have removed or
        # rewritten instructions.  Each IR tuple carries an orig_idx (set by
        # _parse_ir and preserved by _fold_pass) that ties every surviving
        # instruction back to its position in the original IR.  Build a map
        # orig_idx → new_pc and remap the label dict through it.
        orig_idx_to_new_pc = {insn[3]: new_pc for new_pc, insn in enumerate(ir)}
        labels = {name: orig_idx_to_new_pc[old_pc]
                  for name, old_pc in labels.items()
                  if old_pc in orig_idx_to_new_pc}

    words: list[int] = []
    for lineno, mnemonic, args, *_ in ir:   # *_ tolerates both 3- and 4-tuples
        try:
            word = _assemble_line([mnemonic] + args, labels)
            words.append(word)
        except (IndexError, ValueError) as e:
            raise AssemblyError(f"{filename}:{lineno}: bad operands — {e}") from e

    return words, fold_stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    hex_mode  = '--hex'     in argv
    no_fold   = '--no-fold' in argv
    flags     = {a for a in argv if a.startswith('--')}
    args      = [a for a in argv if not a.startswith('--')]

    if not args:
        print(__doc__)
        return 1

    src_path = Path(args[0])
    if not src_path.exists():
        print(f"Error: file not found: {src_path}")
        return 1

    source = src_path.read_text()

    try:
        words, fold_stats = assemble(source, str(src_path), fold=not no_fold)
    except AssemblyError as e:
        print(f"Assembly failed: {e}")
        return 1

    fold_note = ""
    if fold_stats:
        fold_note = (f"  [fold: {fold_stats['folded']} folded, "
                     f"{fold_stats['elim']} dead stores eliminated]")

    if hex_mode:
        print(f"--- SPU-13 Assembler v3.1 | {src_path.name} | {len(words)} words"
              f"{fold_note} ---")
        _sw = Path(__file__).resolve().parent.parent
        if str(_sw) not in sys.path:
            sys.path.insert(0, str(_sw))
        from spu_vm import OPNAMES
        for i, w in enumerate(words):
            op  = (w >> 56) & 0xFF
            r1  = (w >> 48) & 0xFF
            r2  = (w >> 40) & 0xFF
            pa  = (w >> 24) & 0xFFFF
            pb  = (w >>  8) & 0xFFFF
            name = OPNAMES.get(op, f"0x{op:02X}")
            print(f"  [{i:04d}]  {w:016X}  {name:<8}  r1={r1} r2={r2} "
                  f"a={_s16(pa)} b={_s16(pb)}")
        return 0

    out_path = Path(args[1]) if len(args) > 1 else src_path.with_suffix('.bin')
    with out_path.open('wb') as f:
        for w in words:
            f.write(struct.pack('>Q', w))

    print(f"SPU-13 Assembler v3.1 | {len(words)} words → {out_path}{fold_note}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
