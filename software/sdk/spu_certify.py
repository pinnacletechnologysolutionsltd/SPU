"""SPU-ECO-6 certified bounded evaluation of user-supplied alternatives, for FIXED inputs on the v0.3 machine.

certify() takes alternatives (spu_geom.Geometry programs) that the USER claims compute the same value. It does not rewrite, reorder or
merge anything. It (1) evaluates each exact value (unbounded); if they differ, it reports an equivalence error and executes nothing;
(2) compiles each with the existing backend; (3) replays the generated instructions (prediction); (4) runs the image on the oracle and the
C++ simulator; (5) classifies. Four sources are kept apart, but they are not four independent implementations: the exact value is the unbounded evaluation of the supplied
IR expression; the prediction replay (spu_v03_backend.predict) and the Python oracle run both use the arithmetic of software/tests/psurd_oracle.py; the C++ simulator is a
separate implementation and is the independent check on that arithmetic.
COMMITTED     no arithmetic refusal, both runs agree with the prediction, and S0 equals the exact value.
REFUSED       an arithmetic refusal occurred and the whole run was predicted. Never certified, whatever S0 holds (S0 may equal the exact value by coincidence).
DISAGREEMENT  prediction, oracle, simulator or a required invariant disagree, OR no complete prediction could be formed. The second case is an incomplete
              verification, not evidence of a numerical disagreement: the observed refusal or fault is still reported.
A certificate is about THESE inputs and THESE generated images. Agreement for bound inputs does not establish general symbolic equivalence."""
from collections import namedtuple
from fractions import Fraction as F
import spu as CLI, spu_record as REC
import spu_v03_backend as B

COMMITTED, REFUSED, DISAGREEMENT = 'COMMITTED', 'REFUSED', 'DISAGREEMENT'
Certificate = namedtuple('Certificate', 'name outcome words asm predicted oracle simulator exact notes')
Report = namedtuple('Report', 'equivalent error exact certificates')

def status_label(raw, initialized):
    """Meaning of S7 under the programs' own convention. The raw register value is always kept next to it; an uninitialized S7 is never a status."""
    if not initialized: return 'uninitialized'
    return {(0, 0, 1): 'ok (0)', (2, 0, 1): 'refused (2)'}.get(raw, f'invalid {raw}')

def _obs(rec):
    s0, s7, f = rec['registers'][0], rec['registers'][7], rec['flags']; raw7 = (s7['a'], s7['b'], s7['d'])
    return dict(cause=rec['cause'], retired=rec['retired'], rs=bool(f['RS']), r=bool(f['R']), s7=raw7, s7_initialized=bool(s7['initialized']),
                s7_status=status_label(raw7, bool(s7['initialized'])), s0=(s0['a'], s0['b'], s0['d']), s0_initialized=bool(s0['initialized']))
def _eq(t, exact): return t[2] > 0 and F(t[0], t[2]) == exact[0] and F(t[1], t[2]) == exact[1]

def _predicted(pr):
    """Replay summary, or None when the replay cannot model the run (a refused operation left an uninitialized register that is read later)."""
    if pr is None: return None
    tr = pr.trace; first = next((i for i, t in enumerate(tr) if t[3] is None), None)
    return dict(rs=pr.rs, s7=(pr.s7, 0, 1), s0=pr.result, refusals=len(pr.refusals), first_refusal=pr.refusals[0] if pr.refusals else None,
                arithmetic_after_first_refusal=None if first is None else len(tr) - first - 1, final_r=bool(tr and tr[-1][3] is None))

def classify(pred, ora, sim, exact, same_record):
    """Pure classification (also used directly by the tests). pred may be None; ora and sim are _obs dictionaries."""
    if not same_record: return DISAGREEMENT, ['oracle and simulator records are not byte-identical']
    if pred is None:                                           # incomplete verification: never COMMITTED, and not claimed as a numerical disagreement
        obs = f"observed on oracle and simulator: cause {ora['cause']}, sticky RS = {int(ora['rs'])}, final R = {int(ora['r'])}, S7 {ora['s7_status']} (raw {ora['s7']}), S0 {'uninitialized' if not ora['s0_initialized'] else ora['s0']}, retired {ora['retired']}"
        return DISAGREEMENT, ['incomplete verification: the backend replay could not model this run, so there is no complete prediction to compare; this is not evidence of a numerical disagreement', obs]
    bad = [f'{k}: predicted {pred[a]} observed {ora[k]}' for k, a in (('rs', 'rs'), ('r', 'final_r'), ('s7', 's7'), ('s0', 's0')) if ora[k] != pred[a]]
    if ora['cause'] != 'HALT': bad.append(f"cause {ora['cause']} (expected HALT)")
    if not ora['s7_initialized']: bad.append(f"S7 is uninitialized (raw {ora['s7']}); it is not a status")
    elif ora['s7'] not in ((0, 0, 1), (2, 0, 1)) or (ora['s7'][0] == 2) != ora['rs']: bad.append(f"S7 {ora['s7_status']} is not the status convention (ok, or refused exactly when RS = 1)")
    if bad: return DISAGREEMENT, bad
    if ora['rs']:
        n = [f"first refusal: instruction {pred['first_refusal'][0]} ({pred['first_refusal'][1]}); {pred['refusals']} refused; {pred['arithmetic_after_first_refusal']} arithmetic operation(s) ran after it",
             f"sticky RS = 1, final R = {int(ora['r'])}, S7 = 2; final S0 is a stale or derived value and is NOT certified"]
        if _eq(ora['s0'], exact): n.append('S0 equals the exact value by coincidence; the candidate is still REFUSED')
        return REFUSED, n
    if not _eq(ora['s0'], exact): return DISAGREEMENT, ['no refusal, but S0 differs from the exact value']
    return COMMITTED, ['no arithmetic refusal; S0 equals the exact value on the oracle and the simulator']

def certify(alternatives, spu_vm, budget=10000):
    """alternatives: {name: spu_geom.Geometry}. spu_vm: path of a built C++ simulator (the simulator run is part of every certificate)."""
    exact = {n: g.prog.exact() for n, g in alternatives.items()}
    if len(set(exact.values())) > 1:
        return Report(False, 'equivalence error: the alternatives have different exact values for these inputs; nothing was compiled, executed or compared', exact, [])
    certs = []
    for name, g in alternatives.items():
        try: asm, img, words, ins, rout = B.compile_v03(g.prog)
        except B.CompileError as e: raise B.CompileError(f'{name}: {e}')
        try: pred = _predicted(B.predict(ins, rout))
        except KeyError: pred = None
        ro, rs_ = CLI.run_oracle(img, budget), CLI.run_sim(img, budget, spu_vm); ora, sim = _obs(REC.decode(ro)), _obs(REC.decode(rs_))
        outcome, notes = classify(pred, ora, sim, exact[name], ro == rs_)
        certs.append(Certificate(name, outcome, len(words), asm, pred, ora, sim, exact[name], notes))
    return Report(True, None, exact, certs)

def format_report(rep):
    if not rep.equivalent: return f'{rep.error}\n' + '\n'.join(f'  {n}: {v}' for n, v in rep.exact.items())
    ex = next(iter(rep.exact.values())); out = [f'exact value (all alternatives, for these inputs): {ex[0]} + {ex[1]}*sqrt3', f'{"alternative":28s} {"outcome":13s} {"words":>5s}  {"S7 status":14s} S0 (oracle)']
    for c in rep.certificates: out.append(f'{c.name:28s} {c.outcome:13s} {c.words:5d}  {c.oracle["s7_status"]:14s} {c.oracle["s0"] if c.oracle["s0_initialized"] else "uninitialized"}')
    for c in rep.certificates: out += [f'  [{c.name}] {n}' for n in c.notes]
    return '\n'.join(out + ['A certificate concerns these inputs and these images only; it is not a proof of general equivalence.'])
