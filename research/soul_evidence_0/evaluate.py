import json
import os
import sys
from checker import check
from scenarios import fixtures

def run():
    results=[]
    for f in fixtures():
        result=check(f['claim'],f['records'],f['language'],f['rules'],f['trusted_manifest'],f['trusted_anchor'])
        results.append({'name':f['name'],'input':{k:v for k,v in f.items() if k not in ('expected','finding')},
          'expected':f['expected'],'expected_finding':f['finding'],'result':result,
          'pass':result['verdict']==f['expected'] and (f['finding'] is None or result.get('finding')==f['finding'])})
    return {'cases':results,'passed':sum(r['pass'] for r in results),'total':len(results),
      'prediction_accuracy_control':{'derived_prediction':True,'observed_outcome':False,'empirically_correct':False}}

def main(path):
    os.makedirs(path,exist_ok=True);result=run()
    with open(os.path.join(path,'results.json'),'w') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print('cases',result['passed'],'/',result['total'])
if __name__=='__main__':main(sys.argv[1])
