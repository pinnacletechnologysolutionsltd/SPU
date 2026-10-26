"""Owner-requested prequalification dry count; never runs a qualification campaign."""
import argparse
import json
from pathlib import Path
from ..lattice_comparison.prepare import identities, digest
from ..lattice_symmetry.fixtures import workload_plan
from .adapter import run
from .checks import inspect


def verify(manifest):
    entries = json.loads(manifest.read_text())
    for path, expected in entries.items():
        assert digest(path) == expected, 'DRYCOUNT_SOURCE_CHANGED: '+path
    old = Path('build/d4_e8_math_20261013/comparison_readiness_01/source_manifest.json')
    for path, expected in json.loads(old.read_text()).items():
        assert digest(path) == expected, 'READINESS_SOURCE_CHANGED: '+path
    return identities()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    args = parser.parse_args()
    assert args.output.resolve().is_relative_to(Path('build').resolve()), 'OUTPUT_SCOPE'
    args.output.mkdir(parents=True, exist_ok=False)
    protection = verify(args.source_manifest)
    plan = workload_plan()
    frozen = Path('build/d4_e8_math_20261013/preparation_01/checks_03/workload_plan.json')
    assert plan == json.loads(frozen.read_text()), 'FIXTURES_CHANGED'
    summaries, executions = {}, 0
    with (args.output/'rows.jsonl').open('x') as stream:
        try:
            for case in plan['proposed_cases']:
                arms = ['coordinates','generator_word','matrix','surd']
                if case['system'] == 'D4':
                    arms.append('signed')
                for arm in arms:
                    row, _ = run(case, arm)
                    inspect(case, row)
                    stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush()
                    executions += 1
                    key = case['system']+'/'+arm
                    target = summaries.setdefault(key, dict(evaluations=0, proposed_work_exceedances=0,
                        proposed_storage_exceedances=0, maximum_work=0, maximum_case_work=0,
                        maximum_setup_work=0, maximum_live_bits=0, maximum_raw_bits=0))
                    target['evaluations'] += 1
                    target['proposed_work_exceedances'] += int(row['proposed_work_exceeded'])
                    target['proposed_storage_exceedances'] += int(row['proposed_storage_exceeded'])
                    for field, value in (('maximum_work',row['work']),('maximum_case_work',row['case_work']),
                            ('maximum_setup_work',row['setup_work']),('maximum_live_bits',row['simultaneous_live_bits']),
                            ('maximum_raw_bits',row['raw_integer_bits'])):
                        if value > target[field]:
                            target[field], target[field+'_fixture'] = value, case['id']
                    print(json.dumps(dict(progress=executions, fixture=case['id'], arm=arm,
                                          case_work=row['case_work'], live_bits=row['simultaneous_live_bits'])), flush=True)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='DRY_COUNT_STOPPED',
                fixture=case['id'],arm=arm,completed_evaluations=executions,error=str(error)),indent=2)+'\n')
            raise
    assert executions == 540, 'EVALUATION_COUNT'
    after = verify(args.source_manifest)
    assert after == protection, 'IDENTITY_CHANGED'
    result = dict(status='DIAGNOSTIC_DRY_COUNT_COMPLETE_NOT_QUALIFICATION', cases=120,
                  applicable_arm_evaluations=executions, unique_fixture_cases=120,
                  summaries=summaries, protection=after, fixture_sha256=digest(frozen),
                  source_manifest_sha256=digest(args.source_manifest),
                  proposed_work_limit=2000000, proposed_storage_limit_bits=1048576,
                  limits_changed=False, qualification='HOLD / NOT RUN',
                  full_event_replay='SHORT LITERALS ONLY; every full row has independent formulas/reference checks',
                  independent_reviewer='PENDING', hardware_commands=0)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':
    main()
