"""Versioned stage-table validation, independent of candidate schemas/code."""

from w31_verify import require


def validate(table):
    require(table['schema']=='qcg0-independent-w31-stages-v1', "stage table invariant failed")
    require(len(table['preparations'])==21 and len(table['routes'])==53, "stage table invariant failed")
    keys=set()
    for route in table['routes']:
        key=(route['curve'],route['arm'],route['tape'])
        require(key not in keys, "stage table invariant failed")
        keys.add(key)
        if route.get('preparation_outcome'):
            require(route['rows']==[] and route['issued']==route['unissued']==0, "stage table invariant failed")
            continue
        n=16 if route['tape']=='CellB' else 17
        require(len(route['rows'])==n, "stage table invariant failed")
        issued=0
        failed=False
        for k,row in enumerate(route['rows']):
            require(row['profile']=='W31' and row['curve']==route['curve'], "stage table invariant failed")
            require(row['arm']==route['arm'] and row['tape']==route['tape'], "stage table invariant failed")
            require(row['request']==f'q{k:02d}', "stage table invariant failed")
            if 'scheduling_outcome' in row:
                require(route['dependent'] and failed, "stage table invariant failed")
                require(row['scheduling_outcome']=='NOT_ISSUED', "stage table invariant failed")
                require(row['reason']=='STATE_DEPENDENT_AFTER_REFUSAL', "stage table invariant failed")
                require(not any(x in row for x in ('status','event_id','ledger','values')), "stage table invariant failed")
                continue
            require(not (route['dependent'] and failed), "stage table invariant failed")
            issued+=1
            require(row['status'] in ('OK','REFUSED','INVALID'), "stage table invariant failed")
            if row['status']=='OK':
                require('values' in row and 'event_id' not in row, "stage table invariant failed")
            else:
                failed=True
                require(row['event_id'].startswith(route['arm']+'.Q.'+row['request']+'.'), "stage table invariant failed")
                require('values' not in row, "stage table invariant failed")
                require(row['state_before']==row['state_after'], "stage table invariant failed")
        require(route['issued']==issued and route['unissued']==n-issued, "stage table invariant failed")
    return True
