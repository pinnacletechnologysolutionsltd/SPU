"""Budgeted deterministic memory. Complete decision state is JSON serializable."""
import copy
import json

def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def size(obj): return len(encode(obj))

def empty(policy):
    if policy == 'M0': return {'kind':policy, 'candidates':[]}
    if policy == 'M1': return {'kind':policy, 'archive':[]}
    return {'kind':policy, 'archive':[], 'index':{}, 'summary':{}}

def items(state): return state['candidates'] if state['kind']=='M0' else state['archive']

def rebuild(state):
    if state['kind'] != 'M2': return
    index={}; summary={}
    for i,r in enumerate(state['archive']):
        index.setdefault(r['key'], []).append(i)
        if r['kind']=='fact': summary[r['key']] = r['id']
    state['index']=index; state['summary']=summary

def index_valid(state):
    if state['kind'] != 'M2': return True
    expected=copy.deepcopy(state); rebuild(expected)
    return state['index']==expected['index'] and state['summary']==expected['summary']

def ingest(state, record, budget):
    """Transaction: remove revoked facts; cap M0 alternatives; evict oldest.

    Revocations physically invalidate the target in all policies before an
    optional historical tombstone is retained. This avoids stale certainty even
    if the tombstone must be evicted. Fixture IDs are globally unique.
    """
    if size(state)>budget: return copy.deepcopy(state), {'status':'INFEASIBLE_BUDGET','discarded':[], 'occupancy':size(state), 'transient_bytes':0,'ops':0}
    s=copy.deepcopy(state); rec=copy.deepcopy(record); data=items(s)
    removed=[]; ops=1
    if rec['kind']=='revoke':
        for r in data[:]:
            if r['kind']=='fact' and r['id']==rec['target']:
                data.remove(r); removed.append({'id':r['id'],'reason':'revoked','record':r}); ops+=1
        if s['kind']!='M0': data.append(rec)
    else:
        data.append(rec)
        if s['kind']=='M0':
            same=[r for r in data if r['key']==rec['key']]
            while len(same)>3:
                old=same.pop(0); data.remove(old); removed.append({'id':old['id'],'reason':'candidate_cap','record':old}); ops+=1
    rebuild(s); ops+=len(data) if s['kind']=='M2' else 0
    transient=size(s)
    while size(s)>budget and data:
        old=data.pop(0); removed.append({'id':old['id'],'reason':'budget_eviction','record':old}); ops+=1
        rebuild(s); ops+=len(data) if s['kind']=='M2' else 0
    if size(s)>budget:
        return copy.deepcopy(state), {'status':'REFUSED_UPDATE','discarded':[], 'occupancy':size(state), 'transient_bytes':transient,'ops':ops}
    return s, {'status':'OK','discarded':removed,'occupancy':size(s),'transient_bytes':transient,'ops':ops}

def query(state, key, epoch=None, retrieval_enabled=True):
    """Same latest-epoch then strength rule; M2 indexes, M1 scans, M0 scans candidates."""
    data=items(state); visits=[]; index_ops=0; index_bytes=0
    if state['kind']=='M2' and not retrieval_enabled:
        return {'answer':'unknown','refs':[],'status':'RETRIEVAL_DISABLED','visits':[], 'logical_bytes':0,'index_ops':0,'validation_visits':0,'validation_bytes':0,'ops':1,'transient_bytes':0}
    validation_bytes=0; validation_visits=0
    if state['kind']=='M2':
        validation_visits=len(data); validation_bytes=sum(size(r) for r in data)+size(state['index'])+size(state['summary'])
        if not index_valid(state): return {'answer':'unknown','refs':[],'status':'INDEX_INVALID','visits':[], 'logical_bytes':0,'index_ops':0,'ops':0,'transient_bytes':0}
        ids=state['index'].get(key,[]); index_ops=1
        index_bytes=size({'key':key,'offsets':ids})
    else: ids=range(len(data))
    candidates=[]
    for i in ids:
        r=data[i]; visits.append(r)
        if r['kind']=='fact' and r['key']==key and (epoch is None or r['epoch']==epoch): candidates.append(r)
    if not candidates: answer='unknown'; refs=[]
    else:
        rank=max((r['epoch'],r['strength']) for r in candidates)
        winners=[r for r in candidates if (r['epoch'],r['strength'])==rank]
        if len({r['value'] for r in winners})>1: answer='unknown'; refs=[]
        else: answer=winners[-1]['value']; refs=[winners[-1]['id']]
    return {'answer':answer,'refs':refs,'status':'OK','visits':[r['id'] for r in visits],
            'logical_bytes':sum(size(r) for r in visits)+index_bytes+validation_bytes,'index_ops':index_ops,
            'validation_visits':validation_visits,'validation_bytes':validation_bytes,
            'ops':1+index_ops+len(visits)+validation_visits,'transient_bytes':size(candidates)+index_bytes+validation_bytes}
