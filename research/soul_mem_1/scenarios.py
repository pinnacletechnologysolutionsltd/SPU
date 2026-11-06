"""Registered streams and evaluator-only expectations; no random input."""
def fact(i, key, value, epoch=0, strength=2, source='sensor'):
    return {'id': i, 'kind': 'fact', 'key': key, 'value': value, 'epoch': epoch, 'strength': strength, 'source': source}
def revoke(i, key, target):
    return {'id': i, 'kind': 'revoke', 'key': key, 'target': target}
def q(key, expected, kind='current', relevant=(), epoch=None):
    return {'key': key, 'kind': kind, 'epoch': epoch, 'expected': expected, 'relevant': list(relevant)}
# Expectations and relevance are evaluator-only. Agents receive records and the
# query stripped of expected/relevant. Source strengths are supplied assumptions.
SCENARIOS = [
 {'id':'S1_stable', 'world':'key remains in box', 'records':[fact('a','key','box'),fact('d1','lamp','on'),fact('d2','leaf','green')],
  'queries':[q('key','box',relevant=['a'])]},
 {'id':'S2_correction', 'world':'ball is red; initial blue sensor later invalidated',
  'records':[fact('a','ball','blue',strength=3,source='faulty'),fact('b','ball','red',strength=2,source='trusted'),revoke('r','ball','a'),fact('d1','lamp','on'),fact('d2','leaf','green')],
  'queries':[q('ball','red',relevant=['a','b','r'])]},
 {'id':'S3_change', 'world':'gate closed at epoch 0, open at epoch 1',
  'records':[fact('a','gate','closed',0),fact('b','gate','open',1),fact('d1','lamp','on'),fact('d2','leaf','green')],
  'queries':[q('gate','open',relevant=['a','b']),q('gate','closed','history',['a'],0)]},
 {'id':'S4_conflict', 'world':'marker is red; strong source outranks two weak conflicting sensors',
  'records':[fact('a','marker','red',strength=3,source='calibrated'),fact('b','marker','blue',strength=1,source='weak1'),fact('c','marker','blue',strength=1,source='weak2'),fact('d1','lamp','on')],
  'queries':[q('marker','red',relevant=['a','b','c'])]},
 {'id':'S5_transfer', 'world':'learned containment rule applies to pearl in bag in chest',
  'records':[fact('ex1','example_chain_1','valid'),fact('ex2','example_chain_2','valid'),fact('a','rule','transitive',source='supplied_rule'),fact('b','pearl','bag'),fact('c','bag','chest'),fact('d1','lamp','on')],
  'queries':[q('pearl','chest','transfer',['a','b','c'])]},
 {'id':'S6_reactivation', 'world':'parcel is at depot; latest higher-priority report invalidated',
  'records':[fact('a','parcel','depot',strength=2,source='witness'),fact('b','parcel','port',strength=3,source='bad_sensor'),revoke('r','parcel','b'),fact('d1','lamp','on'),fact('d2','leaf','green')],
  'queries':[q('parcel','depot',relevant=['a','b','r'])]},
]
