#!/usr/bin/env python3
"""
spu13_asm.py — SPU-13 Sovereign Assembler v3.0
ISA v1.2 — 23 opcodes, Q(√3) rational field

Encoding: [Op:8][R1:8][R2:8][P1_A:16][P1_B:16][Unused:8] = 64-bit word

Usage:
    python3 spu13_asm.py source.sas              # → source.bin
    python3 spu13_asm.py source.sas output.bin   # explicit output
    python3 spu13_asm.py --hex source.sas        # print hex words

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
    """Return ('QR'|'R'|'IMM', index/value)."""
    t = tok.upper()
    if t.startswith('QR'):
        return 'QR', int(t[2:]) & 0xFF
    if t.startswith('R'):
        return 'R', int(t[1:]) & 0xFF
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
        p1_a    = _u16(args[1]) if len(args) > 1 else 0
        p1_b    = _u16(args[2]) if len(args) > 2 else 0

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


def assemble(source: str, filename: str = "<input>") -> list[int]:
    """Two-pass assembler. Returns list of 64-bit words."""
    lines  = source.splitlines()
    labels: dict[str, int] = {}
    words:  list[int]      = []

    # --- Pass 1: collect labels ------------------------------------------
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

    # --- Pass 2: emit words ----------------------------------------------
    for lineno, raw in enumerate(lines, 1):
        clean = raw.split(';')[0].strip()
        if not clean:
            continue
        parts = clean.replace(',', ' ').split()
        mnemonic = parts[0].upper()
        if mnemonic.endswith(':'):
            continue
        if mnemonic not in OPCODES:
            raise AssemblyError(f"{filename}:{lineno}: unknown mnemonic '{mnemonic}'")
        try:
            word = _assemble_line([mnemonic] + parts[1:], labels)
            words.append(word)
        except (IndexError, ValueError) as e:
            raise AssemblyError(f"{filename}:{lineno}: bad operands — {e}") from e

    return words


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    hex_mode = '--hex' in argv
    args     = [a for a in argv if not a.startswith('--')]

    if not args:
        print(__doc__)
        return 1

    src_path = Path(args[0])
    if not src_path.exists():
        print(f"Error: file not found: {src_path}")
        return 1

    source = src_path.read_text()

    try:
        words = assemble(source, str(src_path))
    except AssemblyError as e:
        print(f"Assembly failed: {e}")
        return 1

    if hex_mode:
        print(f"--- SPU-13 Assembler v3.0 | {src_path.name} | {len(words)} words ---")
        for i, w in enumerate(words):
            op  = (w >> 56) & 0xFF
            r1  = (w >> 48) & 0xFF
            r2  = (w >> 40) & 0xFF
            pa  = (w >> 24) & 0xFFFF
            pb  = (w >>  8) & 0xFFFF
            from spu_vm import OPNAMES  # optional pretty-print
            name = OPNAMES.get(op, f"0x{op:02X}")
            print(f"  [{i:04d}]  {w:016X}  {name:<8}  r1={r1} r2={r2} "
                  f"a={_s16(pa)} b={_s16(pb)}")
        return 0

    out_path = Path(args[1]) if len(args) > 1 else src_path.with_suffix('.bin')
    with out_path.open('wb') as f:
        for w in words:
            f.write(struct.pack('>Q', w))

    print(f"SPU-13 Assembler v3.0 | {len(words)} words → {out_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
