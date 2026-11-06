"""Fixed summary, scan and indexed retrieval policies. No evaluator truth."""
import copy
import json

def size(obj):
    return len(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode())

def choose(records, revoked, epoch=None):
    """Highest epoch then strength; equally strong distinct values abstain."""
    fs = [r for r in records if r['kind'] == 'fact' and r['id'] not in revoked and (epoch is None or r['epoch'] == epoch)]
    if not fs: return ('unknown', None)
    highest_epoch = max(r['epoch'] for r in fs)
    fs = [r for r in fs if r['epoch'] == highest_epoch]
    strength = max(r['strength'] for r in fs)
    fs = [r for r in fs if r['strength'] == strength]
    if len({r['value'] for r in fs}) != 1: return ('unknown', None)
    return (fs[-1]['value'], fs[-1]['id'])

class Memory:
    def __init__(self, policy, trigger=True):
        self.policy, self.trigger = policy, trigger
        self.summary = {} # one accepted candidate per key, or unresolved
        self.revoked = set()
        self.archive = []
        self.index = {}
        self.ingest_ops = 0
        self.read_ids = []
        self.read_bytes = self.index_bytes = self.ops = 0
    def ingest(self, record):
        r = copy.deepcopy(record); self.ingest_ops += 1
        if self.policy != 'M0':
            self.archive.append(r)
            if self.policy == 'M2':
                self.index.setdefault(r['key'], []).append(len(self.archive)-1)
                self.ingest_ops += 1
        key = r['key']
        if r['kind'] == 'revoke':
            self.revoked.add(r['target'])
            if self.summary.get(key, {}).get('id') == r['target']:
                self.summary[key] = {'id': None, 'dirty': True}
        else:
            prior = self.summary.get(key)
            if prior is None or prior.get('id') is None:
                self.summary[key] = r
            else:
                val, _ = choose([prior, r], self.revoked)
                if val == 'unknown': self.summary[key] = {'id': None, 'dirty': False}
                elif val == r['value'] and (r['epoch'], r['strength']) >= (prior['epoch'], prior['strength']): self.summary[key] = r
    def get(self, key, history=False, epoch=None):
        entry = self.summary.get(key)
        dirty = entry is not None and entry.get('dirty', False)
        retrieve = self.policy == 'M1' or (self.policy == 'M2' and self.trigger and (history or dirty))
        self.ops += 1
        if retrieve:
            if self.policy == 'M1':
                indexes = range(len(self.archive))
            else:
                indexes = self.index.get(key, [])
                # Explicit index lookup: count canonical key and posting-list bytes.
                self.index_bytes += size({'key':key, 'postings':indexes})
                self.ops += 1
            matching = []
            for i in indexes:
                r = self.archive[i]
                self.read_ids.append(r['id']); self.read_bytes += size(r); self.ops += 1
                if r['key'] == key: matching.append(r)
            return choose(matching, self.revoked, epoch if history else None)
        if history or entry is None or entry.get('id') is None: return ('unknown', None)
        return (entry['value'], entry['id'])
    def answer(self, query):
        if query['kind'] == 'transfer':
            rule, _ = self.get('rule')
            middle, _ = self.get(query['key'])
            end, evidence = self.get(middle) if middle != 'unknown' else ('unknown', None)
            return (end, evidence) if rule == 'transitive' else ('unknown', None)
        return self.get(query['key'], query['kind'] == 'history', query.get('epoch'))
    def storage(self):
        body = {'summary': self.summary, 'revoked': sorted(self.revoked)}
        if self.policy != 'M0': body['archive'] = self.archive
        if self.policy == 'M2': body['index'] = self.index
        return size(body)

def archive_digest(records):
    import hashlib
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def valid_archive(records, trusted_digest):
    if archive_digest(records) != trusted_digest: return False
    seen = {}
    for r in records:
        if r['id'] in seen: return False
        if r['kind'] == 'revoke' and (r['target'] not in seen or seen[r['target']]['key'] != r['key']): return False
        seen[r['id']] = r
    return True
