"""New independent R2 exact fixture derivation; no candidate or count engine."""
from fractions import Fraction as F
from math import comb, gcd
from pathlib import Path
import hashlib,json,re,resource,time,sys
start=time.monotonic();base=Path('research/qcg_0'); out=base/'REVISION2_FIXTURE_VALUES.json';assert not out.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'QCG0_PREREGISTRATION.md':'fbaf2b5a85615bf6a3ade33c759f2d496596aeff234dcf2ce684f0f25bec4f42','QUINTIC_FIXTURE_CERTIFICATE.md':'1391b1d9804c0d5b636070b1bee3d1cdb9c445f2bea4df4444c78243cc4cc673','QUINTIC_FIXTURE_VALUES.json':'8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34','QUINTIC_FIXTURE_REVIEW_MANIFEST.json':'15e310df23279ae8d725d3b01bd7bef3bc95da3b260eac98517cdc31606e3704','REVIEW_CALCULATION_AUTHORIZATION.md':'4b9602998d2cb2fab14af5440c892cce06ca4189d98bb7f40616362849d3e324','QCG0_FIXTURE_REVIEW_PACKET.md':'1f6c5b94ab610f4950a4f2244803aeb17def3adf7a21ea50d5664c2759b98c82','QCG0_PREREGISTRATION_REVISION_2.diff':'43c6f44cc697edb2aff9776f435e6b293c882d1870971b0f6cef86ea3a2b5e75','QCG0_REVISION2_REREVIEW_REQUEST.md':'b935018ca8c0b3acc177745a82949ce0693bce9a3f3649a004ff27c76929f728'}
for name,want in pins.items():assert sha(base/name)==want
# Reconstruct superseded text only in memory, never touching current or old artifacts.
current=(base/'QCG0_PREREGISTRATION.md').read_text().splitlines(True); lines=(base/'QCG0_PREREGISTRATION_REVISION_2.diff').read_text().splitlines(True);old=[];pos=0;i=2
while i<len(lines):
 m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert m
 target=int(m[3])-1;old+=current[pos:target];oldchunk=[];newchunk=[];i+=1
 while i<len(lines) and not lines[i].startswith('@@'):
  line=lines[i];i+=1
  assert line[0] in ' +-'
  if line[0] in ' -':oldchunk.append(line[1:])
  if line[0] in ' +':newchunk.append(line[1:])
 assert current[target:target+len(newchunk)]==newchunk
 old+=oldchunk;pos=target+len(newchunk)
old+=current[pos:];oldhash=hashlib.sha256(''.join(old).encode()).hexdigest();assert oldhash=='b33205e92370a41de5d1b7806f8435057065ea5272ea21866f5700be99025fa8'
def tr(a):
 a=list(map(F,a))
 while len(a)>1 and a[-1]==0:a.pop()
 return a
def add(a,b):return tr([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def mul(a,b):
 c=[F(0)]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]+=x*y
 return tr(c)
def scale(a,k):return tr([v*k for v in a])
def der(a):return tr([i*a[i] for i in range(1,len(a))] or [0])
def integ(a):return [F(0)]+[v/F(i+1) for i,v in enumerate(a)]
def ev(a,t):
 r=F(0)
 for v in reversed(a):r=r*t+v
 return r
def bp(a):
 n=len(a)-1
 return [sum((a[k]*F(comb(i,k),comb(n,k)) for k in range(i+1)),F(0)) for i in range(n+1)]
def cast(b,t):
 b=list(b)
 while len(b)>1:b=[(1-t)*x+t*y for x,y in zip(b,b[1:])]
 return b[0]
def cv(u,v,h):
 u,v,h=map(tr,(u,v,h)); g=add(mul(u,u),mul(v,v)); dx=mul(h,add(mul(u,u),scale(mul(v,v),-1)));dy=scale(mul(h,mul(u,v)),2)
 return {'U':u,'V':v,'h':h,'x':integ(dx),'y':integ(dy),'dx':dx,'dy':dy,'ddx':der(dx),'ddy':der(dy),'signed_speed':mul(h,g),'S':integ(mul(h,g))}
def observable(c,t):
 r={k:ev(c[k],t) for k in ('x','y','dx','dy','ddx','ddy','signed_speed','S')};s=abs(r['signed_speed']);assert s>0
 r['speed']=s;r['T']=[r['dx']/s,r['dy']/s];r['kappa']=(r['dx']*r['ddy']-r['dy']*r['ddx'])/s**3
 for k in ('x','y','dx','dy','ddx','ddy','S'):assert cast(bp(c[k]),t)==r[k]
 assert sum(v*v for v in r['T'])==1
 return r
cs=[cv([1],[0,1],[1]),cv([1],[1,1],[1]),cv([1],[2],[1,1])];offsets=[[F(0),F(0)]];lengths=[F(0)]
for c in cs:
 r=observable(c,F(1));offsets.append([offsets[-1][j]+r[k] for j,k in enumerate(('x','y'))]);lengths.append(lengths[-1]+r['S'])
ch=[]
for u in map(F,('0','1/3','2/3','1','4/3','3/2','2','7/3','3')):
 k=min(u.numerator//u.denominator,2);t=u-k;r=observable(cs[k],t)
 ch.append({'u':u,'segment':k,'t':t,'position':[offsets[k][j]+r[n] for j,n in enumerate(('x','y'))],'unit_tangent':r['T'],'speed':r['speed'],'accumulated_arc_length':lengths[k]+r['S']})
def joint(a,b,gap):
 ra=observable(a,F(1));rb=observable(b,F(0));g0=gap==[F(0),F(0)];veq=[ra['dx'],ra['dy']]==[rb['dx'],rb['dy']];aeq=[ra['ddx'],ra['ddy']]==[rb['ddx'],rb['ddy']];teq=ra['T']==rb['T'];opp=ra['T']==[-v for v in rb['T']];keq=ra['kappa']==rb['kappa']
 ua,va=ev(a['U'],F(1)),ev(a['V'],F(1));ub,vb=ev(b['U'],F(0)),ev(b['V'],F(0))
 return {'position_gap':gap,'left_velocity':[ra['dx'],ra['dy']],'right_velocity':[rb['dx'],rb['dy']],'left_acceleration':[ra['ddx'],ra['ddy']],'right_acceleration':[rb['ddx'],rb['ddy']],'left_kappa':ra['kappa'],'right_kappa':rb['kappa'],'generator_cross':ua*vb-va*ub,'generator_dot':ua*ub+va*vb,'raw':{'tangent_equal':teq,'tangent_opposite':opp,'velocity_equal':veq,'acceleration_equal':aeq,'curvature_equal':keq},'join':{'G0':g0,'G1':g0 and teq,'cusp':g0 and opp,'C1':g0 and veq,'C2':g0 and veq and aeq,'G2':g0 and teq and keq}}
bs=[cv([1,1],[1],[1]),cs[1],cv([1,1],[1,2],[1]),cv([2],[2,1],[1]),cv([-1],[-1,-1],[1]),cs[0],cv([1],[-1,1],[1]),cv([1000000],[1000001,1],[1]),cs[1]]
js={f'b{i+1}':joint(cs[0],b,[F(1,4),F(0)] if i==8 else [F(0),F(0)]) for i,b in enumerate(bs)}
loops={}
for name,h in [('L0',F(1)),('L1',F(1000001,1000000))]:
 rev=cv([-1,1],[1],[h]);r=observable(cs[0],F(1));v=observable(rev,F(1));res=[r[k]+v[k] for k in ('x','y')]
 loops[name]={'second_h':h,'first_displacement':[r[k] for k in ('x','y')],'second_displacement':[v[k] for k in ('x','y')],'closure_residual':res,'closed':res==[F(0),F(0)],'total_length':r['S']+v['S']}
# Adapt only old stored scalars: never regenerate or select PH5.
original=json.loads((base/'QUINTIC_FIXTURE_VALUES.json').read_text());adapt=[]
for row in original['cell_A']:
 vals=[F(*p) for p in row['values']];vals[7]*=2
 assert vals[7]/vals[8]==F(*row['kappa_corrected'])
 adapt.append({'t':F(*row['t']),'values':vals,'D_nonzero':row['D_nonzero']})
vals={'schema':'QCG0-revision2-independent-values-v1','disposition':'REVISE','pins':pins,'superseded_revision1_sha256_reconstructed_in_memory':oldhash,'CH1':{'segments':cs,'segment_start_positions':offsets[:-1],'segment_start_lengths':lengths[:-1],'rows':ch,'joins':{'u1':joint(cs[0],cs[1],[F(0),F(0)]),'u2':joint(cs[1],cs[2],[F(0),F(0)])}},'S6_joins':js,'closures':loops,'CellA_adapted_true_curvature_pair':adapt,'join_convention':'Raw endpoint comparisons separate from geometric joins. G1 requires G0; C2 requires G0,C1 and acceleration equality; G2 requires G0,G1 and curvature equality. No gap is a geometric join.'}
maxbits=0
def encode(x):
 global maxbits
 if isinstance(x,F):
  assert x.denominator>0 and gcd(x.numerator,x.denominator)==1
  maxbits=max(maxbits,abs(x.numerator).bit_length(),x.denominator.bit_length());assert maxbits<=4096
  return [x.numerator,x.denominator]
 if isinstance(x,dict):return {k:encode(v) for k,v in x.items()}
 if isinstance(x,list):return [encode(v) for v in x]
 return x
encoded=encode(vals);blob=json.dumps(encoded,sort_keys=True,indent=2)+'\n';assert len(blob.encode())<10*1024**2
with out.open('x') as f:f.write(blob)
assert json.loads(out.read_text())==encoded
for name,want in pins.items():assert sha(base/name)==want
print(json.dumps({'result':'COMPLETE','argv':sys.argv,'cwd':str(Path.cwd()),'source_sha256':sha(Path(__file__)),'new_values_sha256':sha(out),'new_values_bytes':out.stat().st_size,'max_serialized_rational_bits':maxbits,'elapsed_seconds':time.monotonic()-start,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'address_space_limit':resource.getrlimit(resource.RLIMIT_AS),'reconstructed_revision1_sha256':oldhash,'children':0,'new_CH1_rows':len(ch),'new_join_rows':len(js),'adapted_CellA_rows':len(adapt),'closure_residuals':{k:encoded['closures'][k]['closure_residual'] for k in loops},'join_truths':{k:v['join'] for k,v in js.items()}}))
