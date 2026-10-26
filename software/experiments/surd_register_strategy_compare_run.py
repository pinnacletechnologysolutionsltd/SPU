"""Freeze once or run the bounded S0 strategy comparison."""
import hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software.experiments import surd_register_strategy_compare as cmp

BASE=ROOT/'build/spu_surd_register/s0_20261007_attempt04'
INPUT=ROOT/'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json'
SOURCES=('software/experiments/surd_register_strategy_compare.py',
         'software/experiments/surd_register_strategy_compare_run.py',
         'software/experiments/run_surd_register_strategy_compare_recorded.sh',
         'spu_strategy/contract_surd_register_strategy_compare_2026-10-07.md',
         'build/spu_surd_register/s0_20261007_attempt04/plan.json',
         'build/spu_surd_register/s0_20261007_attempt04/run_01/results.json',
         'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json')
VARIANTS=('explicit_denominator_fit_rescue','cross_cancel','adaptive','combined')

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze(directory):
    out=ROOT/directory
    if out.exists(): raise FileExistsError(out)
    baseline=json.loads((BASE/'plan.json').read_text())
    for name,want in baseline['source_hashes'].items():
        if digest(ROOT/name)!=want: raise ValueError('accepted S0 source drift: '+name)
    out.mkdir(parents=True)
    plan={'format':'SPU_SURD_STRATEGY_COMPARE_V1','base_s0_plan':str((BASE/'plan.json').relative_to(ROOT)),
          'input':str(INPUT.relative_to(ROOT)),'sources':{name:digest(ROOT/name) for name in SOURCES},
          'baseline_source_hashes':baseline['source_hashes'],
          'variants':list(VARIANTS),'lane_widths':[16,32,64],'base_policy':'FIT_RESCUE',
          'adaptive_trigger':'normalize raw result when maximum signed/unsigned result width >= W-1 and <= W; zero remains canonical',
          'retained_cohort':'all 32 S0 inputs at chain lengths 1,3,6,12; catalog joints have b=0',
          'synthetic_cohort':'four explicit denominator pairs; ADD and MUL; widths 16,32,64',
          'max_attempts':1,'per_attempt_timeout_seconds':60,'cumulative_timeout_seconds':60,
          'timings':'NOT_MEASURED','hardware_operations':0,'device_equivalence_tested':False}
    body=json.dumps(plan,sort_keys=True,separators=(',',':')).encode()
    plan['plan_sha256']=hashlib.sha256(body).hexdigest()
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print('FROZEN',out/'plan.json',plan['plan_sha256'])

def execute(plan_path,out_path):
    plan=json.loads(plan_path.read_text()); recorded=plan.pop('plan_sha256')
    if hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=recorded:
        raise ValueError('plan hash mismatch')
    for name,want in plan['sources'].items():
        if digest(ROOT/name)!=want: raise ValueError('source drift: '+name)
    for name,want in plan['baseline_source_hashes'].items():
        if digest(ROOT/name)!=want: raise ValueError('accepted S0 source drift: '+name)
    out=ROOT/out_path
    if out.exists():
        if not out.is_dir() or {p.name for p in out.iterdir()}!={'stdout.log','stderr.log'}:
            raise FileExistsError(out)
    else: out.mkdir(parents=True)
    data=json.loads(INPUT.read_text())
    runs={name:cmp.run_variant(data,variant) for name,variant in zip(VARIANTS,('explicit','cross_cancel','adaptive','combined'))}
    synthetic={name:cmp.synthetic(variant) for name,variant in zip(VARIANTS,('explicit','cross_cancel','adaptive','combined'))}
    boundary={name:cmp.boundary(variant) for name,variant in zip(VARIANTS,('explicit','cross_cancel','adaptive','combined'))}
    baseline=runs[VARIANTS[0]]
    exact={name:(run['correctness']['mismatches']==[] and run['correctness']==baseline['correctness'])
           for name,run in runs.items()}
    exact.update({'synthetic_'+name:row['correct'] for name,row in synthetic.items()})
    exact.update({'boundary_'+name:row['exact'] for name,row in boundary.items()})
    result={'format':'SPU_SURD_STRATEGY_COMPARE_RESULTS_V1','plan_sha256':recorded,
            'retained_rational_joint':{'count':32,'chains':[1,3,6,12],'exact_agreement':exact,
                'variants':runs},'synthetic_surd':{'case_count':4,'operations':['ADD','MUL'],
                'widths':[16,32,64],'variants':synthetic},
            'boundary_cohort':{'cases':['cancelable','coprime_control'],
                'operations_per_case':'two sequential MUL operations per width',
                'widths':[16,32,64],'variants':boundary},'timings':'NOT_MEASURED',
            'hardware_operations':0,'device_equivalence_tested':False}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'report.md').write_text(render(result))
    print('PASS' if all(exact.values()) else 'FAIL',out/'results.json')
    if not all(exact.values()): raise SystemExit(1)

def render(data):
    lines=['# Surd strategy comparison','',
      'Reference: accepted explicit-denominator S0 with FIT_RESCUE. Identical retained inputs and W=16,32,64 lane budgets were used.','',
      '## Retained rational-joint cohort','',
      '| Variant | Exact agreement | Fallbacks | GCD calls | GCD steps | Exact divisions | Peak intermediate bits |','|---|---:|---:|---:|---:|---:|---:|']
    for name,run in data['retained_rational_joint']['variants'].items():
        stats=[p for c in run['chains'].values() for k,p in c['policy_accounting'].items()]
        fallbacks=sum(x['fallbacks'] for x in stats)
        gcds=sum(x['counts'].get('gcd_calls',0) for x in stats)+run['technique_cost']['cross_cancel_gcd_calls']
        gcd_steps=sum(x['counts'].get('gcd_steps',0) for x in stats)+run['technique_cost']['cross_cancel_gcd_steps']
        divs=sum(x['counts'].get('exact_quotients',0) for x in stats)+run['technique_cost']['cross_cancel_exact_divisions']
        peak=max((max(x['max_named_intermediate_bits'].values(),default=0) for x in stats),default=0)
        lines.append(f'| {name} | {data["retained_rational_joint"]["exact_agreement"][name]} | {fallbacks} | {gcds} | {gcd_steps} | {divs} | {peak} |')
    lines+=['','## Synthetic Surd operations','','| Variant | Cases | Exact cases | GCD calls | GCD steps | Exact divisions | Fallbacks | Peak intermediate bits |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,row in data['synthetic_surd']['variants'].items():
        cost=row['technique_cost']; traces=[x['trace']['counts'] for x in row['cases']]
        gcds=sum(x.get('gcd_calls',0) for x in traces)+cost['cross_cancel_gcd_calls']
        steps=sum(x.get('gcd_steps',0) for x in traces)+cost['cross_cancel_gcd_steps']
        divisions=sum(x.get('exact_quotients',0) for x in traces)+cost['cross_cancel_exact_divisions']
        peak=max((max(x['trace']['named_intermediates'].values(),default=0) for x in row['cases']),default=0)
        lines.append(f'| {name} | {len(row["cases"])} | {sum(x["exact_match"] for x in row["cases"])} | {gcds} | {steps} | {divisions} | 0 | {peak} |')
    lines+=['','## Retained execution status breakdown','','| Variant | Narrow OK | Narrow INVALID_INPUT | Narrow INTERMEDIATE_OVERFLOW | Narrow DESTINATION_OVERFLOW | Wide fallback continuations | Re-entries | Nonresident results |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,run in data['retained_rational_joint']['variants'].items():
        counts={}
        for by_op in run['narrow_execution_statuses'].values():
            for status,count in by_op.items(): counts[status]=counts.get(status,0)+count
        stats=[p for c in run['chains'].values() for k,p in c['policy_accounting'].items()]
        lines.append(f'| {name} | {counts.get("OK",0)} | {counts.get("INVALID_INPUT",0)} | {counts.get("INTERMEDIATE_OVERFLOW",0)} | {counts.get("DESTINATION_OVERFLOW",0)} | {sum(x["wide_continuations"] for x in stats)} | {sum(x["reentries"] for x in stats)} | {sum(x["nonresident_results"] for x in stats)} |')
    lines+=['','## Boundary-focused cohort','','| Variant | Narrow failures | Wide fallbacks | Wide re-entries | Nonresident | Cross-cancel GCD / steps / divisions | Adaptive normalizations | Wide normalization GCD / steps / divisions |','|---|---:|---:|---:|---:|---|---:|---|']
    for name,row in data['boundary_cohort']['variants'].items():
        c=row['cost']; lines.append(f'| {name} | {c["narrow_failures"]} | {c["wide_fallbacks"]} | {c["wide_reentries"]} | {c["nonresident_wide_results"]} | {c["cross_cancel_gcd_calls"]} / {c["cross_cancel_gcd_steps"]} / {c["cross_cancel_exact_divisions"]} | {c["adaptive_normalizations"]} | {c["wide_gcd_calls"]} / {c["wide_gcd_steps"]} / {c["wide_exact_divisions"]} |')
    lines+=['','Widths are observed maxima, not proofs. Fallback counts and modeled arithmetic work are software-model measures, not cycles or hardware costs. Python timings were not measured.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--freeze': freeze(sys.argv[2])
    elif len(sys.argv)==4 and sys.argv[1]=='--run': execute(ROOT/sys.argv[2],sys.argv[3])
    else: raise SystemExit('usage: --freeze BUILD_DIR | --run PLAN_JSON NEW_OUTPUT_DIR')
