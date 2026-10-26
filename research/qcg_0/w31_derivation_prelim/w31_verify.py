"""Unconditional integrity checks; safe under -O and PYTHONOPTIMIZE."""
import hashlib
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_inventory(root, inventory):
    entries = Path(inventory).read_text().splitlines()
    require(bool(entries), 'HOLD: empty inventory')
    seen = set()
    for line in entries:
        want, name = line.split('  ', 1)
        require(name not in seen, 'HOLD: duplicate inventory path: '+name)
        seen.add(name)
        path = Path(root)/name
        require(path.is_file(), 'HOLD: missing inventory input: '+str(path))
        require(digest(path) == want, 'HOLD: pin mismatch: '+name)


def verify_inputs(root, manifest):
    for name, want in manifest['inputs'].items():
        path = Path(root)/'research/qcg_0'/name
        require(path.is_file(), 'HOLD: missing certified/input file: '+str(path))
        require(digest(path) == want, 'HOLD: input manifest mismatch: '+name)
