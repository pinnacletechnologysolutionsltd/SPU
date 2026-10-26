"""Short review packet only; refuses existing evidence paths and changed sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from .review import witnesses
from .limits import Profile

BASE = Path('build/d4_e8_math_20261013/preparation_01')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identities():
    reports = {}
    for label, path in (('original_preparation', BASE / 'source_manifest.json'),
                        ('protected_sources', BASE / 'protected_sources.json'),
                        ('sgn_archive', Path('build/sgn1/phase_a_closeout_20261013/archive_01/evidence_manifest.json'))):
        raw = json.loads(path.read_text())
        entries = raw['files'] if label == 'sgn_archive' else raw
        bad = []
        for name, record in entries.items():
            expected = record['sha256'] if isinstance(record, dict) else record
            if not Path(name).is_file() or digest(name) != expected:
                bad.append(name)
        if bad:
            raise ValueError('PROTECTED_IDENTITY_CHANGED: ' + ', '.join(bad))
        reports[label] = dict(files=len(entries), status='UNCHANGED', manifest_sha256=digest(path))
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='new preparation evidence directory under build/')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(Path('build').resolve()) or output.exists():
        parser.error('output must be a new directory under build/')
    protected = identities()
    review = witnesses()
    paths = sorted(Path('software/research/lattice_comparison').glob('*.py')) + [
        Path('software/tests/test_lattice_comparison_preparation.py'),
        Path('spu_strategy/contract_d4_e8_comparison_readiness_2026-10-13.md'),
        Path('docs/D4_E8_COMPARISON_READINESS_2026-10-13.md')]
    manifest = {str(path): digest(path) for path in paths}
    output.mkdir(parents=True, exist_ok=False)
    for path in paths:
        target = output / 'snapshot' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for name, data in (('source_manifest.json', manifest), ('review_witnesses.json', review),
                       ('identity_checks.json', protected), ('proposed_profile.json', vars(Profile()))):
        (output / name).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    result = dict(status='PREPARATION_ONLY_NOT_QUALIFIED', campaign='NOT RUN',
                  independent_reviewer='PENDING', fully_instrumented_arms='NOT IMPLEMENTED',
                  source_manifest_sha256=digest(output / 'source_manifest.json'),
                  protected=protected, hardware_commands=0)
    (output / 'preparation_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status=result['status'], evidence=str(args.output)), sort_keys=True))


if __name__ == '__main__':
    main()
