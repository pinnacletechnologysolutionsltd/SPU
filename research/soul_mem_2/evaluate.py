"""Frozen comparison; evaluator metadata never enters the memory state."""
import copy
import json
import os
import sys
from memory import empty, ingest, items, query, size, index_valid
from support import check
from scenarios import SCENARIOS, fact, rev
BUDGETS={'small':239,'medium':431,'large':815}

def trial(s,p,b):
    state=empty(p); events=[]; peak=size(state); peak_transient=0; total_ops=0
    if peak>b:
        return {'scenario':s['id'],'policy':p,'budget':b,'status':'INFEASIBLE_BUDGET','initial_size':peak,'updates':[],'queries':[]}
    for event in s['stream']:
        state,report=ingest(state,event,b)
        report['incoming']=event['id']; report['retained']=[r['id'] for r in items(state)]
        report['state']=copy.deepcopy(state)
        events.append(report); peak=max(peak,report['occupancy']); peak_transient=max(peak_transient,report['transient_bytes']); total_ops+=report['ops']
        assert size(state)<=b and index_valid(state)
        if report['status']!='OK': break
    outcomes=[]
    for t in s['queries']:
        # Only key/epoch is passed into the memory policy; expected is evaluator-only.
        result=query(state,t['key'],t['epoch'])
        retained=items(state)
        claim=None if result['answer']=='unknown' else (t['key'],result['answer'], t['epoch'] if t['epoch'] is not None else next(r['epoch'] for r in retained if r['id']==result['refs'][0]))
        support=check(claim,result['refs'],retained)
        outcomes.append({'kind':t['kind'],'key':t['key'],'expected':t['expected'],**result,
            'support':support,'correct':result['answer']==t['expected'],
            'appropriate_abstention':result['answer']=='unknown' and not any(r['kind']=='fact' and r['key']==t['key'] and (t['epoch'] is None or r['epoch']==t['epoch']) for r in retained),
            'unjustified_certainty':result['answer']!='unknown' and support!='SUPPORTED'})
    retained_ids={r['id'] for r in items(state)}
    return {'scenario':s['id'],'policy':p,'budget':b,'status':'OK', 'initial_size':size(empty(p)),
        'updates':events,'final_state':state,'persistent_bytes':size(state),'peak_persistent_bytes':peak,
        'peak_temporary_serialized_estimate':peak_transient,'ingest_ops':total_ops,'queries':outcomes,
        'not_recoverable_ids':[r['id'] for r in s['stream'] if r['id'] not in retained_ids]}

def controls():
    def build(p,records,b=10000):
        s=empty(p)
        for r in records:s,_=ingest(s,r,b)
        return s
    a=fact('a','ball','red'); b=fact('b','ball','blue',0,2)
    valid=build('M0',[a]); missing=build('M1',[]); revoked=build('M0',[a,rev('r','ball','a')])
    archive=build('M2',[a,b]); corrupt=copy.deepcopy(archive);corrupt['index']['ball']=[99]
    normal=query(archive,'ball'); disabled=query(archive,'ball',retrieval_enabled=False)
    wrong=copy.deepcopy(archive); wrong['archive'].pop(0)
    baseline=empty('M0'); too_small=size(baseline)-1
    unchanged,refused=ingest(baseline,a,too_small)
    capped,report=ingest(empty('M0'),a,size(empty('M0')))
    mismatch=check(('ball','red',0),['b'],[a,b])
    chain=[fact('x','A','B'),fact('y','B','C')]
    return {'valid_summary':query(valid,'ball')['answer']=='red',
      'missing_history_unknown':query(missing,'ball')['answer']=='unknown',
      'revoked_not_certain':query(revoked,'ball')['answer']=='unknown',
      'false_reference_unsupported':mismatch=='UNSUPPORTED',
      'transitive_supported':check(('A','C',0),['x','y'],chain,('transitive',))=='SUPPORTED',
      'transitive_missing_rule_unknown':check(('A','C',0),['x','y'],chain,())=='UNKNOWN',
      'disabled_retrieval_changes_result':normal['answer']=='blue' and disabled['answer']=='unknown',
      'incorrect_eviction_detected':not index_valid(wrong),
      'infeasible_budget':refused['status']=='INFEASIBLE_BUDGET' and unchanged==baseline,
      'overflow_evicts_under_budget':size(capped)<=size(empty('M0')) and len(report['discarded'])==1,
      'index_corruption_detected':not index_valid(corrupt),
      'valid_archive_index_usable':index_valid(archive) and normal['answer']=='blue'}

def main(path):
    os.makedirs(path,exist_ok=True)
    report={'budgets':BUDGETS,'registered_scenarios':SCENARIOS,'controls':controls(),
            'trials':[trial(s,p,b) for s in SCENARIOS for p in ('M0','M1','M2') for b in BUDGETS.values()]}
    with open(os.path.join(path,'results.json'),'w') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
    print('trials:',len(report['trials']),'controls:',sum(report['controls'].values()),'/',len(report['controls']))
if __name__=='__main__':main(sys.argv[1])
