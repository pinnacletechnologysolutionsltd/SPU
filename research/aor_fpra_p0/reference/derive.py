"""Independent reference derivation. Registered execution requires separate GO."""
import argparse
from hashlib import sha256
import importlib.util
from itertools import chain
import json
import os
from pathlib import Path
import resource
import shlex
import sys
import time
import tracemalloc

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
for _name in ('accounting','pell','semantics','controls'):
    _spec=importlib.util.spec_from_file_location(_name,HERE/(_name+'.py'))
    _module=importlib.util.module_from_spec(_spec)
    sys.modules[_name]=_module
    _spec.loader.exec_module(_module)

from accounting import Budget, Ledger, Refusal, encoded
from controls import (Oracle,cases,control_verdict,fault_for_request,inject,
                      reject_fault,request,validate_result)
from semantics import State

SPEC_HASH='8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb'
FILES=('nominal.json','controls.json','accounting.json','faults.json','summary.json','manifest.json')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


class Writer:
    """Publish manifest last; partial output cannot be an accepted artifact set."""
    def __init__(self,destination):
        self.destination=Path(destination)
        self.destination.mkdir(parents=False,exist_ok=False)
        self.used,self.hashes=0,{}
        self.finished=False

    def write(self,name,value):
        if self.finished or name not in FILES or name in self.hashes:
            raise ValueError('unregistered/repeated output')
        if name=='manifest.json' and set(self.hashes)!=set(FILES[:-1]):
            raise ValueError('manifest before complete payload set')
        if name=='manifest.json' and (value.get('files')!=dict(self.hashes)
                                     or value.get('acceptance')!='PENDING'):
            raise ValueError('manifest binding/acceptance mismatch')
        if name=='summary.json' and value.get('status')!='DERIVED_PENDING_INDEPENDENT_ACCEPTANCE':
            raise ValueError('unqualified summary disposition')
        encoder=json.JSONEncoder(ensure_ascii=False,separators=(',',':'),allow_nan=False)
        buffer=bytearray()
        for chunk in chain(encoder.iterencode(value),('\n',)):
            data=chunk.encode('utf-8')
            if len(buffer)+len(data)>2*1024**2 or self.used+len(buffer)+len(data)>4*1024**2:
                raise Refusal('OUTPUT_LIMIT','writer.'+name)
            buffer.extend(data)
        temporary=self.destination/('.'+name+'.pending')
        with temporary.open('xb') as stream:
            stream.write(buffer); stream.flush(); os.fsync(stream.fileno())
        self.used+=len(buffer)
        self.hashes[name]=sha256(buffer).hexdigest()

    def finish(self):
        if set(self.hashes)!=set(FILES):
            raise RuntimeError('incomplete artifact set')
        for name in FILES:
            temporary=self.destination/('.'+name+'.pending')
            if digest(temporary)!=self.hashes[name] or (self.destination/name).exists():
                raise RuntimeError('artifact identity/exclusivity failure')
        for name in FILES:  # manifest.json is last.
            os.link(self.destination/('.'+name+'.pending'),self.destination/name)
            (self.destination/('.'+name+'.pending')).unlink()
        directory=os.open(self.destination,os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        self.finished=True
        return self.hashes['manifest.json']


def source_identities():
    paths=[HERE/(name+'.py') for name in ('derive','pell','semantics','accounting','controls')]
    paths += [HERE/'test_reference_synthetic.py']
    paths += [HERE.parent/name for name in ('REFERENCE_ENCODINGS.md','REFERENCE_DERIVATION_PACKET.md',
                                            'PREPARATION.md','REVISION3_SPEC_REVIEW.md')]
    paths += [ROOT/'tools'/name for name in ('run_detached_job.sh','run_detached_job_worker.sh','run_elapsed_deadline.py')]
    return {str(path.relative_to(ROOT)):digest(path) for path in paths}


def assert_limits():
    result={}
    for name,expected in ((resource.RLIMIT_AS,1024**3),(resource.RLIMIT_FSIZE,4*1024**2)):
        soft,hard=resource.getrlimit(name)
        if soft!=expected or hard!=expected:
            raise RuntimeError('required inherited hard/soft limit missing')
        result[str(name)]=[soft,hard]
    return result


def execute_case(arm,tape,shared,label,control=None):
    limits={} if control is None else {k:v for k,v in control['limits'].items() if k!='work'}
    ledger=Ledger(shared)
    started=time.monotonic_ns()
    model=State(ledger,arm,limits)
    setup_ns=time.monotonic_ns()-started
    started=time.monotonic_ns()
    oracle=Oracle(ledger,label+'.reference')
    reference_setup_ns=time.monotonic_ns()-started
    setup_counts=dict(ledger.counts)
    if control and control['limits'].get('work')==0:
        # The fixture's simulated algorithm remainder is zero; derivation work
        # still consumes the unchanged real case/invocation allowance.
        ledger.modeled_cap=ledger.modeled_used
    records,faults=[],[]
    for index,req in enumerate(tape):
        prior_counts=dict(ledger.counts)
        prior_used=ledger.used
        path=label+'.'+arm+'.'+str(index)+'.'+str(req.get('op','malformed'))
        fault=None if control is None else fault_for_request(control,index,req)
        if control and control['fault']=='bad_proof' and index==0:
            inject(model,'bad_proof',path)
        started=time.monotonic_ns()
        result=model.execute(req,path,fault)
        modeled_ns=time.monotonic_ns()-started
        modeled_last=ledger.previous
        validator_fault=None
        if control:
            if control['fault'] in ('inverse_sign','product_exponent','old_key','equality_true') and index==len(tape)-1:
                validator_fault=control['fault']
            elif control['fault']=='stale_snapshot':
                validator_fault='stale_snapshot'
        started=time.monotonic_ns()
        expected=validate_result(model,oracle,req,result,path,validator_fault)
        reference_ns=time.monotonic_ns()-started
        if expected is not None and validator_fault and expected!=result['output']:
            faults.append(dict(reject_fault(expected,result['output'],validator_fault),
                               path=path,expected=expected,altered=result['output']))
        if control and control['id']==5:
            forged={'receipt':dict(result['output']['receipt'],operation_status='OK',code=None,stage=None),'proof':'UNIT'}
            oracle.charge('K','forged_proof_rejection')
            faults.append(dict(reject_fault(result['output'],forged,'mint_proof'),
                               path=path,expected=result['output'],altered=forged))
        if result['refused']:
            code=result['output']['receipt']['code']
            ledger.event('K',path+'.reference.expected_refusal','REFERENCE')
            if control is None:
                raise RuntimeError('nominal refusal: '+code)
            if code=='WORK_LIMIT' and control['id']!=17:
                raise RuntimeError('incomplete derivation work allowance')
            if control['fault'] in ('stale_snapshot','bad_proof'):
                faults.append({'fault':control['fault'],'rejected':True,'path':path,
                               'reason':code,'altered_state':result['before'],
                               'refusal':result['output']})
        # Identities are digested, with full terminal inventory per case. This
        # avoids repeating hundreds of directory fields for every observation.
        encoded_request={'op':req['op'],'args':[value if (type(value) is not int or
                         req['op'] in ('STEP','SET_EQUAL') and position==0) else str(value)
                         for position,value in enumerate(req['args'])]}
        row={'request':encoded_request,'output':result['output'],'refused':result['refused'],
             'before_sha256':sha256(encoded(result['before'])).hexdigest(),
             'after_sha256':sha256(encoded(result['after'])).hexdigest(),
             'atomic':result['before']==result['after'] if result['refused'] else None,
             'unchanged':result['before']==result['after'],
             'cache_events':result['cache_events'],
             'wire_sha256':result['wire_sha256'],'discarded_wire_bytes':result['discarded_wire_bytes'],
             'ladder_extent':[sum(x['valid'] for x in result[which]['ladder']) for which in ('before','after')],
             'graph_unchanged':all(result['before'][key]==result['after'][key] for key in ('primary','cache','ladder')),
             'counts':{key:value-prior_counts.get(key,0) for key,value in sorted(ledger.counts.items())
                       if value!=prior_counts.get(key,0)},
             'last_event':modeled_last,'denied':ledger.denied,
             'modeled_ns':modeled_ns,'reference_ns':reference_ns}
        if control:
            row['milestones']=[x for x in ledger.milestones if x[0]>prior_used]
            row['deliberate_fault']=fault or ('bad_proof' if control['fault']=='bad_proof' else None)
            if expected is not None and expected!=result['output']:
                row['expected_output']=expected
        records.append(row)
        if result['refused']:
            break
    prior_verdict=dict(ledger.counts)
    verdict=None if control is None else control_verdict(control,records,faults,oracle.charge)
    final_checks={key:value-prior_verdict.get(key,0) for key,value in ledger.counts.items()
                  if value!=prior_verdict.get(key,0)}
    return {'arm':arm,'case':label,'records':records,'terminal_inventory':model.identity(),
            'fault':None if control is None else control['fault'],
            'setup_replay_ns':setup_ns,'reference_setup_ns':reference_setup_ns,
            'setup_counts':setup_counts,'final_check_counts':final_checks,
            'ledger':ledger.summary(),'control_verdict':verdict},faults


def nominal_tape(rho):
    tape=[]
    for index in range(64):
        tape.append(request('STEP',0 if index<32 else 1,1 if index<32 else -1))
        if (index+1)%rho==0:
            tape.append(request('OBSERVE'))
    return tape


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',required=True)
    parser.add_argument('--spec-sha256',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--source-manifest',required=True)
    args=parser.parse_args()
    frozen_args=['--spec','research/aor_fpra_p0/PREPARATION.md',
                 '--spec-sha256',SPEC_HASH,
                 '--source-manifest','research/aor_fpra_p0/R1_SOURCE_SHA256.json',
                 '--output','build/aor_fpra_p0/reference_derivation_01/fixtures']
    if sys.argv[1:]!=frozen_args or Path.cwd()!=ROOT:
        raise RuntimeError('proposed frozen argv/working-directory mismatch')
    if args.spec_sha256!=SPEC_HASH or digest(args.spec)!=SPEC_HASH:
        raise RuntimeError('frozen specification identity mismatch')
    limits=assert_limits()
    output=Path(args.output)
    parent=output.parent
    if output.name!='fixtures' or not parent.resolve().is_relative_to(ROOT/'build'):
        raise RuntimeError('detached evidence parent missing')
    if output.exists():
        raise RuntimeError('exclusive fixture destination already exists')
    # These files precede systemd launch. LAUNCHED may legitimately be written
    # after this child starts; never race that marker or wait for it here.
    identity_files=('git_commit','git_status.txt','command.txt','unit_name','launch_time_utc',
                    'working_directory.txt','tool_versions.txt')
    evidence={name:(parent/name).read_text() for name in identity_files}
    evidence_hashes={name:digest(parent/name) for name in identity_files}
    expected=['/usr/bin/prlimit','--as=1073741824:1073741824','--fsize=4194304:4194304','--',
              '/usr/bin/python3','-I','-B',str(Path(__file__).resolve().relative_to(ROOT)),*sys.argv[1:]]
    if shlex.split(evidence['command.txt'])!=expected:
        raise RuntimeError('reviewed command/argv mismatch')
    sources=source_identities()
    source_manifest=Path(args.source_manifest).read_bytes()
    source_manifest_sha=sha256(source_manifest).hexdigest()
    if json.loads(source_manifest)!=sources:
        raise RuntimeError('reviewed source manifest mismatch')
    started=time.monotonic_ns()
    tracemalloc.start()
    shared=Budget()
    nominal,controls,faults=[],[],[]
    # No registered case is constructed or executed at import.
    for arm in 'ABCD':
        for rho in (1,8,64):
            result,mutants=execute_case(arm,nominal_tape(rho),shared,'nominal.rho'+str(rho))
            nominal.append(result); faults.extend(mutants)
    for arm in 'ABCD':
        for control in cases():
            result,mutants=execute_case(arm,control['requests'],shared,'control.'+str(control['id']),control)
            controls.append(result); faults.extend(mutants)
    writer=Writer(output)
    writer.write('nominal.json',nominal)
    writer.write('controls.json',controls)
    writer.write('accounting.json',{'cases':[dict(case=x['case'],arm=x['arm'],**x['ledger']) for x in nominal+controls],
                                    'total_charged':shared.used,'cost_claim':'abstract partial work only'})
    writer.write('faults.json',faults)
    writer.write('summary.json',{'status':'DERIVED_PENDING_INDEPENDENT_ACCEPTANCE',
                                 'nominal_cases':len(nominal),'control_cases':len(controls),
                                 'scheduling':'SCHEDULE_EQUIVALENT',
                                 'elapsed_ns_after_preflight':time.monotonic_ns()-started,
                                 'heap_peak_bytes_through_payload_write':tracemalloc.get_traced_memory()[1],
                                 'rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    if source_identities()!=sources:
        raise RuntimeError('reference source changed during derivation')
    if digest(args.source_manifest)!=source_manifest_sha or any(
            digest(parent/name)!=identity for name,identity in evidence_hashes.items()):
        raise RuntimeError('input/provenance identity changed during derivation')
    writer.write('manifest.json',{'spec_sha256':SPEC_HASH,'sources':sources,
                                  'files':dict(writer.hashes),'limits':limits,
                                  'executable':{'path':sys.executable,'sha256':digest(sys.executable),
                                                'version':sys.version},
                                  'argv':sys.argv,'launcher_evidence':evidence,
                                  'source_manifest_sha256':source_manifest_sha,
                                  'launcher_evidence_sha256':evidence_hashes,
                                  'acceptance':'PENDING'})
    print('artifact_manifest_sha256='+writer.finish())
    print('final_elapsed_ns_after_preflight='+str(time.monotonic_ns()-started))
    print('final_heap_peak_bytes='+str(tracemalloc.get_traced_memory()[1]))
    print('final_rss_kib='+str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':
    main()
