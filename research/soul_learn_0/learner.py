"""Deterministic finite hypothesis elimination with explicit state and provenance."""
import copy
import json

# General candidates are supplied as the inductive bias, not as an answer.
HYPOTHESES = ('never', 'linked', 'fixed', 'linked_and_fixed')
def predict(h, x):
    if h=='never': return False
    if h=='linked': return x['linked']
    if h=='fixed': return x['fixed']
    if h=='linked_and_fixed': return x['linked'] and x['fixed']
    raise ValueError(h)

def initial():
    return {'observations': [], 'viable': list(HYPOTHESES), 'rejected': {}, 'active': None, 'status':'unknown'}

def observe(state, example):
    s=copy.deepcopy(state)
    if any(o['id']==example['id'] for o in s['observations']): raise ValueError('duplicate id')
    s['observations'].append(copy.deepcopy(example))
    for h in HYPOTHESES:
        if h in s['viable'] and predict(h,example)!=example['outcome']:
            s['viable'].remove(h); s['rejected'][h]=example['id']
    if not s['viable']: s['status']='unresolved'; s['active']=None
    else:
        s['status']='established' if len(s['viable'])==1 else 'unresolved'
        # Ordered simplicity bias, reported as provisional when >1 remain.
        s['active']=s['viable'][0]
    return s

def infer(state, case):
    if state['active'] is None: return {'answer':None,'status':state['status'],'hypothesis':None}
    return {'answer':predict(state['active'],case), 'status':state['status'], 'hypothesis':state['active']}

def recall(state, ident):
    return next((x['outcome'] for x in state['observations'] if x['id']==ident), None)

def serialize(state): return json.dumps(state,sort_keys=True,separators=(',',':'))
def load(data):
    state=json.loads(data)
    if set(state['viable']) | set(state['rejected']) != set(HYPOTHESES) or set(state['viable']) & set(state['rejected']): raise ValueError('invalid hypothesis state')
    return state
