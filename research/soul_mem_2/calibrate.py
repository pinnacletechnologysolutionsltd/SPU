"""Separate pre-registration calibration; no registered scenarios imported."""
import json
import sys
from memory import empty, ingest, size

def main(path):
    states={p:empty(p) for p in ('M0','M1','M2')}; samples={}
    for i in range(8):
        record={'id':f'cal{i}','kind':'fact','key':f'k{i}','value':f'v{i}','epoch':0,'strength':1}
        for p in states: states[p],_=ingest(states[p],record,1000000)
        if i+1 in (2,4,8): samples[str(i+1)]={p:size(s) for p,s in states.items()}
    budgets={name:max(samples[n].values()) for name,n in [('small','2'),('medium','4'),('large','8')]}
    with open(path,'w') as f: json.dump({'samples':samples,'budgets':budgets,'rule':'maximum policy state size after 2, 4, and 8 unique calibration records'},f,sort_keys=True,indent=2);f.write('\n')
    print(budgets)
if __name__=='__main__':main(sys.argv[1])
