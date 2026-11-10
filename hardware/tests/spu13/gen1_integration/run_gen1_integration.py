"""GEN1-ISA-COVERAGE-2 runner: one compile, 7 case runs + 6 no-override mutant runs, judged against the frozen oracle.
usage: run_gen1_integration.py OUT_DIR EXPECTED_JSON EXPECTED_SHA256
Exit 0 only if every case passes and every negative control is detected. No retry, no repair."""
import sys, os, re, json, hashlib, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT, EXP = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
os.chdir(ROOT)
import parse_record as PR
EXP_SHA = sys.argv[3]
BENCH = Path(__file__).with_name('gen1_integration_sim.v')
FILELIST = ROOT / 'hardware/boards/artix7/wukong_v3/cpu_v02/filelists/candidate_portable.f'
GOLDEN_SRC = HERE / 'fixtures/source_hashes.sha256'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Every simulator output line must be exactly one of these records (whitespace-tolerant), or the $finish line.
LINE_RE = {
    'OVR': r'^OVR\s+(\d+)\s+([0-9a-f]{16})\s+(OK|MISMATCH)$', 'PRECOND': r'^PRECOND\s+OK\s+(\d+)$',
    'ISSUE': r'^ISSUE\s+(\d+)\s+([0-9a-f]{16})$', 'RETIRE': r'^RETIRE\s+(\d+)\s+(\d+)$',
    'FAULT_ENTER': r'^FAULT_ENTER\s+(\d+)\s+(\d+)$', 'RX': r'^RX\s+([0-9a-f]{2})$',
    'FRAME_ERROR': r'^FRAME_ERROR\s+at\s+\d+$',
    'FINAL': r'^FINAL\s+state=(\d+)\s+pc=(\d+)\s+halted=([01])\s+fault=([01])\s+valid=([0-9a-f]{2})$',
    'END': r'^END\s+bytes=(\d+)$', 'FAIL': r'^FAIL\b.*$'}
FINISH_RE = r'^\S+:\d+: \$finish called at \d+ \(1ps\)$'
# Override index sets of the frozen bench (plan section 2); checked against the oracle ROM images at start-up.
OVR_SET = {'G': [0, 2, 4], 'N1': [2, 3], 'N2': [0, 1, 2, 3, 4, 5], 'O': [0, 1, 2, 3, 4, 5], 'I': [4, 5], 'M1': [1], 'M2': [7]}

def parse(log):
    o = {k: [] for k in LINE_RE}; o.update(malformed=[], unparsed=[], finish=0)
    for line in log.splitlines():
        line = line.strip()
        if not line: continue
        key = line.split()[0]
        if key in LINE_RE:
            m = re.match(LINE_RE[key], line)
            if m: o[key].append(m.groups())
            else: o['malformed'].append(line)
        elif re.match(FINISH_RE, line): o['finish'] += 1
        else: o['unparsed'].append(line)
    o['fail'] = [line for line in log.splitlines() if line.strip().startswith('FAIL')]
    o['frame_errors'] = len(o['FRAME_ERROR'])
    o['ovr'] = [(int(k), w, v) for k, w, v in o['OVR']]
    o['issue'] = [(int(p), w) for p, w in o['ISSUE']]
    o['retire'] = [(int(p), int(st)) for p, st in o['RETIRE']]
    o['fault_enter'] = [(int(f), int(p)) for f, p in o['FAULT_ENTER']]
    o['final'] = tuple(int(x, 16) if i == 4 else int(x) for i, x in enumerate(o['FINAL'][0])) if len(o['FINAL']) == 1 else None
    o['rx'] = bytes(int(b, 16) for (b,) in o['RX'])
    o['end'] = len(o['END']) == 1 and int(o['END'][0][0]) == len(o['RX'])
    return o

def judge_frame(o, e):
    f = []
    recs, bad, covered = PR.scan(o['rx'])
    if o['frame_errors']: f.append('uart framing error')
    if len(recs) != 1: f.append('valid records=%d' % len(recs))
    if bad: f.append('bad headers %s' % bad)
    if sum(1 for c in covered if not c): f.append('unexpected bytes=%d' % sum(1 for c in covered if not c))
    if o['rx'] != bytes.fromhex(e['frame']): f.append('frame != expected')
    return f

def judge(o, e):
    f = list(o['fail']) + ['malformed: %s' % x for x in o['malformed']] + ['unparsed: %s' % x for x in o['unparsed']]
    n_ret = len(e['retires'])
    counts = {'OVR': len(OVR_SET[e['name']]), 'PRECOND': 1, 'ISSUE': n_ret, 'RETIRE': n_ret,
              'FAULT_ENTER': 1 if e['fault'] else 0, 'RX': len(bytes.fromhex(e['frame'])), 'FINAL': 1, 'END': 1, 'FRAME_ERROR': 0}
    for k, n in counts.items():
        if len(o[k]) != n: f.append('count %s=%d expected %d' % (k, len(o[k]), n))
    if o['finish'] != 1: f.append('finish lines=%d' % o['finish'])
    if not o['end']: f.append('END missing or byte count mismatch')
    if sorted(k for k, _, _ in o['ovr']) != OVR_SET[e['name']]: f.append('override indices %s' % [k for k, _, _ in o['ovr']])
    for k, w, v in o['ovr']:
        if v != 'OK' or w != e['rom'][k]: f.append('override %d readback %s %s' % (k, w, v))
    want_issue = [(p, e['rom'][p]) for p, _ in e['retires']]
    if o['issue'] != want_issue: f.append('issue sequence %s' % o['issue'][-2:])
    if o['retire'] != [tuple(r) for r in e['retires']]: f.append('retire sequence %s' % o['retire'][-2:])
    if e['fault']:
        allowed = (2,) if e['cause'] == 'fetch_reject' else (3, 4)
        if len(o['fault_enter']) != 1 or o['fault_enter'][0][0] not in allowed or o['fault_enter'][0][1] != e['pc']:
            f.append('fault entry %s' % o['fault_enter'])
        want_final = (7, e['pc'], 0, 1, e['mask'])
    else:
        want_final = (6, 14, 1, 0, e['mask'])
    if o['final'] != want_final: f.append('final %s != %s' % (o['final'], want_final))
    return f + judge_frame(o, e)

def main():
    OUT.mkdir(parents=True)
    res = {'expected_sha256': sha(EXP), 'bench_sha256': sha(BENCH), 'runner_sha256': sha(__file__),
           'filelist_sha256': sha(FILELIST)}
    if res['expected_sha256'] != EXP_SHA: return finish(res, 'UNKNOWN', 'expected-record hash mismatch')
    gs = subprocess.run(['sha256sum', '-c', str(GOLDEN_SRC)], capture_output=True, text=True)
    res['golden_sources_ok'] = gs.returncode == 0 and gs.stdout.count(': OK') == 17
    if not res['golden_sources_ok']: return finish(res, 'UNKNOWN', 'shared RTL differs from golden Phase S sources')
    exp = json.loads(EXP.read_text())
    g = [int(w, 16) for w in exp['0']['rom']]
    for e in exp.values():   # bench override sets must cover every word where the oracle ROM differs from golden
        if not {i for i, w in enumerate(e['rom']) if int(w, 16) != g[i]} <= set(OVR_SET[e['name']]):
            return finish(res, 'UNKNOWN', 'override set does not cover oracle ROM for %s' % e['name'])
    files = [l.split()[1] for l in FILELIST.read_text().splitlines() if l.startswith('sv ')]
    cmd = ['iverilog', '-g2012', '-Ihardware/rtl/arch', '-Ihardware/rtl/core/spu13', '-o', str(OUT / 'sim.vvp'), str(BENCH)] + files
    res['compile_command'] = cmd
    c = subprocess.run(cmd, capture_output=True, text=True); (OUT / 'compile.log').write_text(c.stdout + c.stderr)
    if c.returncode: return finish(res, 'FAILED', 'compile rc=%d' % c.returncode)
    outs, res['cases'] = {}, {}
    def run(cid, extra, tag):
        r = subprocess.run(['vvp', '-n', str(OUT / 'sim.vvp'), '+CASE=%s' % cid] + extra, capture_output=True, text=True, timeout=900)
        (OUT / ('%s.log' % tag)).write_text(r.stdout + r.stderr); return parse(r.stdout)
    for cid, e in exp.items():
        o = outs[cid] = run(cid, [], 'case_%s_%s' % (cid, e['name']))
        fl = judge(o, e)
        res['cases'][e['name']] = {'pass': not fl, 'failures': fl, 'rx_hex': o['rx'].hex(), 'retire_tail': o['retire'][-2:],
                                   'fault_enter': o['fault_enter'], 'final': o['final']}
    nc = {}
    nc['NC1_corrupted_expected_byte'] = {e['name']: bool(judge(outs[cid], dict(e, frame=(lambda b: (b[:5 + int(cid)] + bytes([b[5 + int(cid)] ^ 0x01]) + b[6 + int(cid):]).hex())(bytes.fromhex(e['frame'])))))
                                         for cid, e in exp.items()}
    nc['NC2_cross_case_expectation'] = {'%s_vs_%s' % (exp[i]['name'], exp[j]['name']): bool(judge(outs[i], exp[j]))
                                        for i in exp for j in exp if i != j}
    nc3 = {}
    for cid, e in exp.items():
        if e['name'] == 'G': continue
        o = run(cid, ['+NO_OVERRIDE'], 'mutant_no_override_%s_%s' % (cid, e['name']))
        nc3[e['name']] = {'full_judge_detects': bool(judge(o, e)), 'frame_only_detects': bool(judge_frame(o, e))}
    nc['NC3_no_override_mutant'] = nc3
    g = exp['0']; nc['NC4_G_equals_frozen_3_40'] = bytes.fromhex(g['frame']) == PR.EXPECTED and outs['0']['rx'] == PR.EXPECTED
    res['negative_controls'] = nc
    detected = (all(nc['NC1_corrupted_expected_byte'].values()) and all(nc['NC2_cross_case_expectation'].values())
                and all(v['full_judge_detects'] and v['frame_only_detects'] for v in nc3.values()) and nc['NC4_G_equals_frozen_3_40'])
    allpass = all(v['pass'] for v in res['cases'].values())
    return finish(res, 'PASS' if allpass and detected else 'FAILED',
                  'cases %d/7 pass; negative controls %s' % (sum(v['pass'] for v in res['cases'].values()), 'all detected' if detected else 'NOT all detected'))

def finish(res, verdict, why):
    res['verdict'], res['reason'] = verdict, why
    (OUT / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(verdict, '-', why); return 0 if verdict == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main())
