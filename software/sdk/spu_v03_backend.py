"""SPU-ECO-2 v0.3 `programmable-surd` backend for spu_ir.Program: lowering, register allocation, refusal prediction.

lower():  keeps the IR operation order exactly (one SSUB/SADD/SMUL per IR operation, constants in creation order);
          SLIK for a constant with b = 0, d = 1 that fits int32, otherwise LOADT. No algebraic rewriting.
          Registers: S0-S6 for values (S7 is the status register). A value's register is reused when its last use is the
          instruction that overwrites it (operands are read before the write). The result must land in S0: v0.3 has no
          move instruction, so that is a compile error if S0 is busy at the result's definition.
          Rematerialization (ECO-4): only when no register is free, the live CONSTANT whose next use is farthest is
          evicted and reloaded (SLIK/LOADT) just before that use. Arithmetic operations are never reordered, added or
          removed, and loads never refuse, so the refusal sequence is unchanged; only register contents (hence the stale
          value left by a refused operation) may differ. Computed values are never evicted: no data memory.
          Epilogue (as in the hand-written examples): BR RS, refused; SLIK S7,0; HALT; refused: SLIK S7,2; HALT.
predict(): replays the LOWERED instruction sequence, register by register, with the machine arithmetic of
          software/tests/psurd_oracle.py (the SurdFixed64 / psurd_arith semantics). A refused SMUL/SADD/SSUB leaves its
          destination unchanged, so stale values are tracked. This is a prediction; it is not a simulator run."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
import psurd_oracle as O
import spu_asm as A

class CompileError(Exception): pass
VALUE_REGS, MAXWORDS, EPILOGUE_WORDS = 7, 256, 5
MNEMONIC = {'add': 'SADD', 'sub': 'SSUB', 'mul': 'SMUL'}

def lower(prog):
    st = prog.stmts
    if prog.out is None: raise CompileError('no result selected')
    opsof = lambda s: list(dict.fromkeys(s[1:])) if s[0] != 'const' else []
    uses = {i: [] for i in range(len(st))}
    for i, s in enumerate(st):
        for j in opsof(s): uses[j].append(i)
    last = {i: (uses[i][-1] if uses[i] else i) for i in range(len(st))}
    last[prog.out] = len(st)                                  # the result stays live to the end
    free, reg, ins = list(range(VALUE_REGS)), {}, []
    def load(j, d):
        a, b, den = st[j][1]
        if not (-2**63 <= a < 2**63 and -2**63 <= b < 2**63 and 0 < den < 2**64): raise CompileError(f'statement {j}: constant {st[j][1]} does not fit 64-bit fields')
        ins.append(('SLIK', d, a) if b == 0 and den == 1 and -2**31 <= a < 2**31 else ('LOADT', d, (a, b, den)))
    def take(i, protect):                                     # a free register; else evict the live constant used farthest away
        if free: return free.pop(0)
        cand = [v for v in reg if st[v][0] == 'const' and v not in protect and v != prog.out and last[v] > i]
        if not cand: raise CompileError(f'statement {i}: more than {VALUE_REGS} live values (no data memory)')
        return reg.pop(max(cand, key=lambda v: min(u for u in uses[v] if u > i)))   # reloaded at its next use
    for i, s in enumerate(st):
        ops = opsof(s)
        for j in ops:
            if j not in reg: reg[j] = take(i, set(ops)); load(j, reg[j])          # rematerialize an evicted constant
        dying = [j for j in ops if last[j] == i]
        free = sorted(set(free) | {reg[j] for j in dying})
        if i == prog.out:
            if 0 not in free: raise CompileError(f'statement {i}: the result needs S0 but S0 is busy (no move instruction)')
            free.remove(0); d = 0
        else:
            pref = [reg[j] for j in ops[:2] if j in dying]
            d = pref[0] if pref else take(i, set(ops))
            if d in free: free.remove(d)
        reg[i] = d
        if last[i] == i: free = sorted(free + [d])            # a value that is never used does not hold its register
        if s[0] == 'const': load(i, d)
        else: ins.append((MNEMONIC[s[0]], d, reg[s[1]], reg[s[2]]))
    words = sum(7 if x[0] == 'LOADT' else 1 for x in ins) + EPILOGUE_WORDS
    if words > MAXWORDS: raise CompileError(f'image would be {words} words; the limit is {MAXWORDS}')
    return ins, reg[prog.out], words

def to_asm(ins):
    f = {'SLIK': lambda x: f'SLIK S{x[1]}, {x[2]}', 'LOADT': lambda x: 'LOADT S%d, %d, %d, %d' % ((x[1],) + x[2])}
    body = [f[x[0]](x) if x[0] in f else f'{x[0]} S{x[1]}, S{x[2]}, S{x[3]}' for x in ins]
    return '.profile programmable-surd\n' + '\n'.join(['        ' + b for b in body] + [
        '        BR RS, refused', '        SLIK S7, 0', '        HALT', 'refused: SLIK S7, 2', '        HALT']) + '\n'

def compile_v03(prog):
    """-> (asm text, image bytes, words, lowered instructions, result register). Uses the existing assembler."""
    ins, rout, n = lower(prog); asm = to_asm(ins)
    words, _ = A.assemble(asm, A.PROFILE)
    if len(words) != n: raise CompileError('internal: word count mismatch')
    return asm, A.image(words), words, ins, rout

class Prediction:
    def __init__(self, refusals, regs, rout, trace): self.refusals, self.regs, self.rout, self.trace = refusals, regs, rout, trace
    rs = property(lambda s: bool(s.refusals))
    s7 = property(lambda s: 2 if s.refusals else 0)
    result = property(lambda s: s.regs[s.rout])              # S0; when rs, NOT the mathematical result

def predict(ins, rout):
    regs, refusals, trace = {}, [], []                        # trace: (mnemonic, x, y, result or None) per arithmetic op
    for k, x in enumerate(ins):
        if x[0] == 'SLIK': regs[x[1]] = (x[2], 0, 1)
        elif x[0] == 'LOADT': regs[x[1]] = x[2]
        else:
            a, b = regs[x[2]], regs[x[3]]
            r = O.mul(a, b) if x[0] == 'SMUL' else O.addsub(a, b, 1 if x[0] == 'SADD' else -1)
            trace.append((x[0], a, b, r))
            if r is None: refusals.append((k, x[0]))        # destination keeps its previous value
            else: regs[x[1]] = r
    return Prediction(refusals, regs, rout, trace)
