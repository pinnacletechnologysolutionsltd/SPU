"""Registered agent streams and evaluator-only ground truth; no calibration use."""
def fact(id,key,value,epoch=0,strength=1):
    return {'id':id,'kind':'fact','key':key,'value':value,'epoch':epoch,'strength':strength}
def rev(id,key,target): return {'id':id,'kind':'revoke','key':key,'target':target}
def task(key, expected, epoch=None, kind='current'):
    return {'key':key,'epoch':epoch,'expected':expected,'kind':kind}
SCENARIOS=[
 {'id':'S1_stable','world':'key remains in box; light remains on',
  'stream':[fact('a','key','box'),fact('b','light','on')],
  'queries':[task('key','box'),task('light','on')]},
 {'id':'S2_revocation','world':'valid alternative red, later blue source revoked',
  'stream':[fact('a','ball','red',0,1),fact('b','ball','blue',0,2),rev('r','ball','b')],
  'queries':[task('ball','red')]},
 {'id':'S3_revisions','world':'successive label corrections; latest source revoked',
  'stream':[fact('a','item','red',0,1),fact('b','item','blue',0,2),fact('c','item','green',0,3),rev('r','item','c')],
  'queries':[task('item','blue')]},
 {'id':'S4_history','world':'door closed at epoch 0, open at epoch 1',
  'stream':[fact('a','door','closed',0),fact('b','door','open',1)],
  'queries':[task('door','open'),task('door','closed',0,'history')]},
 {'id':'S5_pressure','world':'first record later queried among unrelated records',
  'stream':[fact('a','parcel','depot')]+[fact('d'+str(i),'noise'+str(i),'v'+str(i)) for i in range(8)],
  'queries':[task('parcel','depot'),task('noise7','v7')]},
]
