"""Freeze and measure bounded end-to-end arithmetic strategy paths."""
import hashlib,json,sys,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software.experiments import surd_register_e2e as e2e

S0=ROOT/'build/spu_surd_register/s0_20261007_attempt04'
INPUT=ROOT/'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json'
SOURCES=('software/experiments/surd_register_e2e.py',
 'software/experiments/surd_register_e2e_run.py',
 'software/experiments/run_surd_register_e2e_recorded.sh',
 'spu_strategy/contract_surd_register_e2e_cost_2026-10-07.md',
 'build/spu_surd_register/s0_20261007_attempt04/plan.json',
 'build/spu_surd_register/s0_20261007_attempt04/run_01/results.json',
 'build/spu_surd_register/strategy_compare_20261007/plan_05/plan.json',
 'build/spu_surd_register/strategy_compare_20261007/run_05/results.json',
 'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze(directory):
    out=ROOT/directory
    if out.exists(): raise FileExistsError(out)
    baseline=json.loads((S0/'plan.json').read_text())
    for name,want in baseline['source_hashes'].items():
        if sha(ROOT/name)!=want: raise ValueError('accepted S0 source drift: '+name)
    out.mkdir(parents=True)
    inputs={str(w):{name:[list(r.__dict__.values()) for r in pair]
       for name,pair in e2e.cases(w).items()} for w in (16,32,64)}
    p={'format':'SPU_SURD_E2E_COST_V1','base_s0_plan':str((S0/'plan.json').relative_to(ROOT)),
       's0_inputs':str(INPUT.relative_to(ROOT)),'sources':{n:sha(ROOT/n) for n in SOURCES},
       'baseline_source_hashes':baseline['source_hashes'],'cases':inputs,
       'strategies':list(e2e.STRATEGIES),'trials':5,'repetitions_per_trial':2000,
       'warmup_chains':100,'max_attempts':1,'per_attempt_timeout_seconds':60,
       'cumulative_timeout_seconds':60,'timing_clock':'perf_counter_ns',
       'timing_scope':'two-MUL chain on prepared R inputs including policy checks, normalization and fallback path',
       'hardware_operations':0,'device_equivalence_tested':False}
    p['plan_sha256']=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (out/'plan.json').write_text(json.dumps(p,indent=2)+'\n'); print('FROZEN',out/'plan.json',p['plan_sha256'])

def run(plan_path,out_path):
    plan=json.loads(plan_path.read_text()); digest=plan.pop('plan_sha256')
    if hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=digest:
        raise ValueError('plan hash mismatch')
    for n,want in plan['sources'].items():
        if sha(ROOT/n)!=want: raise ValueError('source drift: '+n)
    for n,want in plan['baseline_source_hashes'].items():
        if sha(ROOT/n)!=want: raise ValueError('accepted S0 source drift: '+n)
    out=ROOT/out_path
    if out.exists():
        if not out.is_dir() or {p.name for p in out.iterdir()}!={'stdout.log','stderr.log'}: raise FileExistsError(out)
    else: out.mkdir(parents=True)
    results=[]
    for ws,cases in plan['cases'].items():
        w=int(ws)
        for name,pair in cases.items():
            x,y=(e2e.ex.R(*r) for r in pair)
            for strategy in plan['strategies']:
                results.append(e2e.measure_case(w,name,x,y,strategy,plan['trials'],
                                  plan['repetitions_per_trial'],plan['warmup_chains']))
    status='PASS' if all(x['exact'] for x in results) else 'FAIL'
    report={'format':'SPU_SURD_E2E_COST_RESULTS_V1','status':status,'plan_sha256':digest,
       'results':results,'timings':'HOST_SOFTWARE_ONLY','hardware_operations':0,
       'device_equivalence_tested':False,'python_object_memory':'NOT_MEASURED'}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'report.md').write_text(render(report))
    print(status,out/'results.json')
    if status!='PASS': raise SystemExit(1)

def render(report):
    lines=['# Surd end-to-end strategy costs','',
      'Host software timings over prepared exact-register inputs. Each case runs two sequential MULs. Inputs, policy checks, normalization and fallback handling are timed. Timing values are not hardware estimates.','',
      '| Width | Case | Strategy | Median ns/chain | Median ns/MUL | Peak result/intermediate bits | Narrow failures | Normalizer calls | Rescues | Wide fallbacks | Re-entry / nonresident | Cross GCD calls |','|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    for r in report['results']:
        c=r['counts_per_chain']; lines.append(f"| {r['width']} | {r['case']} | {r['strategy']} | {r['median_ns_per_chain']:.1f} | {r['median_ns_per_multiply']:.1f} | {c['peak_raw_result_bits']} / {c['peak_raw_intermediate_bits']} | {c['narrow_failures']} | {c['normalizer_calls']} | {c['normalization_rescues']} | {c['wide_fallbacks']} | {c['wide_reentries']} / {c['nonresident_wide_results']} | {c['cross_cancel_gcd_calls']} |")
    lines+=['','All rows passed exact Fraction-pair checks before timing. Five trials, 2,000 chains per trial, and 100 untimed warmups were used. Raw per-trial nanoseconds and detailed operation counts are in `results.json`.','',
      'These timings include Python dispatch and arbitrary-precision integer behavior. They compare these implementations on this host and do not predict RTL latency, throughput, area, energy, or a variable-width pipeline.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--freeze': freeze(sys.argv[2])
    elif len(sys.argv)==4 and sys.argv[1]=='--run': run(ROOT/sys.argv[2],sys.argv[3])
    else: raise SystemExit('usage: --freeze BUILD_DIR | --run PLAN_JSON NEW_OUTPUT_DIR')
