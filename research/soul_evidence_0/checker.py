"""Independent bounded checker; results conditional on a trusted manifest anchor."""
import hashlib
import json

VERDICTS=('SUPPORTED','UNSUPPORTED','UNKNOWN','INVALID_EVIDENCE','UNVERIFIED')
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x): return hashlib.sha256(canon(x)).hexdigest()

def manifest(records, language, rules):
    return {'records':{r['id']:digest(r) for r in records},'language':digest(language),'rules':digest(rules)}

def anchor(records, language, rules): return digest(manifest(records,language,rules))

def evaluation(code, row):
    # Intentionally independent of producer's predictor.
    if code=='0': return False
    if code=='L': return row['linked']
    if code=='F': return row['fixed']
    if code=='L&F': return row['linked'] and row['fixed']
    raise ValueError('unknown hypothesis code')

def check(claim, records, language, rules, trusted_manifest, trusted_anchor):
    def out(v, **extra): return {'verdict':v,**extra}
    # Validate present content first, then absence, then supported semantics.
    if not isinstance(claim,dict) or not isinstance(records,list) or not all(isinstance(r,dict) and isinstance(r.get('id'),str) for r in records): return out('INVALID_EVIDENCE')
    ids=[r['id'] for r in records]
    if len(ids)!=len(set(ids)): return out('INVALID_EVIDENCE')
    for r in records:
        kind=r.get('kind')
        if kind=='fact' and (not isinstance(r.get('proposition'),list) or len(r['proposition'])!=3): return out('INVALID_EVIDENCE')
        if kind=='relation' and any(not isinstance(r.get(k),str) for k in ('left','right','relation')): return out('INVALID_EVIDENCE')
        if kind=='observation' and any(type(r.get(k)) is not bool for k in ('linked','fixed','outcome')): return out('INVALID_EVIDENCE')
        if kind not in ('fact','relation','observation'): return out('INVALID_EVIDENCE')
    if trusted_manifest is not None and not isinstance(trusted_manifest,dict): return out('INVALID_EVIDENCE')
    if trusted_anchor is not None and trusted_manifest is not None and digest(trusted_manifest)!=trusted_anchor: return out('INVALID_EVIDENCE')
    if trusted_anchor is None or language is None or rules is None or trusted_manifest is None: return out('UNKNOWN')
    if not isinstance(trusted_manifest.get('records'),dict): return out('INVALID_EVIDENCE')
    expected=trusted_manifest['records']
    if any(r['id'] not in expected or digest(r)!=expected[r['id']] for r in records): return out('INVALID_EVIDENCE')
    if digest(language)!=trusted_manifest.get('language') or digest(rules)!=trusted_manifest.get('rules'): return out('INVALID_EVIDENCE')
    if set(ids)!=set(expected): return out('UNKNOWN')
    if language.get('version')!='h1' or rules.get('version')!='r1': return out('UNVERIFIED')
    candidates=language.get('candidates',{})
    if not isinstance(candidates,dict) or any(c not in ('0','L','F','L&F') for c in candidates.values()): return out('UNVERIFIED')
    by_id={r['id']:r for r in records}; refs=claim.get('refs',[])
    if not isinstance(refs,list) or any(not isinstance(i,str) for i in refs): return out('INVALID_EVIDENCE')
    if any(i not in by_id for i in refs): return out('UNKNOWN')
    kind=claim.get('type')
    if kind=='direct':
        if len(refs)<1: return out('UNKNOWN')
        record=by_id[refs[0]]
        if record.get('kind')!='fact': return out('INVALID_EVIDENCE')
        return out('SUPPORTED' if claim.get('proposition')==record.get('proposition') else 'UNSUPPORTED')
    if kind=='deduction':
        rule=claim.get('rule')
        if rule is None: return out('UNKNOWN')
        if rule not in rules.get('inference',[]): return out('UNVERIFIED')
        if rule!='transitive': return out('UNVERIFIED')
        if len(refs)<2: return out('UNKNOWN')
        a,b=(by_id[i] for i in refs[:2]); p=claim.get('proposition')
        if a.get('kind')!='relation' or b.get('kind')!='relation': return out('UNSUPPORTED')
        valid=(a['relation']=='subset' and b['relation']=='subset' and a['right']==b['left'] and p==[a['left'],'subset',b['right']])
        return out('SUPPORTED' if valid else 'UNSUPPORTED')
    observations=[r for r in records if r.get('kind')=='observation']
    if any(any(type(r.get(k)) is not bool for k in ('linked','fixed','outcome')) for r in observations): return out('INVALID_EVIDENCE')
    viable=sorted(h for h,c in candidates.items() if all(evaluation(c,r)==r['outcome'] for r in observations))
    if kind=='survivors':
        supplied=claim.get('survivors')
        if not isinstance(supplied,list): return out('UNKNOWN')
        unique=claim.get('unique',False)
        valid=sorted(supplied)==viable and (not unique or len(viable)==1)
        finding='UNIQUE_WITHIN_DECLARED_HYPOTHESIS_AND_EVIDENCE_BOUNDARY' if valid and len(viable)==1 else ('MULTIPLE_SURVIVORS' if len(viable)>1 else 'NO_SURVIVORS' if not viable else 'SINGLE_SURVIVOR')
        return out('SUPPORTED' if valid else 'UNSUPPORTED',survivors=viable,finding=finding)
    if kind=='reject':
        h=claim.get('hypothesis')
        if h not in candidates: return out('UNVERIFIED')
        if not refs: return out('UNKNOWN')
        obs=by_id[refs[0]]
        if obs.get('kind')!='observation': return out('UNSUPPORTED')
        counter=evaluation(candidates[h],obs)!=obs['outcome']
        return out('SUPPORTED' if counter else 'UNSUPPORTED',finding='CONTRADICTED' if counter else 'CONSISTENT')
    if kind=='prediction':
        h=claim.get('hypothesis'); features=claim.get('features')
        if h not in candidates: return out('UNVERIFIED')
        if not isinstance(features,dict) or any(type(features.get(k)) is not bool for k in ('linked','fixed')): return out('UNKNOWN')
        if type(claim.get('prediction')) is not bool: return out('UNKNOWN')
        return out('SUPPORTED' if evaluation(candidates[h],features)==claim['prediction'] else 'UNSUPPORTED',hypothesis_status='consistent' if h in viable else 'contradicted',survivors=viable)
    return out('UNVERIFIED')
