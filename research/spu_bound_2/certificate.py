"""Bounded prefix certificate for denominator-one Pell-unit SMUL traces."""
import itertools
import json
import sys
from software.experiments.surd_cpu_stream import Stream
from research.spu_bound_0.experiment import extrema, compose, U, V, I, width

LIMIT = (1 << 63) - 1


def issue(box, seq):
    mat, interval, steps = I, box, []
    for sign in seq:
        if sign not in (-1, 1):
            raise ValueError('unsupported generator')
        m = U if sign == 1 else V
        mat = compose(m, mat)
        interval = extrema(m, interval)
        bounds = extrema(mat, box)
        steps.append({'matrix': mat, 'bounds': bounds,
                      'interval': interval,
                      'bits': [max(width(n) for n in pair) for pair in bounds]})
    return {'box': box, 'seq': seq, 'steps': steps}


def verify(cert):
    """Independent recurrence and extremum checker; rejects malformed/tampered data."""
    try:
        box, seq, steps = cert['box'], cert['seq'], cert['steps']
        if len(box) != 2 or len(seq) != len(steps): return False
        if any(len(v) != 2 or any(type(x) is not int for x in v) or v[0] > v[1]
               or v[0] < -(1 << 63) or v[1] > LIMIT for v in box): return False
        m = [[1, 0], [0, 1]]
        lohi = [list(v) for v in box]
        for s, item in zip(seq, steps):
            if type(s) is not int or s not in (-1, 1): return False
            m = [[2*m[0][j]+3*s*m[1][j] for j in range(2)],
                 [s*m[0][j]+2*m[1][j] for j in range(2)]]
            mstep = [[2,3*s],[s,2]]
            def bound(row, ranges):
                p = [[c*x for x in v] for c,v in zip(row,ranges)]
                return [sum(min(t) for t in p),sum(max(t) for t in p)]
            bounds = [bound(row, box) for row in m]
            lohi = [bound(row, lohi) for row in mstep]
            bits = [max((v if v >= 0 else -v-1).bit_length()+1 for v in pair) for pair in bounds]
            if [list(v) for v in item['matrix']] != m or [list(v) for v in item['bounds']] != bounds or [list(v) for v in item['interval']] != lohi or item['bits'] != bits: return False
        return True
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def reference_trace(a,b,seq):
    """Use existing independent exact tuple reference with initialized denominator-one registers."""
    st = Stream(); st.load(0,(a,b,1)); st.load(1,(2,1,1)); st.load(2,(2,-1,1))
    events=[]
    for sign in seq:
        st.command('SMUL',['S0','S0', 'S1' if sign == 1 else 'S2'])
        row=st.lines[-1].split()
        events.append({'status':int(row[2]),'write':int(row[3]),'tuple':st.bank[0], 'retire':1})
        if int(row[2]): break
    return events


def summarize(box,seq):
    cert=issue(box,seq)
    assert verify(cert)
    vals=list(itertools.product(*(range(a,b+1) for a,b in box)))
    for a,b in vals:
        exact=[a,b]
        for i,s in enumerate(seq):
            a0,b0=exact; exact=[2*a0+3*s*b0,s*a0+2*b0]
            for x,(lo,hi) in zip(exact,cert['steps'][i]['bounds']): assert lo<=x<=hi
        events=reference_trace(a,b,seq)
        if all(step['bits'][0]<=64 and step['bits'][1]<=64 for step in cert['steps']):
            assert len(events)==len(seq) and all(e['status']==0 and e['write']==1 for e in events)
            assert events[-1]['tuple']==(*exact,1)
    return cert

if __name__=='__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--verify':
        with open(sys.argv[2], encoding='utf-8') as f:
            ok = verify(json.load(f))
        print('VALID' if ok else 'INVALID')
        sys.exit(0 if ok else 1)
    if len(sys.argv) == 2 and sys.argv[1] == '--emit':
        print(json.dumps(issue(((-2,2),(-2,2)),[1,-1]), sort_keys=True))
        sys.exit(0)
    for name,box,seq in [('cancellation',((-2,2),(-2,2)),[1,-1]),('mixed',((-2,2),(-1,1)),[1,1,-1,1]),('no-gain',((-2,2),(-2,2)),[1]),('overflow',((LIMIT,LIMIT),(0,0)),[1,-1])]:
        c=summarize(box,seq)
        print(name, 'bounds',[s['bounds'] for s in c['steps']], 'interval',c['steps'][-1]['interval'], 'bits',[s['bits'] for s in c['steps']])
        a,b=box[0][0],box[1][0]
        print('  eager',reference_trace(a,b,seq),'identity rewrite',{'status':0,'write':0,'retire':0,'tuple':(a,b,1)} if seq==[1,-1] else 'not evaluated')
