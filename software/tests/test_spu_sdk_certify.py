#!/usr/bin/env python3
"""SPU-ECO-6: certified bounded evaluation (spu_certify.py). Software verification only; no hardware run is claimed.
Run: python3 software/tests/test_spu_sdk_certify.py"""
import copy, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'software/sdk'), str(ROOT / 'software/tests')]
import spu_geom as G, spu_certify as C, spu_v03_backend as B

fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)

def alts(pts, k=4):                                              # two user-supplied alternatives for the same triangle
    out = {}
    for name, fn in (('triple-quad expansion', G.triple_quad_points), (f'{k} * orientation^2', lambda a, b, c: k * G.orientation(a, b, c) ** 2)):
        g = G.Geometry(); P = [g.point(*p) for p in pts]; g.result(fn(*P)); out[name] = g
    return out
STD = ((0, 0), (4, 1), (1, 3)); WIT = ((39798, 37420), (-89693, 36555), (30454, 25765)); WEXACT = 9013625693308608100

with tempfile.TemporaryDirectory() as t:
    vm = Path(t) / 'spu_vm'
    check('C++ simulator builds', subprocess.run(['make', '-s', '-C', str(ROOT / 'software/vm'), f'BIN={vm}'], capture_output=True).returncode == 0)

    rep = C.certify(alts(STD), str(vm)); c = {x.name: x for x in rep.certificates}
    check('standard triangle: equivalent, both COMMITTED with S0 = 484 on the oracle and the simulator',
          rep.equivalent and all(x.outcome == C.COMMITTED and x.oracle['s0'] == (484, 0, 1) == x.simulator['s0'] and x.oracle == x.simulator for x in c.values()))
    check('standard triangle: words 38 and 21; prediction agrees (no refusal)', (c['triple-quad expansion'].words, c['4 * orientation^2'].words) == (38, 21) and all(not x.predicted['rs'] for x in c.values()))

    c_ok = c['triple-quad expansion']
    rep = C.certify(alts(WIT), str(vm)); c = {x.name: x for x in rep.certificates}; tq, fo = c['triple-quad expansion'], c['4 * orientation^2']
    check('witness: exact value 9013625693308608100 for both', all(v == (WEXACT, 0) for v in rep.exact.values()))
    check('witness: triple-quad is REFUSED and 4D^2 is COMMITTED', tq.outcome == C.REFUSED and fo.outcome == C.COMMITTED and fo.oracle['s0'] == (WEXACT, 0, 1))
    check('witness: first refusal, later arithmetic and sticky RS are reported apart from the final state',
          tq.predicted['first_refusal'] == (24, 'SMUL') and tq.predicted['arithmetic_after_first_refusal'] == 7 and tq.oracle['rs'] and not tq.oracle['r'] and tq.oracle['s7'][0] == 2)
    check('witness: the refused S0 is not the exact value, and prediction, oracle and simulator all agree',
          tq.oracle['s0'] != (WEXACT, 0, 1) and tq.oracle == tq.simulator and tq.predicted['rs'] == tq.oracle['rs'] and tq.predicted['s0'] == tq.oracle['s0'])
    text = C.format_report(rep)
    row = next(l for l in text.splitlines() if l.startswith('triple-quad expansion'))
    check('report text: the refused candidate is not shown as COMMITTED, and the limits are stated', 'REFUSED' in row and 'COMMITTED' not in row and 'not a proof' in text)

    check('non-equivalent alternatives: equivalence error, no certificates, nothing executed (a missing simulator path is never touched)',
          (lambda r: (not r.equivalent) and r.certificates == [] and 'equivalence error' in r.error)(C.certify(alts(STD, k=3), '/nonexistent/spu_vm')))

    g = G.Geometry(); u = g.const(4000000000); a = u * u; b = u * u; g.result(a - b)
    r = C.certify({'refuses into uninitialized registers': g}, str(vm)).certificates[0]
    check('refusal into an uninitialized register: both backends fault INVALID with RS = 1 and the same record',
          r.oracle['cause'] == 'INVALID' == r.simulator['cause'] and r.oracle['rs'] and r.oracle == r.simulator and r.predicted is None)
    check('regression: no complete prediction gives DISAGREEMENT with an incomplete-verification diagnostic, never REFUSED or COMMITTED',
          r.outcome == C.DISAGREEMENT and any(n.startswith('incomplete verification') for n in r.notes))
    check('regression: the diagnostic does not claim a numerical disagreement, and the observed fault and refusal are preserved',
          any('not evidence of a numerical disagreement' in n for n in r.notes) and any('cause INVALID' in n and 'sticky RS = 1' in n for n in r.notes))

    text = C.format_report(C.Report(True, None, {r.name: r.exact}, [r])); row = next(l for l in text.splitlines() if l.startswith('refuses into'))
    check('regression: an uninitialized S7 is labelled uninitialized in the report and never shown as a valid status (not 0 or ok)',
          'uninitialized' in row and 'ok (0)' not in row and 'refused (2)' not in row and r.oracle['s7_status'] == 'uninitialized')
    check('regression: the raw S7 register value and its initialized flag are retained, and the incomplete-verification note shows both',
          r.oracle['s7'] == (0, 0, 0) and r.oracle['s7_initialized'] is False and any('S7 uninitialized (raw (0, 0, 0))' in n for n in r.notes))
    check('regression: valid statuses are labelled (ok for completed, refused for refusal)', c_ok.oracle['s7_status'] == 'ok (0)' and tq.oracle['s7_status'] == 'refused (2)')
    g = G.Geometry(); vs = [g.const(i) + g.const(i) for i in range(8)]; acc = vs[0]
    for v in vs[1:]: acc = acc + v
    g.result(acc)
    try: C.certify({'too many live values': g}, str(vm)); msg = ''
    except B.CompileError as e: msg = str(e)
    check('a candidate that cannot compile raises a CompileError naming it', msg.startswith('too many live values:'))

# classification negative controls (pure function): a wrong prediction or observation must be detected, a refusal must never become COMMITTED
pred = dict(rs=False, s7=(0, 0, 1), s0=(5, 0, 1), refusals=0, first_refusal=None, arithmetic_after_first_refusal=None, final_r=False)
ora = dict(cause='HALT', retired=9, rs=False, r=False, s7=(0, 0, 1), s7_initialized=True, s7_status='ok (0)', s0=(5, 0, 1), s0_initialized=True); ex = (5, 0)
check('control: a consistent run is COMMITTED', C.classify(pred, ora, ora, ex, True)[0] == C.COMMITTED)
check('control: oracle and simulator records that differ are DISAGREEMENT', C.classify(pred, ora, ora, ex, False)[0] == C.DISAGREEMENT)
check('control: a wrong predicted S0 is DISAGREEMENT', C.classify(dict(pred, s0=(6, 0, 1)), ora, ora, ex, True)[0] == C.DISAGREEMENT)
check('control: a wrong observed S0 with no refusal is DISAGREEMENT', C.classify(dict(pred, s0=(6, 0, 1)), dict(ora, s0=(6, 0, 1)), dict(ora, s0=(6, 0, 1)), ex, True)[0] == C.DISAGREEMENT)
check('control: predicted refusal but none observed is DISAGREEMENT', C.classify(dict(pred, rs=True, s7=(2, 0, 1), first_refusal=(3, 'SMUL'), refusals=1, arithmetic_after_first_refusal=0), ora, ora, ex, True)[0] == C.DISAGREEMENT)
rp, ro = dict(pred, rs=True, s7=(2, 0, 1), first_refusal=(3, 'SMUL'), refusals=1, arithmetic_after_first_refusal=0, final_r=True), dict(ora, rs=True, r=True, s7=(2, 0, 1), s7_status='refused (2)')
out, notes = C.classify(rp, ro, ro, ex, True)
check('control: a refused run whose S0 EQUALS the exact value is still REFUSED, and says so', out == C.REFUSED and any('coincidence' in n for n in notes))
check('control: a prediction exists but S7 is uninitialized: DISAGREEMENT, never COMMITTED', C.classify(pred, dict(ora, s7=(0, 0, 0), s7_initialized=False, s7_status='uninitialized'), dict(ora, s7=(0, 0, 0), s7_initialized=False, s7_status='uninitialized'), ex, True)[0] == C.DISAGREEMENT)
bad7 = dict(ora, s7=(3, 0, 1), s7_status=C.status_label((3, 0, 1), True))
check('control: an initialized S7 that is neither ok nor refused is labelled invalid with its raw value, and the run is DISAGREEMENT',
      bad7['s7_status'] == 'invalid (3, 0, 1)' and C.classify(pred, bad7, bad7, ex, True)[0] == C.DISAGREEMENT)
check('control: status labels (ok, refused, uninitialized, invalid) and the raw value is never replaced by the label',
      [C.status_label(t, i) for t, i in (((0, 0, 1), True), ((2, 0, 1), True), ((0, 0, 0), False), ((0, 0, 1), False), ((2, 0, 2), True))] == ['ok (0)', 'refused (2)', 'uninitialized', 'uninitialized', 'invalid (2, 0, 2)'])
check('control: no prediction and no refusal observed is DISAGREEMENT (incomplete), never COMMITTED', C.classify(None, ora, ora, ex, True)[0] == C.DISAGREEMENT)
check('control: a refused run is never COMMITTED, whatever S0 holds', all(C.classify(rp, dict(ro, s0=s), dict(ro, s0=s), ex, True)[0] != C.COMMITTED for s in ((5, 0, 1), (0, 0, 1), (6, 1, 2))))
print(f'\n{"FAIL" if fails else "PASS"}: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
