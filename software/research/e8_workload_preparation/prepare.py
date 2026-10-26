"""Review/workload preparation only; never executes the full384-configuration plan."""
import argparse
import json
from pathlib import Path
import shutil
from ..e8_root_images.prepare import protection
from ..e8_root_images.tables import context
from ..lattice_comparison.prepare import digest
from .fixtures import plan
from .preview import run as preview
from .left_kernel import run as kernel
from ..e8_root_images.descriptor import from_word


def protected():
    checks=protection()
    base=Path('build/e8_root_images_20261013/preparation_01')
    entries=json.loads((base/'source_manifest.json').read_text())
    if any(digest(p)!=sha for p,sha in entries.items()):
        raise ValueError('E8_PREPARATION_SOURCE_CHANGED')
    checks['e8_preparation']=dict(files=len(entries),status='UNCHANGED',
                                 manifest_sha256=digest(base/'source_manifest.json'))
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(Path('build').resolve()):
        parser.error('output must be a new child of build/')
    before=protected()
    corpus=plan()
    cases=[c for c in corpus['configs'] if
           (c['family']=='scrambled' and c['length']==8 and c['clients']==1 and
            c['cadence'] in (1,'final') and c['regime']=='shared_lockstep') or
           (c['family']=='inverse_pair' and c['length']==8 and c['clients']==4 and
            c['cadence']==4 and c['regime'] in ('cold_serial','private_lockstep'))]
    assert len(cases)==4
    previews=[preview(c) for c in cases]
    paired=[p['observations'] for p in previews if p['id'].startswith('inverse_pair/')]
    assert paired[0]==paired[1],'REGIME_OBSERVER_MISMATCH'
    result,events=kernel(from_word((0,)),2,True)
    ctx=context()
    row_bound=max(sum(abs(v) for v in row) for row in ctx.inverse_basis)
    assert row_bound==5
    assert max(abs(v) for row in ctx.coefficients for v in row)==6
    before_after=protected()
    assert before_after==before,'SOURCE_PROTECTION_CHANGED'
    args.output.mkdir(parents=True)
    payloads={'fixture_plan.json':corpus,'preview.json':previews,'left_kernel.json':result,
              'left_kernel_events.json':events,'protection.json':before,
              'reference_bounds.json':dict(inverse_basis_max_row_l1=str(row_bound),
                root_coefficients_max=6,input_bound=1 << 31,coefficient_bound=5*(1 << 31),
                rational_raw_bound=108*(1 << 31),normalized_denominator_divides=4,
                status='PROOF_REVIEW_OBLIGATIONS_NOT_FINITE_WIDTH_QUALIFICATION')}
    for name,data in payloads.items():
        (args.output/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    paths=sorted(Path('software/research/e8_workload_preparation').glob('*.py'))+[
        Path('software/tests/test_e8_workload_preparation.py'),
        Path('spu_strategy/contract_e8_review_accounting_preparation_2026-10-13.md'),
        Path('docs/E8_ROOT_IMAGE_MATHEMATICAL_REVIEW_PACKET_2026-10-13.md')]
    for p in paths:
        target=args.output/'snapshot'/p
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,target)
    (args.output/'source_manifest.json').write_text(json.dumps({str(p):digest(p) for p in paths},indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status='PREPARATION_CHECKS_PASS_NOT_QUALIFICATION',configs_prepared=384,
        preview_configs=4,preview_observations=sum(len(p['observations']) for p in previews),
        left_kernel_work=result['work'],left_kernel_peak_bits=result['simultaneous_live_bits'],
        independent_reviewer='PENDING',evidence=str(args.output)),sort_keys=True))


if __name__=='__main__':
    main()
