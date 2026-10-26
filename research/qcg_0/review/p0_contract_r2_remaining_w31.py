"""Remaining uniquely named Cell A W31 width traces; not a pilot or arm benchmark."""
from fractions import Fraction as F
from math import comb
from pathlib import Path
import hashlib,json,time,resource,sys
start=time.monotonic();base=Path('research/qcg_0');out=base/'P0_CONTRACT_R2_REMAINING_CELL_A_STAGE_EXPECTATIONS.json';assert not out.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={'QCG0_P0_EXECUTION_CONTRACT.md':'4c95617479b858919c86ad5be3cedad37fb9e547f88b9c6d9a8764e8b083e54f','QUINTIC_FIXTURE_VALUES.json':'8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34','P0_CONTRACT_R2_LEDGER_STAGE_EXPECTATIONS.json':'093b006b4b11e289066265a9021fba92c28ec252b8df44eac06a48f8eeca75bb'}
for p,h in pins.items():assert sha(base/p)==h
old=json.loads((base/'QUINTIC_FIXTURE_VALUES.json').read_text());ph=old['PH5'];src=lambda k:[F(*v) for v in ph[k]]
ps=[src(k) for k in ('x','y','dx','dy','sigma','S','curvature_numerator_corrected')]
class Refusal(Exception):
 def __init__(self,event,value,bits):self.event,self.value,self.bits=event,value,bits
class WidthTrace:
 def __init__(self,arm,phase):self.arm,self.phase=arm,phase;self.k=0;self.step='';self.max_raw=1;self.max_red=1
 def at(self,s):self.step=s;self.k=0
 def check(self,v,lim,sub):
  bits=max(1,abs(v).bit_length())
  if sub.startswith('r'):self.max_raw=max(self.max_raw,bits)
  else:self.max_red=max(self.max_red,bits)
  if bits>lim:raise Refusal(f'{self.arm}.{self.phase}.{self.step}.{self.k}.{sub}',v,lim)
 def op(self,kind,a,b):
  a,b=F(a),F(b);self.k+=1
  if kind=='M':raw=[a.numerator*b.numerator,a.denominator*b.denominator];v=a*b
  elif kind=='A':raw=[a.numerator*b.denominator,b.numerator*a.denominator,a.numerator*b.denominator+b.numerator*a.denominator,a.denominator*b.denominator];v=a+b
  elif kind=='S':raw=[];v=2*a
  else:raise AssertionError(kind)
  for i,z in enumerate(raw,1):self.check(z,63,'r'+str(i))
  self.check(v.numerator,31,'e1');self.check(v.denominator,31,'e2');return v
 def tshift(self,c,t):
  c=c.copy();d=len(c)-1
  for j in range(d):
   for i in range(d-1,j-1,-1):c[i]=self.op('A',c[i],self.op('M',t,c[i+1]))
  return c
 def decas(self,b,t):
  b=b.copy();d=len(b)-1
  for r in range(1,d+1):
   for j in range(d-r+1):b[j]=self.op('A',b[j],self.op('M',t,self.op('A',b[j+1],-b[j])))
  return b[0]
# P1-P15, P1-P9 are covered by invocation02. Check BERN extra prep cannot refuse,
# independent of the absent name of each BERN invocation; no P event-name claim.
p=WidthTrace('B-Bezier','P');bern=[]
for n,a in enumerate(ps):
 p.at('UNNAMED_BERN_'+str(n));n=len(a)-1;b=[]
 for j in range(n+1):
  terms=[p.op('M',F(comb(j,i),comb(n,i)),a[i]) for i in range(j+1)]
  r=terms[0]
  for z in terms[1:]:r=p.op('A',r,z)
  b.append(r)
 bern.append(b)
# For prep successful bit-safety, collecting all terms before summing versus
# summing as each term arrives has identical scalar operations and all are small.
stages={}
for arm in ('B-Bezier','B-TS','C2'):
 records=[]
 for j,row in enumerate(old['cell_A']):
  x=F(*row['t']);w=WidthTrace(arm,'Q.q'+f'{j:02}');r={'q':j,'parameter':row['t']}
  try:
   if arm in ('B-Bezier','B-TS'):
    for n,a in enumerate(bern if arm=='B-Bezier' else ps,1):
     w.at('a'+str(n));v=w.decas(a,x) if arm=='B-Bezier' else w.tshift(a,x)[0]
     if n==5:s=v
    w.at('a8');w.op('M',s,s)
   else:
    jets=[]
    for n,key in enumerate(('U','V','x','y','S'),1):w.at('c'+str(n));jets.append(w.tshift(src(key),x))
    u,v,jx,jy,js=jets;s=js[1]
    w.at('c7');w.op('M',s,s);w.at('c8');m1=w.op('M',u[0],v[1]);w.at('c9');m2=w.op('M',u[1],v[0]);w.at('c10');n=w.op('A',m1,-m2);w.at('c11');w.op('S',n,2)
   r.update(status='OK',first_refusal=None)
  except Refusal as e:r.update(status='REFUSED',code='ARITH_LIMIT',first_refusal=e.event,failing_integer=e.value,limit_bits=e.bits)
  records.append(r)
 stages[arm]=records
vals={'schema':'QCG0-p0-contract-r2-remaining-CellA-width-stage-expectations-v1','pins':pins,'status':'PARTIAL_CERTIFICATE','W31_CellA_trace':stages,'B_Bezier_extra_preparation':{'status':'OK_NO_REFUSAL','largest_raw_bits':p.max_raw,'largest_reduced_bits':p.max_red,'stage_name':'UNSPECIFIED_IN_DRAFT; no failing prep stage exists in this fixture, so this does not obstruct the Q-stage proof'},'scope':'All remaining named CellA arithmetic routes, in addition to invocation02 B-Horner/B-PH/C1. Only width/refusal semantics, not outputs, counted-cost ledgers, memory, benchmarks, other tasks or full P0.','not_certified':'Sequential S1 and CellB nested composition stages remain underdetermined; no repaired event grammar invented.'}
blob=json.dumps(vals,sort_keys=True,indent=2)+'\n'
with out.open('x') as f:f.write(blob)
assert json.loads(out.read_text())==vals
for pth,h in pins.items():assert sha(base/pth)==h
print(json.dumps({'status':'COMPLETE','argv':sys.argv,'cwd':str(Path.cwd()),'script_sha256':sha(Path(__file__)),'expectation_sha256':sha(out),'bytes':len(blob),'refusals':{a:[r for r in rs if r['status']!='OK'] for a,rs in stages.items()},'BERN_extra_prep_raw_bits':p.max_raw,'BERN_extra_prep_red_bits':p.max_red,'elapsed_s':time.monotonic()-start,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'as_limit':resource.getrlimit(resource.RLIMIT_AS),'children':0}))
