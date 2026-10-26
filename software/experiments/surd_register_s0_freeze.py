"""Freeze S0 source identities and workload before its one corpus run."""
import hashlib,json,subprocess
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'build/spu_surd_register/s0_20261006')
FILES=('AGENTS.md','knowledge/isa_reference.md','docs/spu13_isa_spec.md',
 'software/lib/rational_robotics.py','software/lib/rational_robotics_unshared.py',
 'software/experiments/rational_robotics_isa_adapter.py',
 'software/experiments/surd_register_exact.py','software/experiments/surd_register_model.py',
 'software/experiments/surd_register_candidates.py','software/experiments/surd_register_rotation.py',
 'software/experiments/surd_register_workload.py','software/experiments/surd_register_s0_runner.py',
 'software/experiments/surd_register_s0_report.py','software/experiments/surd_register_s0_freeze.py',
 'software/experiments/run_surd_register_s0_recorded.sh',
 'software/experiments/run_surd_register_s0_focused_recorded.sh',
 'software/tests/test_surd_register_s0.py','spu_strategy/spec_spu_surd_register_s0_2026-10-06.md',
 'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json',
 'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/plan.json',
 'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/results.json')

# Hash the dirty-tree files directly: HEAD alone cannot identify this study's
# implementation, references, input corpus, or earlier chain terminal result.
# The status snapshot is retained beside the plan so reviewers can distinguish
# the source tree state from the commit identifier recorded at preflight.


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan_path=OUT/'plan.json'
    if OUT.exists(): raise SystemExit('refuse frozen output directory overwrite')
    OUT.mkdir(parents=True)
    status=subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,check=True).stdout
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    (OUT/'git_status_start.txt').write_bytes(status)
    plan={'format':'SPU_SURD_REGISTER_S0_PLAN_V1','head':head,'dirty':bool(status),
        'dirty_status_sha256':hashlib.sha256(status).hexdigest(),
        'source_hashes':{name:sha(ROOT/name) for name in FILES},
        'inputs_sha256':sha(ROOT/'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json'),
        'prior_chain_results_sha256':sha(ROOT/'build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/results.json'),
        'chain_lengths':[1,3,6,12],'retained_vector_count':32,'lanes_bits':[16,32,64],
        'policies':['EAGER','FIT_RESCUE','BOUNDARY'],'shared_blocks':{'vector_N':4,'joint_N':3},
        'fixed_scale':'LCM of all frozen retained coefficient denominators; computed by runner',
        'synthetic_seed':60061006,'timings':0,'hardware_operations':0,'device_equivalence_tested':False,
        'focused_timeout_seconds':60,'focused_test_attempts_before_amendment':3,
        'focused_test_repair_cycles_before_amendment':2,
        'focused_test_attempts_this_amendment':1,
        'corpus_attempts_this_amendment':1,
        'corpus_timeout_seconds':60,
        'campaign_max_attempts_this_amendment':2,
        'campaign_cumulative_timeout_seconds':120,
        'focused_test_terminal_before_amendment':'FAILED; corrected sources require this bounded rerun',
        'failure_source_hashes':'NOT_CAPTURED_AT_EACH_ATTEMPT; exact prior dirty untracked contents cannot be reconstructed',
        'terminal_recording':'run_surd_register_s0_recorded.sh captures the bounded runner exit status; TERM is sent at 60 seconds and KILL after a 5-second grace period',
        'command':['software/experiments/run_surd_register_s0_recorded.sh',
            str(plan_path.relative_to(ROOT)),str((OUT/'run_01').relative_to(ROOT))]}
    plan['plan_sha256']=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    print('FROZEN',plan_path,plan['plan_sha256'])


if __name__=='__main__': main()
