"""Fixture adaptation and typed observation serialization outside logical charges."""
from dataclasses import fields, is_dataclass
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path


def arguments(operation, raw):
    if type(raw) is not list:
        return raw
    converted = list(raw)
    positions = range(min(1 if operation == 'step' else len(raw), len(raw)))
    for i in positions:
        if type(converted[i]) is list:
            converted[i] = tuple(converted[i])
    return tuple(converted)


def destination(raw):
    return tuple(raw)


def plain(value):
    if is_dataclass(value):
        value = {f.name: getattr(value, f.name) for f in fields(value)}
    if isinstance(value, Mapping):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def identical(left, right):
    """Preserve false-versus-zero and Boolean-versus-integer distinctions."""
    return json.dumps(plain(left), sort_keys=True) == json.dumps(plain(right), sort_keys=True)


def load(path):
    return json.loads(Path(path).read_text())


def check_hashes(root, expected):
    failures = []
    for name, digest in expected.items():
        actual = hashlib.sha256((Path(root) / name).read_bytes()).hexdigest()
        if actual != digest:
            failures.append(name)
    if failures:
        raise RuntimeError('FROZEN_INPUT_CHANGED: ' + ', '.join(failures))


def unique_ids(groups):
    names = [row['id'] for rows in groups for row in rows]
    if len(names) != len(set(names)):
        raise RuntimeError('DUPLICATE_FIXTURE_ID')
    return len(names)
