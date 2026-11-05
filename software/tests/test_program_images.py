"""Every tracked software/programs/*.bin must equal the canonical assembler output
of its same-stem .sas source (raw big-endian 8-byte words, no header).

Images without a source are listed explicitly; a new sourceless image fails.
"""
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.tools import spu13_asm as asm

# Unreferenced 3-word image from the RC2 snapshot (b063280); no source exists.
SOURCELESS = {'software/programs/spu_test_prog.bin'}

tracked = subprocess.run(
    ['git', 'ls-files', '--', 'software/programs/*.bin'],
    cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
assert tracked, 'no tracked program images found'

failures = []
for rel in tracked:
    if rel in SOURCELESS:
        continue
    image = ROOT / rel
    source = image.with_suffix('.sas')
    if not source.exists():
        failures.append(f'{rel}: no .sas source and not listed in SOURCELESS')
        continue
    try:
        words, _ = asm.assemble(source.read_text(), str(source))
    except asm.AssemblyError as exc:
        failures.append(f'{rel}: source does not assemble: {exc}')
        continue
    expected = b''.join(struct.pack('>Q', w) for w in words)
    if image.read_bytes() != expected:
        failures.append(f'{rel}: image differs from canonical assembly of {source.name}')

missing = SOURCELESS - set(tracked)
if missing:
    failures.append(f'SOURCELESS entries no longer tracked: {sorted(missing)}')

if failures:
    print('\n'.join(failures))
    print(f'FAIL: {len(failures)} program image(s) diverge from their sources')
    sys.exit(1)
print(f'PASS: {len(tracked) - len(SOURCELESS)} program images match canonical assembly')
