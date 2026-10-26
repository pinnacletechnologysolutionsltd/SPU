"""Compare run dirs. compare.py exact RUN_DIR   -> run vs retained original native.json/routed.json/fasm.
   compare.py calls FD_SHADOW_DIR REOPEN_DIR     -> per-call search work and first divergence."""
import hashlib, json, sys
from pathlib import Path

ORIG = Path('/home/user/Projects/hardware/SPU/build/spu_surd_register/backend_compatibility_20261012/'
            'openxc7_serial_route_campaign_repair03_20261017/campaign_01/fixture')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def graph(p):
    d = json.loads(Path(p).read_text())
    return {n['name']: [(tuple(r['wire']['id']), tuple(r.get('pip_id') or ()), r['wire'].get('owner')) for r in n['resources']]
            for n in d['nets']}

def exact(run):
    run = Path(run)
    g0, g1 = graph(ORIG / 'native.json'), graph(run / 'native.json')
    diff = [n for n in g0 if g0[n] != g1.get(n)]
    res = dict(nets=len(g0), nets_differing=len(diff), first=diff[:5],
               routed_json_equal=sha(ORIG / 'routed.json') == sha(run / 'routed.json'),
               fasm_equal=sha(ORIG / 'fixture.fasm') == sha(run / 'fixture.fasm'),
               native_json_equal=sha(ORIG / 'native.json') == sha(run / 'native.json'))
    print(json.dumps(res, indent=1))
    return not diff and res['routed_json_equal'] and res['fasm_equal']

def calls(run):
    rows = [json.loads(l) for l in (Path(run) / 'alg3.jsonl').read_text().splitlines()]
    return rows[0], rows[1:]

def cmp_calls(a, b):
    ha, ca = calls(a); hb, cb = calls(b)
    key = lambda c: (c['net'], c['arc'], c['bb'])
    first = next((i for i, (x, y) in enumerate(zip(ca, cb)) if key(x) != key(y) or x['final_cost'] != y['final_cost']), None)
    def tot(cs, f): return sum(c[f] for c in cs)
    for name, cs in (('fd_shadow', ca), ('reopen', cb)):
        print(name, dict(calls=len(cs), pops=tot(cs, 'pops'), pushes=tot(cs, 'pushes'), revisits=tot(cs, 'revisits'),
                         stale=tot(cs, 'stale'), shadow_missed=tot(cs, 'shadow_missed'), cost=tot(cs, 'final_cost'),
                         unrouted=sum(c['result'] != 0 for c in cs), stop_rule=tot(cs, 'stop_rule')))
    print('first divergent call index (state identical before it):', first)
    if first is not None:  # only calls before divergence are a like-for-like comparison
        ca, cb = ca[:first], cb[:first]
    print('like-for-like prefix', len(ca), 'calls: cost fd', tot(ca, 'final_cost'), 'reopen', tot(cb, 'final_cost'),
          'pops fd', tot(ca, 'pops'), 'reopen', tot(cb, 'pops'))
    worse = [(x['net'], x['arc'], x['final_cost'], y['final_cost']) for x, y in zip(ca, cb) if y['final_cost'] > x['final_cost']]
    print('prefix calls where reopen cost > fd cost:', len(worse), worse[:3])

if __name__ == '__main__':
    if sys.argv[1] == 'exact':
        sys.exit(0 if exact(sys.argv[2]) else 1)
    cmp_calls(sys.argv[2], sys.argv[3])
