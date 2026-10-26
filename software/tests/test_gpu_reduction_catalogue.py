#!/usr/bin/env python3
"""GCR-1 adapter, cache and observable-control qualification (Stage A only)."""
import argparse,copy,hashlib,json,subprocess,sys
from dataclasses import replace,asdict
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software.experiments import gpu_reduction_candidates as candidates
from software.experiments.gpu_reduction_catalogue import identity
from software.experiments.gpu_reduction_oracle import observe,MissingObservation,plane_identity,exact_equal
from software.spu_gpu_eval.device_model import pixel_decision,_depth_value

CONTROLS=('edge_sign','edge_factor','depth_association','coefficient_bit','tie_owner',
          'cache_omit_z','missing_field')


def points(data):
    vertices=[v for t in data['triangles'] for v in t['vertices']]
    center=tuple(sum(v[i] for v in data['triangles'][0]['vertices'])//3 for i in (0,1))
    return [*(tuple(v[:2]) for v in vertices),center,(0,479)]


def assert_equivalent(data,original,reduced,delete=False,tie=False):
    scene=candidates.parse_scene_data(data)
    if not plane_identity(scene,reduced):raise AssertionError('Independent plane identity rejected')
    for x,y in points(data):
        if not exact_equal(scene,reduced,x,y):raise AssertionError('Independent exact observation rejected')
        a,b=pixel_decision(original,x,y),pixel_decision(reduced,x,y)
        if delete:b.pop('depths')
        if tie and len(b['covered_by'])==2:
            b['winner']=1;b['rgb']=list(reduced.decoded.triangles[1].rgb)
        try:equal=observe(a)==observe(b)
        except MissingObservation as error:raise AssertionError('UNSUPPORTED:'+str(error)) from error
        if not equal:raise AssertionError('Finite device observation rejected')


def negative(name,base,identities):
    data=copy.deepcopy(base)
    if name in ('tie_owner','cache_omit_z'):
        data['triangles'][1]['vertices']=copy.deepcopy(data['triangles'][0]['vertices'])
        if name=='cache_omit_z':
            for v in data['triangles'][1]['vertices']:v[2]+=1
    _,original,_=candidates.prepare(data,'ORIGINAL',identities)
    reduced=original
    if name=='cache_omit_z':
        def broken_key(t,i):return (t.edges,i['rom_sha256'],i['preparation_sha256'])
        with patch.object(candidates,'cache_key',broken_key):
            _,reduced,_=candidates.prepare(data,'C3',identities)
    elif name=='coefficient_bit':
        p=original.depth[0]
        if not 0<=p.frac_bits<56:raise RuntimeError('Chosen poison bit outside coefficient')
        reduced=replace(original,depth=(replace(p,c_z=p.c_z^(1<<p.frac_bits)),original.depth[1]))
    elif name in ('edge_sign','edge_factor','depth_association'):
        t=original.decoded.triangles[0]
        if name=='edge_sign':t=replace(t,edges=tuple(tuple(-v for v in e) for e in t.edges))
        elif name=='edge_factor':t=replace(t,edges=(tuple(v*2 for v in t.edges[0]),*t.edges[1:]))
        else:t=replace(t,z=(t.z[1],t.z[0],t.z[2]))
        reduced=replace(original,decoded=replace(original.decoded,triangles=(t,original.decoded.triangles[1])))
    print(json.dumps(dict(input_sha256=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
                          checker='assert_equivalent',poison=name,original_depth=[asdict(p) for p in original.depth],
                          candidate_depth=[asdict(p) for p in reduced.depth],candidate_edges=[t.edges for t in reduced.decoded.triangles])))
    assert_equivalent(data,original,reduced,delete=name=='missing_field',tie=name=='tie_owner')
    raise RuntimeError('Invisible poison escaped checker')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--negative',choices=CONTROLS)
    args=parser.parse_args()
    base=json.loads((args.corpus/'baseline.json').read_text());identities=identity()
    if args.negative:negative(args.negative,base,identities);return
    if args.output:args.output.mkdir(parents=True,exist_ok=False)
    _,original,_=candidates.prepare(base,'ORIGINAL',identities)
    for p in original.depth:
        adapter=candidates.ConstantDepth(p.a_z,p.b_z,p.c_z,p.frac_bits)
        for x,y in points(base):
            if _depth_value(p,x,y)!=_depth_value(adapter,x,y):raise AssertionError('Four-field adapter')
    duplicate=json.loads((args.corpus/'variant4.json').read_text())
    cache={};_,first,info=candidates.prepare(duplicate,'C3',identities,cache)
    if info['operations']['cache_hits']!=1:raise AssertionError('Required duplicate cache hit')
    _,source,_=candidates.prepare(duplicate,'ORIGINAL',identities)
    if tuple(map(asdict,source.depth))!=tuple(map(asdict,first.depth)):raise AssertionError('Nine-field reuse')
    assert_equivalent(duplicate,source,first)
    before=dict(cache)
    for defect in ('boolean','range','degenerate','missing'):
        bad=copy.deepcopy(duplicate)
        if defect=='boolean':bad['triangles'][0]['vertices'][0][2]=True
        if defect=='range':bad['triangles'][0]['vertices'][0][2]=65536
        if defect=='degenerate':bad['triangles'][0]['vertices'][1]=bad['triangles'][0]['vertices'][0][:]
        if defect=='missing':del bad['triangles'][0]['rgb']
        try:candidates.prepare(bad,'C3',identities,cache)
        except ValueError:pass
        else:raise AssertionError('Warm cache bypassed validation')
        if cache!=before:raise AssertionError('Malformed input changed cache')
    # Valid empty background is distinct from missing observations.
    if observe(pixel_decision(original,0,479))[2]!=():raise AssertionError('Background fixture')
    controls=[]
    for name in CONTROLS:
        command=[sys.executable,str(Path(__file__).resolve()),'--corpus',str(args.corpus),'--negative',name]
        result=subprocess.run(command,capture_output=True,text=True,timeout=30)
        if result.returncode==0 or 'AssertionError' not in result.stderr:
            raise AssertionError((name,'Control failed outside intended checker',result.stderr))
        controls.append(dict(name=name,command=command,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,
                             stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),
                             stderr_sha256=hashlib.sha256(result.stderr.encode()).hexdigest()))
    report=dict(status='PASS_STAGE_A_ORACLE_ADAPTER_CONTROLS',negative_controls=controls,
                scope='Sampled falsification only; full-frame equivalence remains untested')
    if args.output:(args.output/'stage_pass.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],controls=len(controls))))


if __name__=='__main__':main()
