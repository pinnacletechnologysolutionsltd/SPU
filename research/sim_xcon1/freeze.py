# SIM-XCON-1 pre-execution freeze: selects RTL pixels and records expected values; executes no comparison.
import sys, json, hashlib, subprocess, os
sys.dont_write_bytecode = True
R='/home/john/Projects/hardware/SPU'; S='/home/john/Projects/hardware/spu-sim'; X=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,R+'/software'); sys.path.insert(0,R+'/software/tests')
from spu_gpu_eval.device_model import prepare_scene, pixel_decision, _edge_value
from spu_gpu_eval.device_packet import decode_packet
import test_gpu_device_model_s2 as s2   # transitive-input discovery only
sh=lambda b: hashlib.sha256(b).hexdigest(); fsh=lambda p: sh(open(p,'rb').read())
pk=open(R+'/fixtures/gpu_t1d_scene_wire_64b.bin','rb').read(); assert sh(pk).startswith('aa2bad57')
ref=json.load(open(R+'/fixtures/gpu_t1d_scene_reference.json')); assert fsh(R+'/fixtures/gpu_t1d_scene_reference.json').startswith('7c48bdef')
sc=prepare_scene(pk); dec=decode_packet(pk)
def info(x,y):
    r=pixel_decision(sc,x,y)
    ev=[min(_edge_value(e,x,y) for e in t.edges) for t in dec.triangles]
    d={dd['triangle']:dd['value'] for dd in r['depths']}
    return r,ev,d
pts={}  # (x,y)->category
def add(x,y,cat):
    pts.setdefault((x,y),cat)
for p in ref['diagnostic_pixels']: add(p['x'],p['y'],'reference_json:'+p['coverage'])
add(320,0,'tie_equal_depth_tri0_wins')
cats={}; best={}
for y in range(0,480):
    for x in range(0,640):
        r,ev,d=info(x,y); k=(tuple(r['covered_by']),r['winner'])
        cats.setdefault(('region',k),[]).append((x,y))
        if any(e==0 for e in ev) and (ev[0]==0 and 0 in r['covered_by'] or ev[1]==0 and 1 in r['covered_by']): cats.setdefault(('on_edge_covered',k),[]).append((x,y))
        if len(d)==2 and d[0]!=d[1]:
            dd=abs(d[0]-d[1]); b=best.get(r['winner'])
            if b is None or dd<b[0]: best[r['winner']]=(dd,x,y)
for key in sorted(cats, key=str):
    lst=cats[key]
    n=2 if key[0]=='region' else 2
    for q in (lst[:1]+lst[-1:])[:n]: add(q[0],q[1],'%s:%s'%(key[0],key[1]))
for w,(dd,x,y) in sorted(best.items()): add(x,y,'depth_near_tie_diff%d_winner%d'%(dd,w))
for (x,y),cat in list(pts.items()):
    if cat.startswith('on_edge_covered'):
        r0,_,_=info(x,y)
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<640 and 0<=ny<480 and info(nx,ny)[0]['covered_by']!=r0['covered_by']:
                add(nx,ny,'adjacent_outside_edge'); break
out=[]
for (x,y),cat in sorted(pts.items()):
    r,ev,d=info(x,y)
    out.append(dict(x=x,y=y,category=cat,expected_rgb=r['rgb'],expected_coverage=r['coverage'],expected_covered_by=r['covered_by'],expected_winner=r['winner'],expected_depths=d))
# reference JSON values must agree with the model before freezing (these are the independent expectations)
for p in ref['diagnostic_pixels']:
    o=[q for q in out if q['x']==p['x'] and q['y']==p['y']][0]; assert o['expected_rgb']==p['rgb']
mods=sorted(m.__file__ for m in sys.modules.values() if getattr(m,'__file__',None) and m.__file__.startswith(R))
rtl=[R+'/hardware/rtl/gpu/'+n for n in ('spu_edge_stepper.v','spu_depth_math.v','spu_reciprocal_core.v','spu_shared_mult35.v','spu_attr_stepper.v','spu_depth_compare.v')]
def v(c):
    r=subprocess.run(c,capture_output=True,text=True); return (r.stdout+r.stderr).splitlines()[0]
man=dict(schema='sim-xcon-1-manifest-v1',
 packet_sha256=sh(pk), reference_json_sha256=fsh(R+'/fixtures/gpu_t1d_scene_reference.json'),
 expected_frame_sha256='96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10',
 frame_format='640x480 RGB8, 3 bytes/pixel, 921600 bytes, 4-bit channel n -> byte n*17',
 spu_sim_commit=subprocess.run(['git','-C',S,'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip(),
 spu_sim_tree=subprocess.run(['git','-C',S,'rev-parse','HEAD^{tree}'],capture_output=True,text=True).stdout.strip(),
 spu_sim_status_lines=len(subprocess.run(['git','-C',S,'status','--short'],capture_output=True,text=True).stdout.splitlines()),
 research_head=subprocess.run(['git','-C',R,'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip(),
 python_modules={m[len(R)+1:]:fsh(m) for m in mods},
 rtl_modules={m[len(R)+1:]:fsh(m) for m in rtl},
 fixture_files={'fixtures/gpu_t1d_scene_wire_64b.bin':fsh(R+'/fixtures/gpu_t1d_scene_wire_64b.bin'),'fixtures/gpu_t1d_scene_reference.json':fsh(R+'/fixtures/gpu_t1d_scene_reference.json')},
 spu_sim_rom_sha256=fsh(S+'/hardware/rtl/arch/gpu_reciprocal_lut_q15.mem'),
 tools=dict(iverilog=v(['iverilog','-V']),vvp=v(['vvp','-V']),python=sys.version.split()[0],cmake=v(['cmake','--version'])),
 rtl_checks='the existing helper asserts the 12-bit pixel colour at each point; coverage/winner/depth are recorded here and are implied only through the winning colour',
 points=out)
json.dump(man,open(X+'/manifest.json','w'),indent=1,sort_keys=True)
from collections import Counter
print(len(out),'points'); print(Counter(p['category'].split(':')[0] for p in out)); print(man['spu_sim_commit'],man['spu_sim_status_lines'],len(mods),'py modules')
print(Counter((p['expected_winner'],tuple(p['expected_covered_by'])) for p in out))
