"""SDK-0 assembler and disassembler for the frozen v0.3 `programmable-surd` profile ONLY.

Contract: docs/design/SPU_V03_CONTRACT_CANDIDATE.md (image revision 0x03; §10 SPUI image). The target profile is
never inferred (D-1 condition 2): callers pass profile='programmable-surd'. This is NOT the SPU-13 assembler
(software/tools/spu13_asm.py) nor spu-sim's SAS (spu13-soft-v1); their mnemonics are rejected here.
Encoding is implemented from the ISA table independently of software/tests/psurd_oracle.py (tests cross-check).
Source: one instruction per line, `label:` prefixes, `;` or `#` comments, decimal or 0x integers.
  SLI Sd, s, u32 | SLD Sd | SMUL/SADD/SSUB Sd, Sa, Sb | SNORM Sd, Sa | SLIK Sd, i32 | STST Sa | BR cc, target | HALT
  LOADT Sd, a, b, d   macro: the 6 SLI + SLD words that load (a + b*sqrt3)/d (7 words)
  .word VALUE         one raw 64-bit word (for fault and negative tests; may be BAD_ENCODING at run time)
  .profile NAME       optional; must equal the profile given to the assembler
"""
import re, zlib

PROFILE, PROFILE_ID, REVISION = 'programmable-surd', 0x01, 0x03
CC = dict(AL=0, EQ=1, NE=2, LT=3, GE=4, GT=5, LE=6, RF=7, NR=8, RS=9)
OPS = dict(SLI=0x70, SLD=0x71, SMUL=0x73, SADD=0x74, SSUB=0x75, SNORM=0x76, SLIK=0x78, STST=0x79, BR=0x7A, HALT=0x7B)
FORMS = dict(SLI='rsu', SLD='r', SMUL='rrr', SADD='rrr', SSUB='rrr', SNORM='rr', SLIK='ri', STST='r', BR='ct', HALT='',
             LOADT='rIIU')
HALT_WORD = 0x7B << 56
M64 = 1 << 64

class AsmError(Exception): pass

def W(op, r1=0, r2=0, p=0, low=0): return op << 56 | r1 << 48 | r2 << 40 | p << 24 | low
def enc(m, a):
    if m == 'SLI': return W(0x70, a[0], a[1]) | a[2] << 8
    if m in ('SLD',): return W(0x71, a[0])
    if m in ('SMUL', 'SADD', 'SSUB'): return W(OPS[m], a[0], a[1]) | a[2] << 24
    if m == 'SNORM': return W(0x76, a[0], a[1])
    if m == 'SLIK': return W(0x78, a[0]) | (a[1] & 0xFFFFFFFF) << 8
    if m == 'STST': return W(0x79, 0, a[0])
    if m == 'BR': return W(0x7A, a[0], 0, a[1])
    if m == 'HALT': return HALT_WORD
def loadt(r, a, b, d): return [W(0x70, r, s) | ((v % M64) >> (32 * (s % 2)) & 0xFFFFFFFF) << 8
                                for s, v in enumerate((a, a, b, b, d, d))] + [W(0x71, r)]

INT = re.compile(r'^[+-]?(0x[0-9a-fA-F]+|[0-9]+)$')
def num(tok, lo, hi, what, ln):
    if not INT.match(tok): raise AsmError(f'line {ln}: {what} must be an integer, got {tok!r}')
    v = int(tok, 0)
    if not lo <= v <= hi: raise AsmError(f'line {ln}: {what} {v} outside [{lo}, {hi}]')
    return v
def reg(tok, ln):
    m = re.match(r'^[sS]([0-7])$', tok)
    if not m: raise AsmError(f'line {ln}: expected a register S0-S7, got {tok!r}')
    return int(m.group(1))

def assemble(src, profile):
    """Source text -> (words, listing). Raises AsmError on the first defect; nothing is skipped."""
    if profile != PROFILE: raise AsmError(f'profile must be given explicitly as {PROFILE!r} (got {profile!r})')
    items, labels = [], {}; addr = 0
    for ln, raw in enumerate(src.splitlines(), 1):
        line = re.split(r'[;#]', raw, 1)[0].strip()
        while (m := re.match(r'^([A-Za-z_]\w*):\s*(.*)$', line)):
            if m.group(1) in labels: raise AsmError(f'line {ln}: duplicate label {m.group(1)!r}')
            labels[m.group(1)] = addr; line = m.group(2)
        if not line: continue
        mn, _, rest = line.partition(' '); mn = mn.upper(); ops = [t.strip() for t in rest.split(',')] if rest.strip() else []
        if mn == '.PROFILE':
            if ops != [PROFILE]: raise AsmError(f'line {ln}: source declares profile {rest.strip()!r}; this assembler targets {PROFILE}')
            continue
        if mn == '.WORD':
            if len(ops) != 1: raise AsmError(f'line {ln}: .word takes one value')
            items.append((ln, raw, '.WORD', [num(ops[0], 0, M64 - 1, 'word', ln)])); addr += 1; continue
        if mn not in FORMS: raise AsmError(f'line {ln}: {mn!r} is not a {PROFILE} v0.3 instruction')
        form = FORMS[mn]
        if len(ops) != len(form): raise AsmError(f'line {ln}: {mn} takes {len(form)} operand(s), got {len(ops)}')
        items.append((ln, raw, mn, ops)); addr += 7 if mn == 'LOADT' else 1
    if not 1 <= addr <= 256: raise AsmError(f'image length {addr} outside 1..256 words')
    words, listing = [], []
    for ln, raw, mn, ops in items:
        if mn == '.WORD': out = [ops[0]]
        else:
            a = []
            for kind, t in zip(FORMS[mn], ops):
                if kind == 'r': a.append(reg(t, ln))
                elif kind == 's': a.append(num(t, 0, 5, 'slice', ln))
                elif kind == 'u': a.append(num(t, 0, 2 ** 32 - 1, 'u32', ln))
                elif kind == 'i': a.append(num(t, -2 ** 31, 2 ** 31 - 1, 'i32', ln))
                elif kind == 'I': a.append(num(t, -2 ** 63, 2 ** 63 - 1, 'coefficient', ln))
                elif kind == 'U': a.append(num(t, 1, M64 - 1, 'denominator', ln))
                elif kind == 'c':
                    if t.upper() not in CC: raise AsmError(f'line {ln}: unknown condition {t!r}')
                    a.append(CC[t.upper()])
                elif kind == 't':
                    tgt = labels.get(t) if t in labels else (num(t, 0, 65535, 'target', ln) if INT.match(t) else None)
                    if tgt is None: raise AsmError(f'line {ln}: undefined label {t!r}')
                    if tgt >= addr: raise AsmError(f'line {ln}: branch target {tgt} is not inside the {addr}-word image')
                    a.append(tgt)
            out = loadt(*a) if mn == 'LOADT' else [enc(mn, a)]
        listing.append((len(words), out, raw.strip())); words += out
    return words, listing

def image(words):
    body = b''.join(w.to_bytes(8, 'big') for w in words)
    return b'SPUI' + bytes([PROFILE_ID, REVISION]) + len(words).to_bytes(2, 'little') + zlib.crc32(body).to_bytes(4, 'little') + body
def parse_image(b):
    """SPUI bytes -> words, with the loader's header checks (§10). Raises ValueError."""
    if len(b) < 12 or b[:4] != b'SPUI': raise ValueError('bad framing')
    if b[4] != PROFILE_ID or b[5] != REVISION: raise ValueError(f'architecture identity {b[4]:#04x}/{b[5]:#04x} is not programmable-surd rev 3')
    L = int.from_bytes(b[6:8], 'little')
    if not 1 <= L <= 256 or len(b) != 12 + 8 * L: raise ValueError('bad length')
    if zlib.crc32(b[12:]) != int.from_bytes(b[8:12], 'little'): raise ValueError('CRC mismatch')
    return [int.from_bytes(b[12 + 8 * i:20 + 8 * i], 'big') for i in range(L)]

def decode(w, L):
    """One word -> (mnemonic, operands) or None if execution would fault BAD_ENCODING (contract decode rules)."""
    op, r1, r2, mid, sb = w >> 56, w >> 48 & 255, w >> 40 & 255, w >> 32 & 255, w >> 24 & 255
    if op == 0x70 and r1 < 8 and r2 < 6 and w & 255 == 0: return 'SLI', (r1, r2, w >> 8 & 0xFFFFFFFF)
    if op == 0x71 and r1 < 8 and r2 == 0 and w & (2 ** 40 - 1) == 0: return 'SLD', (r1,)
    if op in (0x73, 0x74, 0x75) and r1 < 8 and r2 < 8 and mid == 0 and sb < 8 and w & 0xFFFFFF == 0:
        return {0x73: 'SMUL', 0x74: 'SADD', 0x75: 'SSUB'}[op], (r1, r2, sb)
    if op == 0x76 and r1 < 8 and r2 < 8 and w & (2 ** 40 - 1) == 0: return 'SNORM', (r1, r2)
    if op == 0x78 and r1 < 8 and r2 == 0 and w & 255 == 0:
        i = w >> 8 & 0xFFFFFFFF; return 'SLIK', (r1, i - (1 << 32) * (i >> 31))
    if op == 0x79 and r1 == 0 and r2 < 8 and w & (2 ** 40 - 1) == 0: return 'STST', (r2,)
    if op == 0x7A and r1 <= 9 and r2 == 0 and w & 0xFFFFFF == 0: return 'BR', (r1, w >> 24 & 0xFFFF)
    if w == HALT_WORD: return 'HALT', ()
    return None

def disassemble(words, macros=True):
    names = {v: k for k, v in CC.items()}; dec = [decode(w, len(words)) for w in words]
    targets = {d[1][1] for d in dec if d and d[0] == 'BR'}; out = []; i = 0
    while i < len(words):
        lab = f'L{i}: ' if i in targets else ''
        d = dec[i]; s = None
        if macros and d and d[0] == 'SLI' and i + 6 < len(words) and not targets & set(range(i + 1, i + 7)):
            seq = dec[i:i + 7]; r = d[1][0]
            if all(x and x[0] == 'SLI' and x[1][0] == r and x[1][1] == k for k, x in enumerate(seq[:6])) and seq[6] == ('SLD', (r,)):
                v = [seq[2 * k][1][2] | seq[2 * k + 1][1][2] << 32 for k in range(3)]
                if v[2]:
                    out.append(f'{lab}LOADT S{r}, {v[0] - M64 * (v[0] >> 63)}, {v[1] - M64 * (v[1] >> 63)}, {v[2]}'); i += 7; continue
        if d is None: s = f'.word 0x{words[i]:016x}  ; BAD_ENCODING at run time'
        else:
            m, a = d
            s = {'SLI': lambda: f'SLI S{a[0]}, {a[1]}, 0x{a[2]:08x}', 'SLD': lambda: f'SLD S{a[0]}',
                 'SNORM': lambda: f'SNORM S{a[0]}, S{a[1]}', 'SLIK': lambda: f'SLIK S{a[0]}, {a[1]}',
                 'STST': lambda: f'STST S{a[0]}', 'BR': lambda: f'BR {names[a[0]]}, ' + (f'L{a[1]}' if a[1] < len(words) else f'{a[1]}  ; BAD_TARGET'),
                 'HALT': lambda: 'HALT'}.get(m, lambda: f'{m} S{a[0]}, S{a[1]}, S{a[2]}')()
        out.append(lab + s); i += 1
    return '\n'.join(['.profile programmable-surd'] + out) + '\n'
