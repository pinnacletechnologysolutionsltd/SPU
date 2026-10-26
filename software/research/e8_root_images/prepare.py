"""Short E8 root-image tranche; refuses overwrite and preserves comparison evidence."""
import argparse
import json
from pathlib import Path
import shutil
from ..lattice_comparison.prepare import identities,digest
from .tables import context,storage_inventory
from .fixtures import plan
from . import descriptor as d, reference, wire
from .linear import identity,transpose,apply as matvec
from .reduced import reduced_word


def protection():
    reports = identities()
    for label,folder in [('comparison','comparison_readiness_01'),('ledger','ledger_preparation_01')]:
        manifest = Path('build/d4_e8_math_20261013')/folder/'source_manifest.json'
        entries = json.loads(manifest.read_text())
        if any(digest(path) != sha for path,sha in entries.items()):
            raise ValueError('SOURCE_IDENTITY_CHANGED:'+label)
        reports[label] = dict(files=len(entries),status='UNCHANGED',manifest_sha256=digest(manifest))
    inventory = Path('build/d4_e8_math_20261013/limit_amendment_review_01/preserved_evidence_inventory.json')
    entries = json.loads(inventory.read_text())
    if any(digest(path) != record['sha256'] for path,record in entries.items()):
        raise ValueError('DIAGNOSTIC_EVIDENCE_CHANGED')
    reports['completed_diagnostic'] = dict(files=len(entries),status='UNCHANGED',manifest_sha256=digest(inventory))
    return reports


def witnesses():
    ctx=context()
    table_check=reference.check_context(ctx)
    fixtures=plan()
    rows=[]
    for case in fixtures['cases']:
        if case['kind']=='negative_identity':
            images=tuple(ctx.index(tuple(-v for v in a)) for a in ctx.basis)
            matrix=tuple(tuple(-v for v in row) for row in identity())
        else:
            images=d.from_word(case['tokens'],ctx)
            matrix=reference.word_matrix(case['tokens'])
        assert d.cartesian(images,ctx)==matrix,'MATRIX_REFERENCE'
        inv=d.inverse(images,ctx)
        assert d.cartesian(inv,ctx)==transpose(matrix),'INVERSE_REFERENCE'
        assert d.compose(images,inv,ctx)==d.compose(inv,images,ctx)==ctx.basis_ids,'INVERSE_ORDERS'
        reduced=reduced_word(images,ctx)
        assert d.cartesian(d.from_word(reduced['tokens'],ctx),ctx)==reference.word_matrix(reduced['tokens']),'REDUCED_REFERENCE'
        permutation=tuple(ctx.index(d.apply(images,x,ctx)) for x in ctx.roots)
        assert len(set(permutation))==240,'ROOT_ACTION_PERMUTATION'
        for x in fixtures['vectors']:
            actual=d.apply(images,x,ctx)
            assert actual==matvec(matrix,x),'MATERIALIZATION_REFERENCE'
            assert sum(v*v for v in actual)==sum(v*v for v in x),'EUCLIDEAN_NORM'
        packet=wire.encode(images,ctx)
        assert wire.decode(packet,ctx)==images,'WIRE_ROUNDTRIP'
        rows.append(dict(id=case['id'],images=images,reduced_word=reduced['tokens'],
                         inversion_length=reduced['length'],descent_steps=reduced['steps'],
                         materializations=len(fixtures['vectors']),serialized_bytes=len(packet)))
    return dict(status='PREPARATION_CHECKS_PASS_NOT_QUALIFICATION',table=table_check,
                descriptor_cases=len(rows),root_actions=240*len(rows),materializations=sum(r['materializations'] for r in rows),
                longest_length=next(r['inversion_length'] for r in rows if r['id']=='longest-minus-identity'),
                root_hash=ctx.root_hash,basis_hash=ctx.basis_hash,rows=rows,storage=storage_inventory(ctx),
                independent_reviewer='PENDING',comparison_arm_added=False,qualification='HOLD / NOT RUN')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(Path('build').resolve()):
        parser.error('output must be a new child of build/')
    before=protection()
    report=witnesses()
    assert protection()==before,'PROTECTION_CHANGED'
    paths=sorted(Path('software/research/e8_root_images').glob('*.py'))+[
        Path('software/tests/test_e8_root_images_preparation.py'),
        Path('spu_strategy/contract_e8_root_image_preparation_2026-10-13.md'),
        Path('docs/E8_ROOT_IMAGE_PREPARATION_2026-10-13.md')]
    args.output.mkdir(parents=True)
    for path in paths:
        target=args.output/'snapshot'/path
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target)
    for name,data in [('source_manifest.json',{str(p):digest(p) for p in paths}),
                      ('preparation.json',report),('fixture_plan.json',plan()),('protection.json',before)]:
        (args.output/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status=report['status'],cases=report['descriptor_cases'],
                         materializations=report['materializations'],evidence=str(args.output)),sort_keys=True))


if __name__=='__main__':
    main()
