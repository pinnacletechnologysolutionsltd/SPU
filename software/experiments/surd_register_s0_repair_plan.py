"""Freeze revised source identities after the preserved S0 runner failure."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/spu_surd_register/s0_20261006'
DEST=OUT/'attempt_02/plan.json'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if DEST.exists(): raise SystemExit('refuse repair-plan overwrite')
    parent=json.loads((OUT/'plan.json').read_text()); parent_hash=parent['plan_sha256']
    status=subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,check=True).stdout
    (DEST.parent/'git_status.txt').write_bytes(status)
    plan=dict(parent); plan['parent_plan_sha256']=parent_hash; plan['campaign_attempt']=2
    plan['dirty']=bool(status); plan['dirty_status_sha256']=hashlib.sha256(status).hexdigest()
    plan['source_hashes']={name:digest(ROOT/name) for name in parent['source_hashes']}
    own='software/experiments/surd_register_s0_repair_plan.py'
    plan['source_hashes'][own]=digest(ROOT/own)
    plan['repair_reason']='read CirculantJoint.f/g/h explicitly in independent oracle adapter'
    plan['command']=['timeout','--signal=KILL','60s','python3',
        'software/experiments/surd_register_s0_runner.py',str(DEST.relative_to(ROOT))]
    plan.pop('plan_sha256',None)
    plan['plan_sha256']=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    DEST.write_text(json.dumps(plan,indent=2)+'\n')
    print('FROZEN_REPAIR',DEST,plan['plan_sha256'])


if __name__=='__main__': main()
