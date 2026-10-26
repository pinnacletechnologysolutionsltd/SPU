"""Read-only access to the qualified snapshot, never the live FCC sources."""
from functools import lru_cache
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'build/sgn1/scheduler_20261013/qualification_preparation_01'
SNAPSHOT = BASE / 'snapshot'
MANIFEST_SHA = '2ffbb5a8db811b2c804285a151c6c9158adfd631b701b950381be46113bbdce5'
NAMESPACE = '_sgn1_qualified_reference_20261013'


def verify_reference():
    raw = (BASE / 'source_manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise AssertionError(('REFERENCE_MANIFEST',))
    for name, digest in json.loads(raw).items():
        if hashlib.sha256((SNAPSHOT / name).read_bytes()).hexdigest() != digest:
            raise AssertionError(('REFERENCE_SOURCE', name))
    job = ROOT / 'build/sgn1/scheduler_20261013/qualification_01'
    if [n for n in ('COMPLETE', 'FAILED', 'TIMEOUT') if (job / n).exists()] != ['COMPLETE']:
        raise AssertionError(('REFERENCE_TERMINAL',))
    result = json.loads((job / 'result.json').read_text())
    if result['outcome'] != 'COMPLETE' or result['exit_code'] != 0:
        raise AssertionError(('REFERENCE_RESULT', result))


@lru_cache(maxsize=None)
def frozen_module(name):
    if name not in {'packets', 'node_service', 'conservation', 'schedule_reference',
                    'scheduler_fixtures', 'scheduler_qualification', 'trace_checker'}:
        raise ValueError('REFERENCE_MODULE')
    verify_reference()
    path = SNAPSHOT / 'software/research/sgn1'
    if NAMESPACE not in sys.modules:
        spec = importlib.util.spec_from_file_location(NAMESPACE, path / '__init__.py',
                                                     submodule_search_locations=[str(path)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[NAMESPACE] = module
        spec.loader.exec_module(module)
    elif Path(sys.modules[NAMESPACE].__file__).resolve() != (path / '__init__.py').resolve():
        raise AssertionError(('REFERENCE_NAMESPACE',))
    return importlib.import_module(NAMESPACE + '.' + name)


def plan():
    return frozen_module('scheduler_fixtures').frozen_plan()
