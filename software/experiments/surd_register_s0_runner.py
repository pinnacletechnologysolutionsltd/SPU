"""S0 retained-corpus correctness/accounting runner; never times operations."""
import hashlib,json,math,platform,sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software.lib import rational_robotics as ref
from software.lib import rational_robotics_unshared as fused
from software.experiments import surd_register_exact as ex
from software.experiments import surd_register_model as model
from software.experiments.surd_register_candidates import FixedScale,SharedBlock
from software.experiments.surd_register_workload import (from_q3,oracle_chain,
    oracle_quadray,bounded_chain,bounded_quadray)
from software.experiments.surd_register_s0_report import render

CORPUS=ROOT/'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json'
PRIOR=ROOT/'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/results.json'
OUT=ROOT/'build/spu_surd_register/s0_20261006'
PLAN=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else OUT/'plan.json'
OUT=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else OUT

def q(values): return ref.Q3(Fraction(values[0],values[1]),Fraction(values[2],values[3]))
def decode(row,catalog,names):
    v=ref.QuadrayQ(*(q(x) for x in row['vector']))
    js=tuple(ref.CirculantJoint(3,*(q(x) for x in catalog[n])) for n in names)
    return v,js


def add_counts(dst,src):
    for k,v in src.items():
        if isinstance(v,int): dst[k]=dst.get(k,0)+v
        elif isinstance(v,dict):
            node=dst.setdefault(k,{})
            for a,b in v.items(): node[a]=node.get(a,0)+b


def merge_trace(dst,trace):
    add_counts(dst['counts'],{k:v for k,v in trace['counts'].items() if k!='product_operand_widths'})
    for pair in trace['counts']['product_operand_widths']:
        key=f'{pair[0]}x{pair[1]}'; dst['product_width_histogram'][key]=dst['product_width_histogram'].get(key,0)+1
    for k,v in trace['named_intermediates'].items(): dst['max_named_intermediate_bits'][k]=max(dst['max_named_intermediate_bits'].get(k,0),v)


def retained(data):
    results={}; comparisons={'reference_fused':0,'independent_oracle':0,'bounded_candidates':0,'mismatches':[]}
    for label,names in data['chains'].items():
        cases=[]; policy_stats={f'{w}_{p}':{'fallbacks':0,'reentries':0,'nonresident_results':0,'wide_continuations':0,'operations':0,
            'status_counts':{},'counts':{},'product_width_histogram':{},'max_named_intermediate_bits':{}}
            for w in (16,32,64) for p in model.POLICIES}
        for row in data['records']:
            v,js=decode(row,data['catalog'],names)
            forward=ref.fk_chain(v,js); expected=(forward,ref.inverse_fk_chain(forward,js))
            got=fused.apply_joint_chain(v,js); comparisons['reference_fused']+=1
            if got!=expected: comparisons['mismatches'].append([row['name'],label,'fused'])
            opair=oracle_chain(v,js); oracle=(oracle_quadray(opair[0],ref),oracle_quadray(opair[1],ref))
            comparisons['independent_oracle']+=1
            if expected!=oracle: comparisons['mismatches'].append([row['name'],label,'oracle'])
            for w in (16,32,64):
                for p in model.POLICIES:
                    out,stats=bounded_chain(v,js,w,p)
                    pair=(bounded_quadray(out[0],ref),bounded_quadray(out[1],ref)); comparisons['bounded_candidates']+=1
                    key=f'{w}_{p}'; dst=policy_stats[key]
                    if pair!=expected: comparisons['mismatches'].append([row['name'],label,key])
                    dst['fallbacks']+=stats['fallbacks']; dst['reentries']+=stats['reentries']; dst['operations']+=stats['operations']
                    dst['nonresident_results']+=stats['nonresident_results']; dst['wide_continuations']+=stats['wide_continuations']
                    add_counts(dst['status_counts'],stats['status_counts']); merge_trace(dst,stats['trace'])
            cases.append({'source':row['source'],'fixture_index':row.get('fixture_index'),'name':row['name']})
        results[label]={'joint_count':len(names),'distinct_retained_inputs':len(cases),'inputs':cases,
            'policy_accounting':policy_stats,'wide_fused_kernel_timing':'NOT_MEASURED'}
    return results,comparisons


def scale_candidates(data,scale):
    fixed=FixedScale(scale); fstats={'scale':scale,'logical_bits_per_register':128,'loads_ok':0,'loads_rejected':0,'mul_ok':0,'mul_rejected':0,'mul_rejected_reasons':{},'mismatches':0}
    shared={'vector_block_bits':9*64,'joint_block_bits':7*64,'load_blocks':0,'mul_blocks':0,'alignment_multiplications':0,'block_scale_updates':0,'fallbacks':0,'mismatches':0}
    for row in data['records']:
        v=ref.QuadrayQ(*(q(x) for x in row['vector'])); vals=tuple(from_q3(x) for x in v.components())
        block=SharedBlock.load(vals); shared['load_blocks']+=1
        shared['alignment_multiplications']+=block.counts['scale_alignment_multiplications']; shared['fallbacks']+=block.counts['fallbacks']
        if block.materialize()!=tuple(ex.normalize(r) for r in vals): shared['mismatches']+=1
        js=data['catalog']['thirds_period6']; joint=tuple(from_q3(q(x)) for x in js)
        jb=SharedBlock.load(joint); shared['load_blocks']+=1
        shared['alignment_multiplications']+=jb.counts['scale_alignment_multiplications']; shared['fallbacks']+=jb.counts['fallbacks']
        if jb.materialize()!=tuple(ex.normalize(r) for r in joint): shared['mismatches']+=1
        fixed_loaded=[]
        for r in (*vals,*joint):
            loaded=fixed.load(r)
            fixed_loaded.append(loaded)
            if loaded['status']=='OK': fstats['loads_ok']+=1
            else: fstats['loads_rejected']+=1
        if fixed_loaded[0]['status']==fixed_loaded[1]['status']=='OK':
            out=fixed.apply('MUL',fixed_loaded[0]['value'],fixed_loaded[1]['value']); fstats['mul_ok' if out['status']=='OK' else 'mul_rejected']+=1
            if out['status']=='OK':
                got=ex.R(out['value'][0],out['value'][1],scale); exact,_=ex.raw('MUL',vals[0],vals[1])
                if ex.normalize(got)!=ex.normalize(exact): fstats['mismatches']+=1
            else:
                reason=out['reason']; fstats['mul_rejected_reasons'][reason]=fstats['mul_rejected_reasons'].get(reason,0)+1
        else:
            fstats['mul_rejected']+=1
            fstats['mul_rejected_reasons']['INPUT_NOT_ON_SCALE']=fstats['mul_rejected_reasons'].get('INPUT_NOT_ON_SCALE',0)+1
        sb=SharedBlock.load((vals[0],vals[1])); sb.apply_pairs('MUL',((0,1),)); shared['mul_blocks']+=1
        shared['alignment_multiplications']+=sb.counts['scale_alignment_multiplications']; shared['block_scale_updates']+=sb.counts['block_scale_updates']
        shared['fallbacks']+=sb.counts['fallbacks']
        exact,_=ex.raw('MUL',vals[0],vals[1])
        if sb.materialize()!=(ex.normalize(exact),): shared['mismatches']+=1
    return {'fixed_scale':fstats,'shared_scale':shared}


def main():
    plan=json.loads(PLAN.read_text()); frozen_hash=plan.pop('plan_sha256')
    actual_hash=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if actual_hash!=frozen_hash: raise ValueError('plan hash mismatch')
    plan['plan_sha256']=frozen_hash
    for name,digest in plan['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest: raise ValueError('source drift: '+name)
    if (OUT/'results.json').exists() or (OUT/'report.md').exists(): raise FileExistsError('S0 result exists')
    raw=CORPUS.read_bytes(); data=json.loads(raw)
    if hashlib.sha256(raw).hexdigest()!=plan['inputs_sha256']: raise ValueError('retained input hash mismatch')
    den=[z[k] for row in data['records'] for z in row['vector'] for k in (1,3)]
    den += [z[k] for joint in data['catalog'].values() for z in joint for k in (1,3)]
    scale=1
    for d in den: scale=math.lcm(scale,d)
    chains,checks=retained(data); scales=scale_candidates(data,scale)
    status='PASS_RETAINED' if not checks['mismatches'] and not scales['shared_scale']['mismatches'] and not scales['fixed_scale']['mismatches'] else 'FAIL'
    report={'format':'SPU_SURD_REGISTER_S0_RESULTS_V1','retained_correctness_status':status,
        'cohorts':{'retained_vector_rational_joint':{'count':32,'joint_coefficients':'all b=0',
          'inputs_sha256':hashlib.sha256(raw).hexdigest(),'chains':chains,'correctness':checks},
          'synthetic_nonzero_surd':{'separate_test':'software/tests/test_surd_register_s0.py',
             'fixtures':'nonzero-b operands, cancellation, unequal scales, range witnesses, invalid loads and rotation cases',
             'final_terminal_status':'NOT_VERIFIED_AFTER_REPAIR_BUDGET_EXHAUSTED'}},
        'scale_candidates':scales,'prior_chain_result_sha256':hashlib.sha256(PRIOR.read_bytes()).hexdigest(),
        'head':plan['head'],'dirty_worktree_at_freeze':plan['dirty'],
        'dirty_status_sha256':plan['dirty_status_sha256'],'source_hashes':plan['source_hashes'],
        'plan_sha256':plan['plan_sha256'],'failure_source_hashes':plan['failure_source_hashes'],
        'policy_boundaries':'EAGER normalizes each core result; FIT_RESCUE normalizes only after raw destination miss; BOUNDARY explicitly normalizes after each joint stage in forward and recovery chains',
        'lane_widths_bits':[16,32,64],'parameterized_full_range_intermediate_limits':{str(w):{op:ex.intermediate_limits(op,w) for op in ('ADD','SUB','MUL','NEG','CONJ','EQ','NORM')} for w in (16,32,64)},
        'logical_storage_and_schedule_bytes':{'explicit_register_bits':192,'explicit_register_bytes':24,
          'fixed_register_bits':128,'fixed_implicit_scale_bytes':8,'shared_vector4_block_bits':576,
          'shared_joint3_block_bits':448,'bytes_per_chain_length_n':{'explicit_load':'96+72*n','fixed_load':'64+48*n',
          'shared_load':'72+56*n','explicit_output_store':192,'fixed_output_store':128,'shared_output_store':144}},
        'prior_35_bit_peak_is_observation_only':True,'trials':0,'timing':'NOT_RUN_BY_S0',
        'modelled_counts_are_cycles':'NO','python_object_memory':'NOT_MEASURED',
        'python':sys.version,'platform':platform.platform(),'hardware_operations':0,'device_equivalence_tested':False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'report.md').write_text(render(OUT,PLAN))
    print(status,OUT/'results.json',flush=True)


if __name__=='__main__': main()
