"""A deliberately untrusted finite-hypothesis learner and claim producer."""
LANG={'version':'h1','candidates':{'never':'0','linked':'L','fixed':'F','linked_and_fixed':'L&F'}}
RULES={'version':'r1','predicates':['linked','fixed'],'inference':['direct','transitive']}

def predicts(name, row):
    return {'never':False,'linked':row['linked'],'fixed':row['fixed'],
            'linked_and_fixed':row['linked'] and row['fixed']}[name]

def train(rows):
    return [h for h in LANG['candidates'] if all(predicts(h,r)==r['outcome'] for r in rows)]

def claim(kind, **fields): return {'type':kind,**fields}
