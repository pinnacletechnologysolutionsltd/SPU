# SIM-XCON-1 single execution. Reads the frozen manifest; edits no source; no network.
import sys, os, json, hashlib, subprocess, shutil, time
sys.dont_write_bytecode = True
R='/home/john/Projects/hardware/SPU'; S='/home/john/Projects/hardware/spu-sim'; X=os.path.dirname(os.path.abspath(__file__))
OUT=X+'/run_01'; os.mkdir(OUT)          # fails if it exists: one run only
t0=time.time(); res=dict(steps={}, started=time.strftime('%FT%T'))
sh=lambda b: hashlib.sha256(b).hexdigest(); fsh=lambda p: sh(open(p,'rb').read())
man=json.load(open(X+'/manifest.json')); assert fsh(X+'/manifest.json')==sys.argv[1], 'manifest not the frozen one'
def run(cmd, **k):
    r=subprocess.run(cmd, capture_output=True, text=True, **k); return r
def rec(name, ok, **d): res['steps'][name]=dict(ok=bool(ok), **d); print(name, 'PASS' if ok else 'FAIL', d, flush=True)
# 1. identities
head=run(['git','-C',S,'rev-parse','HEAD']).stdout.strip(); st=run(['git','-C',S,'status','--short']).stdout
rec('spu_sim_baseline', head==man['spu_sim_commit']=='c1e0676eee5d2398b8d90eec43bd55b2d2f6b924' and st=='', head=head, dirty_lines=len(st.splitlines()))
bad=[p for p,h in {**man['python_modules'],**man['rtl_modules'],**man['fixture_files']}.items() if fsh(R+'/'+p)!=h]
rec('research_inputs_unchanged_since_freeze', not bad, mismatched=bad)
pk=open(R+'/fixtures/gpu_t1d_scene_wire_64b.bin','rb').read()
rec('packet_identity', sh(pk)==man['packet_sha256'] and fsh(S+'/fixtures/gpu_t1d_scene_wire_64b.bin')==man['packet_sha256'], sha=sh(pk))
rec('reference_json_identity', fsh(R+'/fixtures/gpu_t1d_scene_reference.json')==man['reference_json_sha256']==fsh(S+'/fixtures/gpu_t1d_scene_reference.json'))
# 2. build the C++ simulator from the committed tree
src=OUT+'/src'; os.mkdir(src)
a=subprocess.run(f"git -C {S} archive c1e0676 | tar -x -C {src}", shell=True, capture_output=True, text=True)
cfg=run(['cmake','-S',src,'-B',OUT+'/build','-DCMAKE_BUILD_TYPE=Release']); bld=run(['cmake','--build',OUT+'/build','--parallel','4'])
exe=OUT+'/build/spu-sim'
open(OUT+'/build.log','w').write(cfg.stdout+cfg.stderr+bld.stdout+bld.stderr)
rec('cpp_build_from_c1e0676', a.returncode==0 and cfg.returncode==0 and bld.returncode==0 and os.path.exists(exe), exe_sha256=fsh(exe) if os.path.exists(exe) else None)
# 3. C++ frame
cmd=[exe,'gpu','render',S+'/fixtures/gpu_t1d_scene_wire_64b.bin','--output',OUT+'/cpp.rgb8']
r=subprocess.run(cmd,cwd=src,capture_output=True,text=True); cpp=open(OUT+'/cpp.rgb8','rb').read()
res['cpp_command']=cmd; res['cpp_cwd']=src
# 4. Python frame
sys.path.insert(0,R+'/software'); sys.path.insert(0,R+'/software/tests')
from spu_gpu_eval.device_model import prepare_scene, render_rgb8
import test_gpu_device_model_s2 as s2
py=render_rgb8(prepare_scene(pk)); open(OUT+'/py.rgb8','wb').write(py)
res['python_command']='spu_gpu_eval.device_model.render_rgb8(prepare_scene(packet_bytes))'
rec('cpp_python_byte_identical', cpp==py and len(cpp)==640*480*3==921600, cpp_sha=sh(cpp), py_sha=sh(py), cpp_rc=r.returncode)
rec('frame_hash_matches_frozen', sh(cpp)==sh(py)==man['expected_frame_sha256'], expected=man['expected_frame_sha256'])
# 5. frozen expected pixels vs both frames
mism=[]
for p in man['points']:
    o=(p['y']*640+p['x'])*3; e=bytes(v*17 for v in p['expected_rgb'])
    if cpp[o:o+3]!=e or py[o:o+3]!=e: mism.append((p['x'],p['y']))
rec('frozen_pixels_vs_frames', not mism, points=len(man['points']), mismatches=mism)
# 6. RTL datapath at frozen pixels, one call; subprocess output tee'd (no source change)
real=s2.subprocess.run; logs=[]
def tee(cmd,*a,**k):
    r=real(cmd,*a,**k); logs.append(dict(cmd=[str(c) for c in cmd],rc=r.returncode,stdout=r.stdout,stderr=r.stderr))
    if str(cmd[0])=='iverilog':
        shutil.copy(str(cmd[6]), OUT+'/rtl_tb.v')
    return r
s2.subprocess.run=tee
expected={(p['x'],p['y']):tuple(p['expected_rgb']) for p in man['points']}
try:
    s2._rtl_packet_datapath(pk, expected); rtl_ok=True; err=''
except AssertionError as ex:
    rtl_ok=False; err=str(ex)[:3000]
s2.subprocess.run=real
json.dump(logs,open(OUT+'/rtl_commands.json','w'),indent=1)
vvp=[l for l in logs if l['cmd'][0]=='vvp']; pix=[ln for l in vvp for ln in l['stdout'].splitlines() if ln.startswith('PIXEL')]
rec('rtl_selected_pixels', rtl_ok and len(pix)==len(expected), points=len(expected), pixel_lines=len(pix), detail=err)
# 7. post-run integrity
bad2=[p for p,h in {**man['python_modules'],**man['rtl_modules'],**man['fixture_files']}.items() if fsh(R+'/'+p)!=h]
st2=run(['git','-C',S,'status','--short']).stdout
rec('inputs_unchanged_after_run', not bad2 and st2=='', mismatched=bad2, spu_sim_dirty=len(st2.splitlines()))
res['elapsed_s']=round(time.time()-t0,1); res['all_pass']=all(s['ok'] for s in res['steps'].values())
json.dump(res,open(OUT+'/result.json','w'),indent=1,sort_keys=True)
print('ALL_PASS' if res['all_pass'] else 'NOT_ALL_PASS', res['elapsed_s'],'s')
sys.exit(0 if res['all_pass'] else 1)
