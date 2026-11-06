"""Registered four-way trial; writes artifacts only to a supplied scratch path."""
import copy
import json
import os
import sys
from engines import EngineA, EngineB
from model import checkpoint, digest, new_state, validate
from scenarios import PRE, CONTINUE, TRUTH

def prepare():
    state = new_state()
    for o in PRE: EngineA().ingest(state, o)
    return state

def summary(state):
    # Bounded factual summary: up to 20 current beliefs, ordered by original
    # observation sequence, plus the standing goal. Does not copy source history.
    s = new_state()
    index = {o['id']: o for o in state['observations']}
    for i, b in enumerate([x for x in state['beliefs'] if x['status'] == 'current'][:20], 1):
        source = index[b['evidence'][0]]
        o = {'id': 'summary-' + str(i), 'seq': source['seq'], 'key': b['key'], 'value': b['value'],
             'strength': 'strong', 'kind': 'fact', 'reason': 'summary', 'source': 'compacted-state'}
        EngineB().ingest(s, o)
    return s

def answers(engine, state):
    return {'persistent': engine.answer(state, ['inside', 'key']),
            'colour': engine.answer(state, ['colour', 'ball']),
            'door': engine.answer(state, ['door', 'gate']),
            'unknown': engine.answer(state, ['colour', 'coin']),
            'transfer': engine.transfer(state, 'pearl')}

def run():
    original = prepare()
    cp = checkpoint(original, 'lineage-1', 'pre', None, EngineA.name)
    assert validate(cp, None)
    migrated = json.loads(json.dumps(cp, sort_keys=True, separators=(',', ':')))
    if not validate(migrated, None):
        raise ValueError('checkpoint failed validation')
    results = {}
    final_states = {}
    for name, engine, state in [('C0', EngineA(), copy.deepcopy(original)),
                                ('C1', EngineB(), copy.deepcopy(migrated['body']['state'])),
                                ('C2', EngineB(), summary(original)),
                                ('C3', EngineB(), new_state())]:
        for o in CONTINUE: engine.ingest(state, o)
        a = answers(engine, state)
        obsids = {o['id'] for o in state['observations']}
        bs = state['beliefs']
        results[name] = {'answers': a,
            'historical_recall': sum(i in obsids for i in ['o1','o2','o3','o4','o5','o6','o7','o8']) / 8,
            'relationship_accuracy': sum(a[k] == TRUTH[k] for k in ['persistent','colour','door']) / 3,
            'revision_correctness': int(any(b['id'] == 'b-o2' and b['status'] == 'superseded' for b in bs) and any(b['id'] == 'b-o3' and b['supersedes'] == 'b-o2' for b in bs)),
            'change_history': int(any(b['id'] == 'b-o4' and b['status'] == 'superseded' for b in bs) and any(b['id'] == 'b-o5' and b['reason'] == 'world-changed-after-o4' for b in bs)),
            'provenance_integrity': sum(i in obsids and next(o for o in state['observations'] if o['id'] == i)['source'] == 'sensor:' + i for i in ['o1','o2','o3','o4','o5','o6','o7','o8']) / 8,
            'unknown_calibration': int(a['unknown'] == TRUTH['unknown']),
            'transfer_performance': int(a['transfer'] == TRUTH['transfer']),
            'state_integrity': validate(checkpoint(state, 'lineage-1', name, cp['digest'], engine.name), cp['digest'])}
        final_states[name] = state
    # Migration is exact serialization/deserialization, not representation translation.
    migration = {'source_engine': EngineA.name, 'destination_engine': EngineB.name,
        'source_representation': 'soul-state-1', 'destination_representation': 'soul-state-1',
        'procedure': 'canonical JSON serialization and load; no translation',
        'input_digest': cp['digest'], 'output_digest': migrated['digest'],
        'intentionally_omitted': [], 'untranslatable': [],
        'missing_or_altered': int(migrated['body']['state'] != original),
        'validated': validate(migrated, None)}
    # Mutations each touch only the copied fixture and do not block valid data.
    missing = copy.deepcopy(original); missing['beliefs'] = [b for b in missing['beliefs'] if b['id'] != 'b-o1']
    changed = copy.deepcopy(cp); changed['body']['state']['beliefs'][0]['evidence'] = ['o2']
    digest_control = not validate(changed, None)
    changed['digest'] = digest(changed['body'])
    reference_control = not validate(changed, None)
    child = checkpoint(original, 'lineage-1', 'child', cp['digest'], EngineB.name)
    wrong_predecessor = not validate(child, 'incorrect-predecessor')
    controls = {'necessary_relationship_removed_detected': EngineB().answer(missing, ['inside','key']) == 'unknown',
                'altered_reference_digest_detected': digest_control,
                'altered_reference_rehashed_detected': reference_control,
                'incorrect_predecessor_detected': wrong_predecessor,
                'unresolved_contradiction_abstains': EngineB().answer(original, ['colour','coin']) == 'unknown',
                'unknown_not_established': EngineB().answer(original, ['inside','unseen']) == 'unknown',
                'valid_checkpoint_usable': validate(cp, None) and EngineB().answer(original, ['inside','key']) == 'box'}
    forks=[]
    for name, val in [('fork-left','north'), ('fork-right','south')]:
        s=copy.deepcopy(original)
        EngineB().ingest(s, {'id':name, 'seq':9, 'key':['location','traveller'], 'value':val,
            'strength':'strong', 'kind':'fact', 'reason':'observation', 'source':'sensor:'+name})
        forks.append(checkpoint(s, 'lineage-1', name, cp['digest'], EngineB.name))
    fork_ok = all(validate(f, cp['digest']) for f in forks) and forks[0]['digest'] != forks[1]['digest'] and all(f['body']['predecessor'] == cp['digest'] for f in forks)
    return {'results': results, 'migration': migration, 'controls': controls, 'fork_valid': fork_ok}, cp, migrated, forks, final_states

def main(path):
    os.makedirs(path, exist_ok=True)
    report, cp, migrated, forks, states = run()
    for name, obj in [('results.json',report), ('checkpoint.json',cp), ('migration-output.json',migrated), ('forks.json',forks), ('final-states.json',states)]:
        with open(os.path.join(path,name),'w') as f: json.dump(obj,f,indent=2,sort_keys=True); f.write('\n')
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == '__main__': main(sys.argv[1])
