#!/usr/bin/env python3
"""Restore and replay the historical focused Surd Lorentz simulation package."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from retention_archive import package, restore
from retention_tree import digest
from verify_restore import load_manifest, verify


def rehearsal(output: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    cleanup = repo / 'build/repository_cleanup'
    if not output.resolve().is_relative_to(cleanup.resolve()) or output.resolve() == cleanup.resolve():
        raise ValueError('output must be a fresh child of build/repository_cleanup')
    if output.exists() or output.is_symlink():
        raise ValueError('output already exists')
    evidence = repo / 'docs/research/surd_lorentz_20261011/evidence'
    historical = json.loads((evidence / 'source_hashes.json').read_text())
    archived = json.loads((evidence / 'archive_manifest.json').read_text())
    # Check historical sources before producing any package; never substitute.
    for name, expected in historical.items():
        if digest(Path(name)) != expected:
            raise ValueError(f'historical source mismatch: {name}')
    for name, expected in archived['files'].items():
        if digest(evidence / name) != expected:
            raise ValueError(f'historical evidence mismatch: {name}')
    output.mkdir(parents=True, exist_ok=False)
    staging = output / 'staging'
    staging.mkdir()
    for name in historical:
        source = Path(name)
        target = staging / source.relative_to(repo)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(evidence, staging / 'retained_evidence')
    # The replay recipe is packaged, independent of the source filesystem.
    original = json.loads((evidence / 'compile_command.json').read_text())
    argv = [arg.replace(str(repo), '{RESTORE_ROOT}') for arg in original]
    argv[argv.index('-o') + 1] = '{REPLAY_ROOT}/cpu.vvp'
    historical_program = next(name for name in historical if name.endswith('/program.txt'))
    recipe = {'compile_argv': argv, 'program': str(Path(historical_program).relative_to(repo)),
              'poisoned_program': 'retained_evidence/poisoned_program.txt',
              'scope': 'Historical frozen stream replay; no regenerated oracle or full FPGA qualification'}
    (staging / 'replay_recipe.json').write_text(json.dumps(recipe, indent=2) + '\n')
    pins = package(staging, output / 'package')
    # Remove staging from its expected location without deleting it.
    staging.rename(output / 'staging_unavailable')
    restored = output / 'restored'
    restore(output / 'package', restored, pins)
    recipe = json.loads((restored / 'replay_recipe.json').read_text())
    replay = output / 'replay'
    replay.mkdir()
    deadline = time.monotonic() + 55
    commands = []

    def execute(argv: list[str], name: str) -> subprocess.CompletedProcess:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('55-second rehearsal execution limit exceeded')
        proc = subprocess.run(argv, cwd=restored, capture_output=True, timeout=remaining)
        (replay / (name + '.stdout')).write_bytes(proc.stdout)
        (replay / (name + '.stderr')).write_bytes(proc.stderr)
        commands.append({'argv': argv, 'cwd': str(restored), 'exit_code': proc.returncode})
        (replay / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return proc

    compile_argv = [a.replace('{RESTORE_ROOT}', str(restored)).replace('{REPLAY_ROOT}', str(replay))
                    for a in recipe['compile_argv']]
    if execute(compile_argv, 'compile').returncode:
        raise ValueError('restored compile failed')
    binary = replay / 'cpu.vvp'
    sources = re.findall(r'"([^"]+)"', binary.read_text().split('.file_names')[-1])
    compiled = sorted({str((restored / name).resolve()) for name in sources if name.endswith(('.v', '.vh'))})
    expected_compiled = [str(restored / Path(name).relative_to(repo)) for name in
                         json.loads((restored / 'retained_evidence/compiled_sources.json').read_text())]
    if compiled != sorted(expected_compiled) or not all(Path(p).is_relative_to(restored) for p in compiled):
        raise ValueError('compiled sources are not exactly the restored historical inputs')
    positive = execute(['vvp', str(binary), '+PROGRAM=' + str(restored / recipe['program'])], 'positive')
    if positive.returncode or b'PASS canonical CPU directed execution and complete kernel stream' not in positive.stdout:
        raise ValueError('positive replay did not pass')
    count = len(re.findall(rb'^INS ', positive.stdout, re.M))
    if count != 853:
        raise ValueError('historical instruction retirement count differs')
    negative = execute(['vvp', str(binary), '+PROGRAM=' + str(restored / recipe['poisoned_program'])], 'negative')
    if negative.returncode == 0 or b'atomic tuple mismatch' not in negative.stdout:
        raise ValueError('poisoned expectation did not fail as expected')
    verify(restored, load_manifest(output / 'package/manifest.json', pins['manifest_sha256']))
    result = {'status': 'PASS_FOCUSED_RESTORATION_REHEARSAL', 'package': pins,
              'historical_inputs_verified': len(historical), 'compiled_sources': compiled,
              'retired_instructions': count, 'poisoned_expectation_rejected': True,
              'original_sources_required_by_replay': False,
              'isolation': 'restored-only arguments and compiled-source audit; no OS sandbox claim',
              'scope': recipe['scope'], 'independent_storage_copies': 0,
              'production_pruning_qualified': False, 'cleanup_authorized': False}
    (output / 'rehearsal_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rehearsal(args.out.absolute())
