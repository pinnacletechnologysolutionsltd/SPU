"""Independent evidence checker: direct propositions or explicit transitivity."""
def check(claim, refs, available, rules=()):
    if claim is None: return 'UNKNOWN'
    lookup={r['id']:r for r in available if r['kind']=='fact'}
    if not refs or any(ref not in lookup for ref in refs): return 'UNKNOWN'
    facts=[lookup[ref] for ref in refs]
    if len(facts)==1:
        r=facts[0]
        return 'SUPPORTED' if (r['key'],r['value'],r['epoch'])==tuple(claim) else 'UNSUPPORTED'
    if len(facts)==2:
        if 'transitive' not in rules: return 'UNKNOWN'
        a,b=facts
        return 'SUPPORTED' if (a['key']==claim[0] and a['value']==b['key'] and b['value']==claim[1] and a['epoch']==b['epoch']==claim[2]) else 'UNSUPPORTED'
    return 'UNKNOWN'
