"""Registered evaluation; resource accounting is per query and per occurrence."""
import copy
import json
import os
import sys
from memory import Memory, archive_digest, valid_archive
from scenarios import SCENARIOS, fact, revoke

def run_scenario(s, policy):
    mem = Memory(policy)
    for record in s['records']: mem.ingest(record)
    out = []
    for query in s['queries']:
        before = (len(mem.read_ids), mem.read_bytes, mem.index_bytes, mem.ops)
        visible = {k: query[k] for k in ('key','kind','epoch')}
        value, source = mem.answer(visible)
        ids = mem.read_ids[before[0]:]
        relevant = set(query['relevant']) # evaluator-only relevance oracle
        hits = sum(i in relevant for i in ids)
        out.append({'query': visible, 'answer': value, 'expected': query['expected'],
            'correct': value == query['expected'], 'source_id': source,
            'source_attribution_correct': source in relevant if source is not None else None,
            'unjustified_certainty': value not in ('unknown', query['expected']),
            'archived_records_accessed': len(ids), 'archive_record_ids': ids,
            'archive_bytes': mem.read_bytes-before[1], 'index_bytes': mem.index_bytes-before[2],
            'operations': mem.ops-before[3], 'relevant_accesses': hits,
            'retrieval_precision': hits/len(ids) if ids else None})
    return {'scenario':s['id'], 'policy':policy, 'queries':out,
            'persistent_bytes':mem.storage(), 'persistent_archive_records':len(mem.archive),
            'summary_keys':len(mem.summary), 'ingest_operations':mem.ingest_ops}

def controls():
    s = next(x for x in SCENARIOS if x['id'].startswith('S6'))
    healthy=run_scenario(s,'M2')['queries'][0]
    missing=copy.deepcopy(s); missing['records']=[r for r in missing['records'] if r['id']!='a']
    missing_result=run_scenario(missing,'M2')['queries'][0]
    corrupted=copy.deepcopy(s['records']); trusted=archive_digest(corrupted)
    corrupted[2]['target']='d1'
    raw_detect = not valid_archive(corrupted,trusted)
    semantic_detect = not valid_archive(corrupted,archive_digest(corrupted))
    disabled = Memory('M2', trigger=False)
    for r in s['records']: disabled.ingest(r)
    disabled_answer=disabled.answer({'key':'parcel','kind':'current','epoch':None})[0]
    stable=run_scenario(SCENARIOS[0],'M2')['queries'][0]
    conflict=run_scenario(next(x for x in SCENARIOS if x['id'].startswith('S4')),'M2')['queries'][0]
    return {'irrelevant_history_not_retrieved': all(i in {'a','b','r'} for i in healthy['archive_record_ids']),
      'missing_critical_evidence_abstains':missing_result['answer']=='unknown',
      'misleading_evidence_outweighed': conflict['answer']=='red',
      'summary_sufficient_no_retrieval': stable['answer']=='box' and stable['archived_records_accessed']==0,
      'provenance_alteration_digest_detected':raw_detect,
      'provenance_alteration_semantic_detected':semantic_detect,
      'valid_provenance_accepted':valid_archive(s['records'],trusted),
      'disabled_trigger_loses_retrieval_and_answer': disabled_answer=='unknown' and not disabled.read_ids and healthy['answer']=='depot'}

def main(path):
    os.makedirs(path,exist_ok=True)
    results = [run_scenario(s,p) for s in SCENARIOS for p in ('M0','M1','M2')]
    output={'runs':results,'controls':controls(), 'registered_scenarios':SCENARIOS}
    with open(os.path.join(path,'results.json'),'w') as f: json.dump(output,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(output,sort_keys=True,indent=2))
if __name__ == '__main__': main(sys.argv[1])
