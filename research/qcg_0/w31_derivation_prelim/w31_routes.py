"""Atomic preparation/requests, scheduling outcomes and JSON-ready rows."""
from copy import deepcopy
from hashlib import sha256
import json
from w31_arithmetic import Q, Trace, Refusal, Invalid
from w31_prepare import prepare
from w31_verify import require
from w31_sequential import evaluate as sequential
from w31_cell_b import evaluate as cell_b


def encode(v):
    if isinstance(v,Q):
        return [v.n,v.d]
    if isinstance(v,dict):
        return {k:encode(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):
        return [encode(x) for x in v]
    return v


def state_hash(v):
    return sha256(json.dumps(encode(v),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def attempt(trace, function):
    try:
        return dict(status='OK',values=encode(function()),ledger=dict(trace.counts))
    except (Refusal,Invalid) as ex:
        return dict(status='REFUSED' if isinstance(ex,Refusal) else 'INVALID',
                    code=ex.code,event_id=ex.event,ledger=dict(trace.counts))


def preparation(arm,U,V,phi=None):
    state = {}
    def build():
        state.update(prepare(trace,arm,U,V,phi))
        return state
    trace = Trace()
    row = attempt(trace,build)
    row['phase'] = 'P'
    if row['status'] != 'OK':
        row['preparation_outcome'] = 'PREPARATION_REFUSED' if row['status']=='REFUSED' else 'PREPARATION_INVALID'
        require(state == {}, "preparation modified refused state")
    return state,row


def route(arm,state,tape,parameters=None):
    bcell = tape == 'CellB'
    if not bcell and tape not in ('S1','S2','S3'):
        raise ValueError('unknown tape')
    dependent = not bcell and (tape == 'S3' or arm in ('FD','TS','PHFD','C1','C2'))
    state = deepcopy(state)
    stopped,rows = False,[]
    positions = parameters if bcell else [Q(k,16) for k in range(17)]
    for k,t in enumerate(positions):
        context = dict(profile='W31',arm=arm,tape=tape,request=f'q{k:02d}',parameter=encode(t))
        if stopped:
            rows.append(dict(context,scheduling_outcome='NOT_ISSUED',reason='STATE_DEPENDENT_AFTER_REFUSAL'))
            continue
        before = state_hash(state)
        working = deepcopy(state)
        trace = Trace()
        result = attempt(trace,lambda: cell_b(trace,arm,working,t,k) if bcell else
                         sequential(trace,arm,tape,working,k))
        if result['status'] == 'OK':
            state = working
        else:
            require(before == state_hash(state), "request modified refused state")
            stopped = dependent
        rows.append(dict(context,**result,state_before=before,state_after=state_hash(state)))
    if tape == 'S3':
        export_s3(rows)
    issued = sum('status' in row for row in rows)
    return dict(arm=arm,tape=tape,dependent=dependent,issued=issued,unissued=len(rows)-issued,rows=rows)


def export_s3(rows):
    """Relabel delayed payloads only; never move an operation, ledger or event."""
    delayed = [r['values'].pop('increment_from_previous') if r.get('status')=='OK'
               else None for r in rows]
    for k, row in enumerate(rows):
        if row.get('status') != 'OK':
            continue
        available = k == 16 or rows[k+1].get('status') == 'OK'
        row['increment_available'] = available
        if available:
            row['values']['increment_to_next'] = None if k == 16 else delayed[k+1]
