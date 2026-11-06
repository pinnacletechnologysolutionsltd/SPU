"""Two independently coded deterministic interpreters over a common state."""
from model import observe

class EngineA:
    name = 'A-event-scan-1'
    def ingest(self, state, obs):
        observe(state, obs)
        if obs['kind'] != 'fact' or obs['strength'] != 'strong':
            return
        previous = [b for b in state['beliefs'] if b['key'] == obs['key'] and b['status'] == 'current']
        for b in previous:
            b['status'] = 'superseded'
        state['beliefs'].append({'id': 'b-' + obs['id'], 'key': obs['key'], 'value': obs['value'],
            'evidence': [obs['id']], 'status': 'current', 'supersedes': previous[-1]['id'] if previous else None,
            'reason': obs['reason']})
    def answer(self, state, key):
        matches = [b for b in state['beliefs'] if b['key'] == key and b['status'] == 'current']
        weak = [o for o in state['observations'] if o['key'] == key and o['strength'] == 'weak']
        if not matches or any(o['value'] != matches[-1]['value'] and o['seq'] > self._sequence(state, matches[-1]) for o in weak):
            return 'unknown'
        return matches[-1]['value']
    @staticmethod
    def _sequence(state, belief):
        return next(o['seq'] for o in state['observations'] if o['id'] == belief['evidence'][0])
    def transfer(self, state, subject):
        if self.answer(state, ['rule', 'inside_transitive']) != 'yes': return 'unknown'
        middle = self.answer(state, ['inside', subject])
        return 'unknown' if middle == 'unknown' else self.answer(state, ['inside', middle])

class EngineB:
    name = 'B-index-fold-1'
    def ingest(self, state, obs):
        observe(state, obs)
        if obs['kind'] != 'fact' or obs['strength'] != 'strong': return
        old = None
        for b in reversed(state['beliefs']):
            if b['key'] == obs['key'] and b['status'] == 'current':
                old = b
                break
        if old is not None: old['status'] = 'superseded'
        state['beliefs'].append({'id': 'b-' + obs['id'], 'key': list(obs['key']), 'value': obs['value'],
            'evidence': [obs['id']], 'status': 'current', 'supersedes': old['id'] if old else None,
            'reason': obs['reason']})
    def answer(self, state, key):
        index = {}
        for b in state['beliefs']:
            if b['status'] == 'current': index[tuple(b['key'])] = b
        b = index.get(tuple(key))
        if b is None: return 'unknown'
        seqs = {o['id']: o['seq'] for o in state['observations']}
        for o in state['observations']:
            if o['key'] == key and o['strength'] == 'weak' and o['seq'] > seqs[b['evidence'][0]] and o['value'] != b['value']:
                return 'unknown'
        return b['value']
    def transfer(self, state, subject):
        facts = {}
        for b in state['beliefs']:
            if b['status'] == 'current' and self.answer(state, b['key']) != 'unknown': facts[tuple(b['key'])] = b['value']
        if facts.get(('rule', 'inside_transitive')) != 'yes': return 'unknown'
        return facts.get(('inside', facts.get(('inside', subject))), 'unknown')
