from pprint import pprint
from research.qaf_expr_graph_0.model import normal
from research.qaf_expr_graph_1.model import ORIGINAL, IDENTITY, CONJ_MUL, NORM, HIGH, compare

for name,left,right,x,status in [
    ('small cancellation',ORIGINAL,IDENTITY,(3,-2),0),
    ('overflow cancellation',ORIGINAL,IDENTITY,(HIGH,0),0),
    ('conjugate vs norm',CONJ_MUL,NORM,(1,2),0),
    ('initial status negative control',ORIGINAL,IDENTITY,(1,0),2),
]:
    c=compare(left,right,x,status)
    print('\n',name,'x=',x,'initial_status=',status)
    print('normal form left=',normal(left.root),'right=',normal(right.root))
    print('observer decisions=',c['permitted_in_fixture'])
    for side in ('left','right'):
        tr=c[side]
        print(side,'result=',tr['result'],'status=',tr['status'])
        for e in tr['events']:
            print(' ',e['op'],'exact=',e['exact'],'bits=',e['bits'],
                  'status=',e['status'],'write=',e['write'],'retire=',e['retire'])
