# Independent Surd CPU oracle review

Date: 2026-10-07. Scope: read-only review and host checks; no arithmetic,
RTL, ISA, synthesis, or device changes. Arithmetic and architectural semantics
reviewed here are the experimental explicit-denominator CPU extension.

## Frozen authority and outcome

The authority is the owner-approved
`build/spu_surd_register/main_cpu_integration_20261007/annex_draft_02/annex.md`,
SHA-256 `97f1d1ae9401471043b29f837887e71d75407d2b329298743c581df881195066`,
as recorded by `stage_A_closure_01.json` and
`implementation_freeze_01/manifest.json` in that same campaign directory.
The five reviewed oracle/arithmetic sources match their implementation-freeze
hashes. The historical [S0 semantics](../spu_strategy/spec_spu_surd_register_s0_2026-10-06.md)
are a distinct policy: S0 canonicalizes every zero; this CPU interface retains
fitting raw zero. Reusing S0 as the tuple oracle would introduce a false failure.

No defect found in the reviewed ADD/SUB formula, selected zero policy, oracle
alias handling, or commit guard. Host checks passed 60,000 aligned tuple/alias
cases, all eight frozen zero-policy tuple/status expectations, nine overflowing
alias cases, and one uninitialized-source preservation case. These checks test
the Python oracle; they do not establish new RTL, routing, or physical evidence.

## Findings

| Concern | Evidence and interpretation |
|---|---|
| Denominator alignment | `software/experiments/surd_cpu_stream.py:Stream.command` computes `g=gcd(d,f)`, `u=f//g`, `v=d//g`, and `(a*u ± c*v,b*u ± e*v,d*u)`. Independent Fraction component checks establish value equality. This review additionally checks the exact raw tuple against an LCM-derived representation. |
| Unsigned scale factors | `spu13_surd_arith.v` normalizes `(d,0,f)` and uses the wide outputs as `v=d/g`, `u=f/g`, validating positive unsigned 64-bit factors without requiring signed architectural fit. `surd_cpu_products.v` treats ADD/SUB scale factors as unsigned and sign-corrects the coefficient products before 130-bit accumulation. Directed cases exercise scale factors above `2^63-1`. |
| Fitting zero | `fits(result)` runs before `canonical(result)`: `(0,0,raw_d)` survives whenever its positive denominator fits. A nonfitting zero reduces to `(0,0,1)`. `SNORM` always canonicalizes valid zero. A zero-denominator `SLD` fails before committing. All eight cases in frozen `zero_policy_expectations.json` agree with the stream oracle. |
| Aliasing | Python reads `x` and `y` before changing `bank[dst]`. Tuple immutability preserves those values when destination equals either source. RTL captures `lhs/rhs` on acceptance and holds destination identity in `held_dst`; one operation remains in flight. The host check exercises separate destination, destination=left, and destination=right. |
| Failure preservation | The stream updates the bank only under `write`. RTL `bank_we` requires arithmetic status OK or a valid atomic load. Overflow, invalid operands, bad encoding, and engine failure therefore have no arithmetic destination write by inspection. Directed overflow cases read back retained destinations; the review checks host bank equality across overflow and invalid-source failure. |

The coefficient-pair Fraction oracle is independent of the hardware normalizer
and mixed signed/unsigned product correction. It establishes exact values,
while the explicit GCD policy determines representation and fit. It does not
independently verify normalizer timing, fault production, or every CPU encoding.
`Stream.command` is a program generator for validated supported mnemonics;
it is not a complete arbitrary instruction decoder.

## Verification gaps to flag before stronger claims

1. `hardware/tests/spu13/spu13_core_surd_tasks.vh:issue` counts write pulses and
   validates tuple data when a write pulse occurs. It does not compare the
   entire tuple bank and validity bits against a saved snapshot after every
   failure. Some directed failures have explicit destination readbacks; this
   is incomplete coverage of corruption without a write event. Minimal proposed
   correction: snapshot the bank before issue and assert unchanged bank and
   validity on every failed retirement, with initialized poison destinations.
2. Existing directed arithmetic uses destination=left extensively; general
   destination=right and all-sources-equal ADD/SUB coverage is sparse. Minimal
   proposed correction: add those alias shapes for normal commit, rescue,
   and unrescued overflow, with post-retirement source/destination readback.
   This review's host aliases do not substitute for CPU trace checks.
3. `Stream` has no engine-fault production model. The reviewed CPU directed
   program does not inject ENGINE_FAULT into the shared normalizer. Minimal
   proposed correction: inject invalid/nonzero-remainder completion in a
   dedicated simulation fixture and require one status=3 retirement, zero
   writes, exact destination preservation, and acceptance of the next command.
   Keep production arithmetic and the frozen interface unchanged.

These are proposed verification changes, not authorization to consume another
campaign slot or modify the frozen implementation. No failing arithmetic was
silently repaired. Full repository/RTL gates were not rerun for this document.

## Reproduce the host review

Run from the repository root. This command contains no RTL execution or timing
campaign; its observed runtime was approximately four seconds.

```bash
python3 -B - <<'PY'
from fractions import Fraction
from itertools import product
from math import lcm
from pathlib import Path
import hashlib, json
from software.experiments.surd_cpu_stream import Stream
base = Path('build/spu_surd_register/main_cpu_integration_20261007')
manifest = json.loads((base/'implementation_freeze_01/manifest.json').read_text())
for name in ('software/experiments/surd_cpu_stream.py',
             'software/experiments/surd_cpu_directed.py',
             'hardware/rtl/core/spu13/spu13_surd_arith.v',
             'hardware/rtl/core/spu13/spu13_surd_exec.v',
             'hardware/rtl/math/surd_cpu_products.v'):
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == manifest['source_sha256'][name], name
annex = base/'annex_draft_02/annex.md'
assert hashlib.sha256(annex.read_bytes()).hexdigest() == manifest['approved_annex_sha256']
count = 0
for op, sign in [('SADD', 1), ('SSUB', -1)]:
    for a,b,c,e,d,f in product(range(-2,3), range(-2,3), range(-2,3), range(-2,3), range(1,5), range(1,5)):
        x,y = (a,b,d),(c,e,f); den = lcm(d,f)
        wanted = (a*(den//d)+sign*c*(den//f), b*(den//d)+sign*e*(den//f), den)
        for dst in (0,1,2):
            s = Stream(); s.bank[:3] = [x,y,(17,-19,23)]
            s.command(op, [f'S{dst}','S0','S1'])
            assert s.status == 0 and s.bank[dst] == wanted
            assert Fraction(wanted[0],den) == Fraction(a,d)+sign*Fraction(c,f)
            assert Fraction(wanted[1],den) == Fraction(b,d)+sign*Fraction(e,f)
            count += 1
print('PASS aligned tuple and alias cases:', count)
rows = json.loads((base/'annex_draft_02/zero_policy_expectations.json').read_text())['cases']
for row in rows:
    s = Stream(); s.bank[2] = tuple(row.get('initial_destination',[17,-19,23])); op = row['op']
    if op == 'SLD':
        s.load(2, tuple(row['staged_tuple']))
    else:
        initialized = row.get('initialized',[True]*len(row['sources']))
        for i,t in enumerate(row['sources']):
            s.bank[i] = tuple(t) if initialized[i] else None
        s.command(op, ['S2','S0']+(['S1'] if len(row['sources']) == 2 else []))
    assert s.bank[2] == tuple(row['expected_tuple']), row['name']
    assert s.status == {'OK':0,'INVALID':1}[row['status']], row['name']
print('PASS frozen zero-policy tuple/status cases:', len(rows))
for op,x,y in [('SSUB',(-(1<<63),0,1),(1,0,1)),
               ('SMUL',(-(1<<63),0,1),(-1,0,1)),
               ('SADD',(1,0,(1<<64)-1),(-1,0,2))]:
    for dst in (0,1,2):
        s = Stream(); s.bank[:3] = [x,y,(17,-19,23)]; old = list(s.bank)
        s.command(op, [f'S{dst}','S0','S1'])
        assert s.status == 2 and s.bank == old
s = Stream(); s.bank[2] = (17,-19,23); s.command('SNORM',['S2','S0'])
assert s.status == 1 and s.bank[2] == (17,-19,23)
print('PASS overflow aliases and uninitialized-source preservation')
PY
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/SURD_CPU_ORACLE_REVIEW_2026-10-07.md
```

Because the review is a new untracked document, also inspect its whitespace
directly; `git diff --check` alone does not inspect untracked file content.
