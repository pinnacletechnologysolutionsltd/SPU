"""Append-only toy state, canonical checkpoints and bounded integrity checks."""
import copy
import hashlib
import json

SCHEMA = 'soul-state-1'

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

def new_state():
    return {'observations': [], 'beliefs': [], 'goals': ['answer only with evidence']}

def observe(state, obs):
    if any(x['id'] == obs['id'] for x in state['observations']):
        raise ValueError('duplicate observation')
    state['observations'].append(copy.deepcopy(obs))

def checkpoint(state, lineage, ident, predecessor, engine):
    body = {'schema': SCHEMA, 'lineage': lineage, 'id': ident,
            'predecessor': predecessor, 'engine': engine, 'state': copy.deepcopy(state)}
    return {'body': body, 'digest': digest(body)}

def validate(cp, expected_predecessor):
    body = cp['body']
    if cp['digest'] != digest(body) or body['schema'] != SCHEMA:
        return False
    if body['predecessor'] != expected_predecessor:
        return False
    observations = body['state']['observations']
    by_id = {o['id']: o for o in observations}
    if len(by_id) != len(observations):
        return False
    for belief in body['state']['beliefs']:
        refs = belief['evidence']
        if not refs or any(r not in by_id for r in refs):
            return False
        # Each cited observation must actually concern this exact proposition.
        if any(by_id[r]['key'] != belief['key'] or by_id[r]['value'] != belief['value'] for r in refs):
            return False
        if belief['supersedes'] is not None and belief['supersedes'] not in {b['id'] for b in body['state']['beliefs']}:
            return False
    return True
