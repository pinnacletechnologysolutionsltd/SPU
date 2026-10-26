"""Independent QCG-0 fixture oracle; stdlib only, no children/network/imported project code."""
from fractions import Fraction as F
from itertools import product, permutations
from math import comb
from pathlib import Path
import json, resource, time, hashlib, sys
START=time.monotonic()
BASE=Path('research/qcg_0')
OUT=BASE/'QUINTIC_FIXTURE_VALUES.json'
assert not OUT.exists()
def trim(a):
 a=list(map(F,a))
 while len(a)>1 and not a[-1]: a.pop()
 return a
def add(a,b): return trim([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def neg(a): return [-x for x in a]
def sub(a,b): return add(a,neg(b))
def scale(a,c): return trim([x*c for x in a])
def mul(a,b):
 r=[F(0)]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):
   assert (abs(x.numerator*y.numerator)).bit_length()<=16384
   r[i+j]+=x*y
   assert max(abs(r[i+j].numerator).bit_length(),r[i+j].denominator.bit_length())<=4096
 return trim(r)
def der(a): return trim([i*a[i] for i in range(1,len(a))] or [0])
def integ(a): return [F(0)]+[x/F(i+1) for i,x in enumerate(a)]
def ev(a,t):
 r=F(0)
 for x in reversed(a): r=r*t+x
 return r
def comp(a,b):
 r=[F(0)]
 for x in reversed(a): r=add(mul(r,b),[x])
 return r
def bern(a,n): return [sum((a[k]*F(comb(i,k),comb(n,k)) for k in range(min(i,len(a)-1)+1)),F(0)) for i in range(n+1)]
def unbern(b):
 n=len(b)-1;r=[F(0)]
 for i,x in enumerate(b):
  for j in range(n-i+1):
   c=[F(0)]*(i+j)+[x*comb(n,i)*comb(n-i,j)*(-1)**j];r=add(r,c)
 return r
def cast(b,t):
 b=list(b)
 while len(b)>1:b=[(1-t)*b[i]+t*b[i+1] for i in range(len(b)-1)]
 return b[0]
def resultant(u,v):
 a,b,c=reversed(u);d,e,f=reversed(v)
 m=[[a,b,c,0],[0,a,b,c],[d,e,f,0],[0,d,e,f]];r=0
 for p in permutations(range(4)):
  q=(-1)**sum(p[i]>p[j] for i in range(4) for j in range(i+1,4))
  for i in range(4):q*=m[i][p[i]]
  r+=q
 return r
def curve(u,v):
 u=trim(u);v=trim(v);xx=sub(mul(u,u),mul(v,v));yy=scale(mul(u,v),2);s=add(mul(u,u),mul(v,v));n=sub(mul(u,der(v)),mul(der(u),v));d=mul(s,s)
 assert add(mul(xx,xx),mul(yy,yy))==d
 r={'U':u,'V':v,'U_prime':der(u),'V_prime':der(v),'dx':xx,'dy':yy,'sigma':s,'sigma_squared':d,'x':integ(xx),'y':integ(yy),'S':integ(s),'N_raw':n,'D_raw':d,'curvature_numerator_corrected':scale(n,2)}
 assert der(r['S'])==s
 r['degrees']={k:len(p)-1 for k,p in r.items() if isinstance(p,list)}
 r['bernstein']={k:bern(r[k],5 if k in ('x','y') else 4) for k in ('x','y','dx','dy')}
 for k,b in r['bernstein'].items():assert unbern(b)==r[k]
 for k in ('x','y'):
  b=r['bernstein'][k]; db=[5*(b[i+1]-b[i]) for i in range(5)]
  assert db==r['bernstein']['d'+k]
 r['endpoint']=[ev(r[k],F(1)) for k in ('x','y','S')]
 r['endpoint_curvature_pairs_corrected']=[[ev(scale(n,2),t),ev(d,t)] for t in (F(0),F(1))]
 r['curvature_cross_checks']=[]
 for t in map(F,('0','1/7','1/3','1/2','1')):
  cross=ev(xx,t)*ev(der(yy),t)-ev(yy,t)*ev(der(xx),t)
  direct=cross/ev(s,t)**3; formula=2*ev(n,t)/ev(d,t)
  assert direct==formula
  r['curvature_cross_checks'].append({'t':t,'cross_over_speed_cubed':direct,'raw_N_over_D':ev(n,t)/ev(d,t)})
 return r
log=[]
for tup in sorted(product((-2,-1,1,2),repeat=6),key=lambda t:(max(map(abs,t)),sum(map(abs,t)),t)):
 assert len(log)<4096
 u=trim(tup[:3]);v=trim(tup[3:]);res=resultant(u,v);n=sub(mul(u,der(v)),mul(der(u),v))
 failed=[]
 if not res:failed.append('K2')
 if len(n)<2:failed.append('K3')
 if n==[0]:failed.append('K4')
 log.append({'tuple':list(tup),'resultant':res,'failed':failed})
 if not failed:break
ph5=curve(u,v); ph5['resultant']=res;ph3=curve([1],[0,1])
tape=list(map(F,('5/7','1/9','3/8','8/9','1/2','2/5','6/7','0','1','1/3','7/10','2/9','5/6','3/4','1/9','5/7')))
def cella(r,t):
 return {'t':t,'values':[ev(r[k],t) for k in ('x','y','dx','dy','sigma_squared','sigma','S','N_raw','D_raw')],'D_nonzero':ev(r['D_raw'],t)!=0,'kappa_corrected':2*ev(r['N_raw'],t)/ev(r['D_raw'],t)}
def seq(r):
 rows=[]
 for j in range(17):
  t=F(j,16);s=ev(r['sigma'],t)
  row={'t':t,'S1':[ev(r[k],t) for k in ('x','y')],'S2_add':[ev(r[k],t) for k in ('dx','dy','sigma')]+[ev(r[k],t)/s for k in ('dx','dy')],'S3_kappa':2*ev(r['N_raw'],t)/s**2,'S3_arc_increment_to_next':ev(r['S'],t+F(1,16))-ev(r['S'],t) if j<16 else None}
  for k in ('x','y','dx','dy'): assert cast(r['bernstein'][k],t)==ev(r[k],t)
  rows.append(row)
 # independent finite difference readback and synthetic Taylor shifts, no candidate engines
 for k in ('x','y','S','dx','dy','sigma'):
  p=r[k]; levels=[[ev(p,F(j,16)) for j in range(len(p))]]
  while len(levels[-1])>1:levels.append([b-a for a,b in zip(levels[-1],levels[-1][1:])])
  ds=[z[0] for z in levels]
  for j in range(17): assert sum((F(comb(j,i))*ds[i] for i in range(min(j,len(ds)-1)+1)),F(0))==ev(p,F(j,16))
  for t in (F(1,16),F(1,3)):
   q=list(p); shifted=[]
   while q:
    synthetic=[F(0)]*len(q);synthetic[-1]=q[-1]
    for i in range(len(q)-2,-1,-1):synthetic[i]=q[i]+t*synthetic[i+1]
    shifted.append(synthetic[0]);q=synthetic[1:]
   assert comp(shifted,[-t,F(1)])==p
 return rows
phi=trim([0,F(4,49),F(18,49),F(27,49)]);dp=der(phi);q=trim([F(-2,7),F(-9,7)])
assert dp==mul(q,q) and ev(phi,F(1))==1
xp=comp(ph3['x'],phi);yp=comp(ph3['y'],phi);sp=comp(ph3['S'],phi)
up=q;vp=mul(phi,q)
assert der(xp)==sub(mul(up,up),mul(vp,vp))
assert der(yp)==scale(mul(up,vp),2)
ret={'phi':phi,'phi_prime':dp,'h_form':{'U':[F(1)],'V':phi,'h':dp},'primitive':{'U':up,'V':vp,'h':[F(1)]},'x':xp,'y':yp,'S':sp,'degrees':[len(xp)-1,len(yp)-1,len(sp)-1],'rows':[]}
for t in tape:
 f=ev(phi,t);d=ev(dp,t);s=d*ev(ph3['sigma'],f)
 vals=[ev(xp,t),ev(yp,t),ev(der(xp),t),ev(der(yp),t),s,abs(s),ev(sp,t)]
 assert vals[:2]==[ev(ph3[k],f) for k in ('x','y')]
 assert vals[2:4]==[d*ev(ph3[k],f) for k in ('dx','dy')]
 for p in (xp,yp,sp):assert cast(bern(p,len(p)-1),t)==ev(p,t)
 ret['rows'].append({'t':t,'values':vals})
bad=trim([0,4,-4]);bs=comp(ph3['S'],bad)
ret['nonmonotone']={'phi':bad,'phi_prime':der(bad),'turn':F(1,2),'oriented_S':bs,'traversal_first_piece':bs,'traversal_second_piece':sub([F(8,3)],bs),'total_length':F(8,3),'total_polynomial_length_status':'OUT_OF_DOMAIN','rows':[{'t':t,'oriented':ev(bs,t),'traversal':ev(bs,t) if t<=F(1,2) else F(8,3)-ev(bs,t)} for t in tape]}
h=F(1,4);a=1-h*h/2+h**4/24;b=h-h**3/6;rho=a*a+b*b-1
joins=[]
for u0,v0 in ((1,1),(2,2),(-1,-1),(1,0),(1,-1),(10**6,10**6+1)):
 cross=v0-u0;dot=u0+v0;vel=[u0*u0-v0*v0,2*u0*v0]
 joins.append({'next_generator':[u0,v0],'generator_cross':cross,'generator_dot':dot,'next_velocity':vel,'G1':cross==0,'cusp':dot==0,'C1':vel==[0,2],'G0':'requires placement','C2':'requires next derivative','G2':'requires next derivative'})
rot=[];z=(1,0)
for k in range(17):
 if k:z=(3*z[0]-4*z[1],4*z[0]+3*z[1])
 zz=[F(v,5**k) for v in z];assert all(v.denominator==5**k for v in zz) if k else True
 rot.append({'k':k,'first_column':zz,'common_denominator':5**k})
values={'schema':'QCG0-independent-fixtures-v1','disposition':'REVISE','curvature_semantics':'Frozen N_raw=UVprime-UprimeV, D_raw=sigma^2 retained. True signed kappa=2*N_raw/D_raw. CellA literal raw pair is not a true curvature pair.','selection_log':log,'selected_tuple':list(tup),'PH5':ph5,'PH3':ph3,'cell_A':[cella(ph5,t) for t in tape],'sequential':{'PH3':seq(ph3),'PH5':seq(ph5)},'cell_B':ret,'controls':{'joins':joins,'near_closed_residual':F(1,10**6),'harmonic_order4':{'h':h,'matrix_diagonal':a,'matrix_upper_right':b,'matrix_lower_left':-b,'forward_backward_residual_multiplier':rho,'initial_state_basis_residuals':[[rho,F(0)],[F(0),rho]]},'E1a_C4':{'R':[[0,-1],[1,0]],'R4':[[1,0],[0,1]]},'E1b':rot,'underspecified':['S5 segment translations/parameter convention','C2/G2 next segment generator derivatives','harmonic initial P,V: residual supplied as operator','S3 final sample has no next interval: null']}}
def encode(o):
 if isinstance(o,F):return [o.numerator,o.denominator]
 if isinstance(o,dict):return {k:encode(v) for k,v in o.items()}
 if isinstance(o,(list,tuple)):return [encode(v) for v in o]
 return o
blob=json.dumps(encode(values),sort_keys=True,indent=2)+'\n';assert len(blob.encode())<10*1024**2
with OUT.open('x') as f:f.write(blob)
assert json.loads(OUT.read_text())==encode(values)
print(json.dumps({'status':'COMPLETE','selected_tuple':tup,'resultant':str(res),'tuples_examined':len(log),'value_bytes':len(blob),'value_sha256':hashlib.sha256(blob.encode()).hexdigest(),'elapsed_s':time.monotonic()-START,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'children':0,'argv':sys.argv,'cwd':str(Path.cwd()),'as_limit':resource.getrlimit(resource.RLIMIT_AS)}))
