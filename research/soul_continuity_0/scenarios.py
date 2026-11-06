"""Registered deterministic observations and evaluator-only answer key."""
def obs(id, seq, key, value, strength='strong', reason='observation'):
    return {'id': id, 'seq': seq, 'key': key, 'value': value, 'strength': strength,
            'kind': 'fact', 'reason': reason, 'source': 'sensor:' + id}

# The blue reading is erroneous; the signed correction reports the same time.
# The door's observation is correct at each of two distinct times.
PRE = [
    obs('o1', 1, ['inside', 'key'], 'box'),
    obs('o2', 2, ['colour', 'ball'], 'blue'),
    obs('o3', 3, ['colour', 'ball'], 'red', reason='correction-of-o2'),
    obs('o4', 4, ['door', 'gate'], 'closed'),
    obs('o5', 5, ['door', 'gate'], 'open', reason='world-changed-after-o4'),
    obs('o6', 6, ['rule', 'inside_transitive'], 'yes'),
    obs('o7', 7, ['colour', 'coin'], 'gold', strength='weak'),
    obs('o8', 8, ['colour', 'coin'], 'silver', strength='weak'),
]
CONTINUE = [obs('o9', 9, ['inside', 'pearl'], 'bag'), obs('o10', 10, ['inside', 'bag'], 'chest')]
# Ground truth is used by the evaluator only, never passed to the engines.
TRUTH = {'persistent': 'box', 'colour': 'red', 'door': 'open', 'unknown': 'unknown', 'transfer': 'chest'}
