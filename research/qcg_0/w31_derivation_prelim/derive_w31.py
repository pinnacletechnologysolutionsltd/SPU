"""REGISTERED WORKLOAD ENTRY. Execute only under separately authorized launcher."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from w31_arithmetic import Q
from w31_prepare import SEQUENTIAL,CELL_B
from w31_routes import preparation,route
from w31_table import validate
from w31_certified import load_reference, check_certified, REFERENCE_NAME


def main():
    # Paths exist only in the launcher's isolated mount namespace.
    if sys.argv[1:]!=['--bounded-authorized-entry'] or not Path('/out').is_dir():
        raise SystemExit('HOLD: use the separately authorized bounded launcher')
    spec=json.loads(Path('/work/INPUT_MANIFEST.json').read_text())
    reference=load_reference(Path('/references')/REFERENCE_NAME, spec['inputs'][REFERENCE_NAME])
    workload=spec['workload']
    table=dict(schema='qcg0-independent-w31-stages-v1',profile='W31',
               contract_sha256=spec['inputs']['QCG0_P0_EXECUTION_CONTRACT.md'],
               preparations=[],routes=[])
    def rationals(values):
        return [Q(*v) for v in values]
    def add(curve,arm,U,V,phi=None):
        state,prep=preparation(arm,rationals(U),rationals(V),rationals(phi) if phi else None)
        prep.update(curve=curve,arm=arm,profile='W31')
        table['preparations'].append(prep)
        for tape in (['CellB'] if phi else ['S1','S2','S3']):
            if prep['status']!='OK':
                r=dict(arm=arm,tape=tape,rows=[],issued=0,unissued=0,
                       preparation_outcome=prep['preparation_outcome'])
            else:
                r=route(arm,state,tape,rationals(workload['cell_b_parameters']) if phi else None)
                for row in r['rows']: row['curve']=curve
            r['curve']=curve
            table['routes'].append(r)
    for curve,source in workload['curves'].items():
        for arm in SEQUENTIAL: add(curve,arm,source['U'],source['V'])
    source=workload['curves']['PH3']
    for arm in CELL_B: add('PH3',arm,source['U'],source['V'],workload['phi'])
    validate(table)
    check_certified(table, reference)
    written=0
    def write(name,data):
        nonlocal written
        b=(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n').encode()
        if len(b)>4194304 or written+len(b)>8*1024*1024:
            Path('/out/CAP_BREACH').touch(exist_ok=False)
            raise SystemExit(90)
        try:
            with Path('/out',name).open('xb') as f: f.write(b)
        except OSError:
            Path('/out/CAP_BREACH').touch(exist_ok=True)
            raise SystemExit(90)
        written+=len(b)
        return hashlib.sha256(b).hexdigest()
    digest=write('stage_tables.json',table)
    # Recorded before any comparison; this entry has no candidate access.
    write('reviewer_certificate.json',dict(schema='qcg0-w31-derivation-certificate-v1',
          scope='independent stage derivation; no candidate comparison or acceptance',
          stage_tables_sha256=digest,source_manifest_sha256=hashlib.sha256(
              Path('/work/SOURCE_INPUTS_R2.sha256').read_bytes()).hexdigest(),
          preparations=21,sequential_routes=48,cell_b_routes=5,table_schema_checked=True,certified_rows_checked=True))
    Path('/out/RUNNER_DONE').touch(exist_ok=False)


if __name__=='__main__': main()
