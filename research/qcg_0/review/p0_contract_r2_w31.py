"""Minimal independent bounded-width arithmetic trace, only unambiguous Cell A steps."""
from fractions import Fraction as F
from pathlib import Path
from collections import Counter
import json,hashlib,time,resource,sys
start=time.monotonic();base=Path('research/qcg_0');out=base/'P0_CONTRACT_R2_LEDGER_STAGE_EXPECTATIONS.json';assert not out.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'QCG0_P0_EXECUTION_CONTRACT.md':'4c95617479b858919c86ad5be3cedad37fb9e547f88b9c6d9a8764e8b083e54f','QUINTIC_FIXTURE_VALUES.json':'8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34','QCG0_PREREGISTRATION.md':'eade4b5f0957c3679c94b67d8f4b1f6b6d005d65316a5337e6c8dfb9370b98dd'}
for p,h in pins.items():assert sha(base/p)==h
old=json.loads((base/'QUINTIC_FIXTURE_VALUES.json').read_text());ph=old['PH5'];src=lambda k:[F(*v) for v in ph[k]]
class Refusal(Exception):
 def __init__(self,event,value,limit):self.event=event;self.value=value;self.limit=limit
class Trace:
 def __init__(self,arm,phase):self.arm=arm;self.phase=phase;self.step='';self.k=0;self.count=Counter();self.events=[]
 def at(self,step):self.step=step;self.k=0
 def check(self,v,bits,sub):
  n=max(1,abs(v).bit_length())
  if n>bits:raise Refusal(f'{self.arm}.{self.phase}.{self.step}.{self.k}.{sub}',v,bits)
 def op(self,kind,a,b):
  a,b=F(a),F(b);self.k+=1;self.count[kind]+=1;self.events.append((self.step,self.k,kind))
  if kind=='M':raw=[a.numerator*b.numerator,a.denominator*b.denominator];r=a*b
  elif kind=='A':raw=[a.numerator*b.denominator,b.numerator*a.denominator,a.numerator*b.denominator+b.numerator*a.denominator,a.denominator*b.denominator];r=a+b
  elif kind=='D':assert b!=0;raw=[a.numerator*b.denominator,a.denominator*b.numerator];r=a/b
  elif kind=='S':assert b==2;raw=[];r=a*2
  else:raise AssertionError(kind)
  for j,v in enumerate(raw):self.check(v,63,'r'+str(j+1))
  if kind in ('M','A','D'):self.count['G_calls']+=1
  self.check(r.numerator,31,'e1');self.check(r.denominator,31,'e2')
  return r
 def horner(self,c,t):
  r=c[-1]
  for a in reversed(c[:-1]):r=self.op('A',self.op('M',r,t),a)
  return r
 def pmul(self,a,b):
  r=[None]*(len(a)+len(b)-1)
  for i,x in enumerate(a):
   for j,y in enumerate(b):
    t=self.op('M',x,y);r[i+j]=t if r[i+j] is None else self.op('A',r[i+j],t)
  return r
 def pplus(self,a,b,sign):return [self.op('A',a[i],sign*b[i]) for i in range(len(a))]
 def pint(self,a):return [F(0)]+[self.op('D',v,i+1) for i,v in enumerate(a)]
 def pder(self,a):return [self.op('M',a[i],i) for i in range(1,len(a))]
def prep(arm,last):
 t=Trace(arm,'P');u=src('U');v=src('V');d={'U':u,'V':v}
 steps=[('UU',lambda:t.pmul(u,u),4),('VV',lambda:t.pmul(v,v),4),('UV',lambda:t.pmul(u,v),4),('dx',lambda:t.pplus(d['UU'],d['VV'],-1),3),('dy',lambda:[t.op('S',z,2) for z in d['UV']],4),('sg',lambda:t.pplus(d['UU'],d['VV'],1),4),('X',lambda:t.pint(d['dx']),4),('Y',lambda:t.pint(d['dy']),5),('SS',lambda:t.pint(d['sg']),5),('U1',lambda:t.pder(u),1),('V1',lambda:t.pder(v),1),('NP1',lambda:t.pmul(u,d['V1']),3),('NP2',lambda:t.pmul(d['U1'],v),3),('Np',lambda:t.pplus(d['NP1'],d['NP2'],-1),2),('Nk',lambda:[t.op('S',z,2) for z in d['Np']],2)]
 for i,(name,fn,degree) in enumerate(steps[:last],1):
  t.at('P'+str(i));r=fn();assert not any(r[degree+1:]);d[name]=r[:degree+1]
 checks={'dx':'dx','dy':'dy','sg':'sigma','X':'x','Y':'y','SS':'S','U1':'U_prime','V1':'V_prime','Np':'N_raw','Nk':'curvature_numerator_corrected'}
 for a,b in checks.items():
  if a in d:assert d[a]==src(b)
 return d,dict(t.count)
# These counts are reviewed preparation checks, not regenerated golden fixtures.
prepared={};counts={}
for name,last in [('B-Horner',15),('B-PH',11),('C1',11),('C2-prep-only',9)]:prepared[name],counts[name]=prep(name,last)
expected={'B-Horner':{'M':43,'A':30,'S':8,'D':14,'G_calls':87},'B-PH':{'M':31,'A':22,'S':5,'D':14,'G_calls':67},'C1':{'M':31,'A':22,'S':5,'D':14,'G_calls':67},'C2-prep-only':{'M':27,'A':22,'S':5,'D':14,'G_calls':63}}
assert counts==expected
stages={}
for arm in ('B-Horner','B-PH','C1'):
 d=prepared[arm];rs=[]
 for j,row in enumerate(old['cell_A']):
  p=F(*row['t']);t=Trace(arm,'Q.q'+f'{j:02}');rec={'q':j,'parameter':row['t']}
  try:
   if arm=='B-Horner':
    for step,key in enumerate(('X','Y','dx','dy','sg','SS','Nk'),1):
     t.at('a'+str(step));value=t.horner(d[key],p)
     if key=='sg':s=value
    t.at('a8');t.op('M',s,s)
   else:
    z=[]
    for step,key in enumerate(('U','V','U1','V1'),1):t.at('b'+str(step));z.append(t.horner(d[key],p))
    u,v,u1,v1=z
    t.at('b5');uu=t.op('M',u,u);t.at('b6');vv=t.op('M',v,v);t.at('b7');uv=t.op('M',u,v)
    t.at('b8');t.op('A',uu,-vv);t.at('b9');t.op('S',uv,2);t.at('b10');s=t.op('A',uu,vv);t.at('b11');t.op('M',s,s)
    t.at('b12');m1=t.op('M',u,v1);t.at('b13');m2=t.op('M',u1,v);t.at('b14');n=t.op('A',m1,-m2);t.at('b15');t.op('S',n,2)
    for step,key in ((16,'X'),(17,'Y'),(18,'SS')):t.at('b'+str(step));t.horner(d[key],p)
   rec.update(status='OK',first_refusal=None)
  except Refusal as e:rec.update(status='REFUSED',code='ARITH_LIMIT',first_refusal=e.event,failing_integer=e.value,limit_bits=e.limit)
  rs.append(rec)
 stages[arm]=rs
value={'schema':'QCG0-p0-contract-r2-local-ledger-stage-expectations-v1','pins':pins,'preparation_counts':counts,'preparation_scope':'PH5 P1-P15/P1-P11/P1-P9 only; counts exclude administrative bound checks and D internal zero validation as implied by the draft K=0 cross-check.','W31_CellA_trace':stages,'status':'PARTIAL_CERTIFICATE','scope':'Minimal independent arithmetic first-refusal trace for named CellA B-Horner/B-PH/C1 branches only; no screened output evaluation, benchmarks, other arms, full P0 or aggregate cost campaign. Existing source coefficients read and preparation trace checked against immutable values.','uncertified':['CellB nested PCOMP and post-compose stage naming','sequential S1 minimal-request program and FD nested stage order','CellA B-Bezier conversion-stage naming and other untraced branches'],'administrative_checks':'Raw r1..rN then reduced e1,e2 follow §3. No K cost claim for internal zero/bound checks; contract should explicitly clarify ledger classification.'}
blob=json.dumps(value,sort_keys=True,indent=2)+'\n'
with out.open('x') as f:f.write(blob)
assert json.loads(out.read_text())==value
for p,h in pins.items():assert sha(base/p)==h
print(json.dumps({'status':'COMPLETE','argv':sys.argv,'cwd':str(Path.cwd()),'script_sha256':sha(Path(__file__)),'expectation_sha256':sha(out),'bytes':len(blob),'preparation_counts':counts,'refusals':{arm:[x for x in rows if x['status']!='OK'] for arm,rows in stages.items()},'elapsed_s':time.monotonic()-start,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'as_limit':resource.getrlimit(resource.RLIMIT_AS),'children':0}))
