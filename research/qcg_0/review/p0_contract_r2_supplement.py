"""Independent supplemental P-1 polynomial references; no candidate code imported."""
from fractions import Fraction as F
from math import comb,gcd
from pathlib import Path
import hashlib,json,time,resource,sys
start=time.monotonic(); base=Path('research/qcg_0');out=base/'P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json'
assert not out.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'QCG0_P0_EXECUTION_CONTRACT.md':'4c95617479b858919c86ad5be3cedad37fb9e547f88b9c6d9a8764e8b083e54f','QCG0_P0_EXECUTION_CONTRACT_REVISION_2.diff':'2aace2485b7f3d82d4226e68936edb6fe0b8206dfc72b44afa51a6344b4bba67','QCG0_PREREGISTRATION.md':'eade4b5f0957c3679c94b67d8f4b1f6b6d005d65316a5337e6c8dfb9370b98dd','QUINTIC_FIXTURE_VALUES.json':'8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34','REVISION2_FIXTURE_VALUES.json':'a66af3d68da5a7dba439818778af9e8fe70244e3dc2d8250ea891354124a0b46'}
for p,h in pins.items():assert sha(base/p)==h
maxred=0;maxraw=0
def checked(x):
 global maxred
 x=F(x);maxred=max(maxred,abs(x.numerator).bit_length(),x.denominator.bit_length());assert maxred<=4096
 return x
def addq(a,b):
 global maxraw
 for z in (a.numerator*b.denominator,b.numerator*a.denominator,a.numerator*b.denominator+b.numerator*a.denominator,a.denominator*b.denominator):maxraw=max(maxraw,abs(z).bit_length())
 assert maxraw<=16384
 return checked(a+b)
def mulq(a,b):
 global maxraw
 maxraw=max(maxraw,abs(a.numerator*b.numerator).bit_length(),(a.denominator*b.denominator).bit_length());assert maxraw<=16384
 return checked(a*b)
def trim(a):
 a=list(map(checked,a))
 while len(a)>1 and not a[-1]:a.pop()
 return a
def add(a,b):return trim([addq(a[i] if i<len(a) else F(0),b[i] if i<len(b) else F(0)) for i in range(max(len(a),len(b)))])
def sc(a,s):return trim([mulq(x,F(s)) for x in a])
def mul(a,b):
 c=[F(0)]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]=addq(c[i+j],mulq(x,y))
 return trim(c)
def der(a):return trim([mulq(a[i],F(i)) for i in range(1,len(a))] or [0])
def integ(a):return [F(0)]+[mulq(v,F(1,i+1)) for i,v in enumerate(a)]
def ev(a,t):
 r=F(0)
 for c in reversed(a):r=addq(mulq(r,t),c)
 return r
def comp(a,b):
 r=[F(0)]
 for c in reversed(a):r=add(mul(r,b),[c])
 return r
def bp(a):
 n=len(a)-1
 return [sum((a[j]*F(comb(i,j),comb(n,j)) for j in range(i+1)),F(0)) for i in range(n+1)]
def cast(b,t):
 while len(b)>1:b=[(1-t)*x+t*y for x,y in zip(b,b[1:])]
 return b[0]
def curve(u,v,h):
 u,v,h=map(trim,(u,v,h));g=add(mul(u,u),mul(v,v));dx=mul(h,add(mul(u,u),sc(mul(v,v),-1)));dy=sc(mul(h,mul(u,v)),2)
 return {'U':u,'V':v,'h':h,'g':g,'dx':dx,'dy':dy,'x':integ(dx),'y':integ(dy),'S_or':integ(mul(h,g))}
ph3=curve([1],[0,1],[1]);ph3h=curve([1],[0,1],[1,1]);rev=trim([1,-1]);ns=trim([0,0,1]);sq=trim([0,F(4,49),F(18,49),F(27,49)])
random=list(map(F,('5/7','1/9','3/8','8/9','1/2','2/5','6/7','0','1','1/3','7/10','2/9','5/6','3/4','1/9','5/7')));dyadic=[F(k,16) for k in range(17)]
def retimed(source,phi,primitive=False):
 u=comp(source['U'],phi);v=comp(source['V'],phi);h=mul(comp(source['h'],phi),der(phi))
 if primitive:u,v,h=sc(v,-1),u,trim([1])
 c=curve(u,v,h)
 for k in ('x','y'):
  c[k]=comp(source[k],phi);assert der(c[k])==c['d'+k]
 base_oriented=add(comp(source['S_or'],phi),[-ev(source['S_or'],ev(phi,F(0)))])
 assert c['S_or']==sc(base_oriented,-1 if primitive else 1)
 c['base_oriented_increment']=base_oriented
 return c
cases={'PH3_rev_h_form':retimed(ph3,rev),'PH3_rev_primitive':retimed(ph3,rev,True),'PH3_ns_h_form':retimed(ph3,ns),'PH3h_sq_h_form':retimed(ph3h,sq)}
def rows(c,tape):
 answer=[]
 for k,t in enumerate(tape):
  x,y,dx,dy,g,h=[ev(c[n],t) for n in ('x','y','dx','dy','g','h')];ss=h*g;s=abs(ss);d=[(ev(c['U'],t)**2-ev(c['V'],t)**2)/g,2*ev(c['U'],t)*ev(c['V'],t)/g];regular=s!=0
  for n in ('x','y','dx','dy'):assert cast(bp(c[n]),t)==ev(c[n],t)
  nr=ev(add(mul(c['U'],der(c['V'])),sc(mul(der(c['U']),c['V']),-1)),t);pair=[2*nr,abs(h)*g*g]
  cross=dx*ev(der(c['dy']),t)-dy*ev(der(c['dx']),t)
  kval=cross/s**3 if regular else None
  if regular:assert kval==pair[0]/pair[1]
  length=ev(c['S_or'],t)*(1 if ev(c['h'],F(1))>0 else -1)
  row={'parameter':t,'position':[x,y],'velocity':[dx,dy],'signed_progression_rate':ss,'nonnegative_speed':s,'continued_direction':d,'unit_tangent':[dx/s,dy/s] if regular else None,'curvature_pair':pair,'signed_curvature':kval,'representation_signed_integral':ev(c['S_or'],t),'base_oriented_length_increment':ev(c['base_oriented_increment'],t),'accumulated_length_increment':length,'requests':{'POSITION':'OK','SPEED':'OK','DIRECTION':'OK','TANGENT':'OK' if regular else 'REFUSED(NONREGULAR)','CURVATURE':'OK' if regular else 'REFUSED(NONREGULAR)'},'regular':regular}
  if tape==dyadic:row['arc_increment_to_next']=None if k==16 else abs(ev(c['S_or'],tape[k+1])-ev(c['S_or'],t))
  answer.append(row)
 return answer
vals={'schema':'QCG0-p0-contract-r2-supplemental-references-v1','supplemental_not_replacement':True,'pins':pins,'cases':{name:{'polynomials':c,'dyadic_S4_rows':rows(c,dyadic),'registered_random_tape_rows':rows(c,random) if name=='PH3h_sq_h_form' else None} for name,c in cases.items()},'nonconstant_h_control':'PH3h composed with phi_sq; htilde=(1+phi_sq)*phi_sqprime. Omitting h composed with phi changes derivatives/speed at nonzero phi.','stationary_convention':'At ns t=0 actual T and kappa refuse; d=(1,0) remains OK; no cancellation extends an actual undefined quotient.','primitive_retiming_ns_request':'REFUSED(NOT_PRIMITIVE_RETIMING)','tapes':{'dyadic':dyadic,'registered_random':random}}
for c in cases.values():assert add(mul(c['dx'],c['dx']),mul(c['dy'],c['dy']))==mul(mul(c['h'],c['g']),mul(c['h'],c['g']))
# Actual traversal agrees between h-form and primitive reversal; continued directions have opposite signs.
a=vals['cases']['PH3_rev_h_form']['dyadic_S4_rows'];b=vals['cases']['PH3_rev_primitive']['dyadic_S4_rows']
for ra,rb in zip(a,b):
 for key in ('position','velocity','nonnegative_speed','unit_tangent','signed_curvature','accumulated_length_increment'):assert ra[key]==rb[key]
 assert ra['continued_direction']==[-z for z in rb['continued_direction']]
def enc(x):
 if isinstance(x,F):assert x.denominator>0 and gcd(x.numerator,x.denominator)==1;return [x.numerator,x.denominator]
 if isinstance(x,list):return [enc(v) for v in x]
 if isinstance(x,dict):return {k:enc(v) for k,v in x.items()}
 return x
v=enc(vals);blob=json.dumps(v,sort_keys=True,indent=2)+'\n';assert len(blob.encode())<10*1024**2
with out.open('x') as f:f.write(blob)
assert json.loads(out.read_text())==v
for p,h in pins.items():assert sha(base/p)==h
print(json.dumps({'status':'COMPLETE','argv':sys.argv,'cwd':str(Path.cwd()),'script_sha256':sha(Path(__file__)),'values_sha256':sha(out),'bytes':len(blob.encode()),'dyadic_rows':68,'nonconstant_h_random_rows':16,'max_tracked_reduced_bits':maxred,'max_tracked_raw_bits':maxraw,'elapsed_s':time.monotonic()-start,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'as_limit':resource.getrlimit(resource.RLIMIT_AS),'children':0}))
