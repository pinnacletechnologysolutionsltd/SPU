"""Short validated-state evidence; no full corpus or qualification execution."""
import argparse
import json
from pathlib import Path
import shutil
from ..e8_workload_preparation.prepare import protected
from ..lattice_comparison.prepare import digest
from ..e8_root_images import descriptor,wire
from ..e8_root_images.tables import context
from ..lattice_drycount.ledger import replay
from .session import Session


def protection():
    checks=protected()
    base=Path('build/e8_root_images_20261013/workload_preparation_02')
    entries=json.loads((base/'source_manifest.json').read_text())
    if any(digest(p)!=sha for p,sha in entries.items()):
        raise ValueError('WORKLOAD_SOURCE_CHANGED')
    checks['workload_preparation']=dict(files=len(entries),status='UNCHANGED',
                                      manifest_sha256=digest(base/'source_manifest.json'))
    return checks


def witnesses():
    ctx=context()
    rows=[]
    for name,word,vector in [('identity',(),(1,)*8),('noncommuting',(0,2),(1,)*8),
                             ('inverse_pair',(0,2,2,0),(3,1,1,1,1,1,1,3))]:
        s=Session(True)
        before=s.report()['work']
        handle=s.import_wire(wire.encode(ctx.basis_ids))
        import_work=s.report()['work']-before
        transition_work=[]
        for j in word:
            before=s.report()['work']; s.transform(handle,j)
            transition_work.append(s.report()['work']-before)
        expected=descriptor.from_word(word)
        before=s.report()['work']; serialized=s.export_wire(handle)
        wire_work=s.report()['work']-before
        assert wire.decode(serialized.payload)==expected,'WIRE_REFERENCE'
        before=s.report()['work']; coordinates=s.materialize(handle,vector)
        materialization_work=s.report()['work']-before
        assert coordinates.payload==descriptor.apply(expected,vector),'VECTOR_REFERENCE'
        before=s.report()['work']
        s.release_export(serialized); s.release_export(coordinates); s.retire(handle)
        cleanup_work=s.report()['work']-before
        report=s.report(); checked=replay(s.events(),report)
        assert report['live_states']==report['live_exports']==0,'OWNERSHIP_RELEASE'
        assert all(cost==117 for cost in transition_work),'TRANSITION_COUNT'
        rows.append(dict(id=name,word=word,initial_vector=vector,output=coordinates.payload,
            import_work=import_work,transform_work=transition_work,serialization_work=wire_work,
            materialization_work=materialization_work,cleanup_work=cleanup_work,
            report=report,ledger=checked,events=s.events()))
    return dict(status='PREPARATION_PASS_NOT_QUALIFICATION',scenarios=rows,
                invariant='registered admitted state / immutable verified context / LEFT-only transition',
                setup_work='UNMETERED',complete_e8_accounting='OPEN',independent_reviewer='PENDING',
                root_hash=ctx.root_hash,basis_hash=ctx.basis_hash)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(Path('build').resolve()):
        parser.error('output must be a new child of build/')
    before=protection(); report=witnesses()
    assert protection()==before,'PROTECTION_CHANGED'
    paths=sorted(Path('software/research/e8_validated_state').glob('*.py'))+[
        Path('software/tests/test_e8_validated_state.py'),
        Path('spu_strategy/contract_e8_validated_state_preparation_2026-10-13.md'),
        Path('docs/E8_VALIDATED_STATE_PREPARATION_2026-10-13.md')]
    args.output.mkdir(parents=True)
    for p in paths:
        target=args.output/'snapshot'/p
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,target)
    for name,data in [('source_manifest.json',{str(p):digest(p) for p in paths}),
                      ('preparation.json',report),('protection.json',before)]:
        (args.output/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status=report['status'],scenarios=len(report['scenarios']),
        transform_work=117,setup='UNMETERED',evidence=str(args.output)),sort_keys=True))


if __name__=='__main__':
    main()
