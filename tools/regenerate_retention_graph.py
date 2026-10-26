#!/usr/bin/env python3
"""Rebuild only a prior graph's fixed input set; preserve identity differences."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from retention_dependencies import dependency_graph
from retention_tree import digest, member_path


def regenerate(repo: Path, prior_path: Path, output: Path) -> None:
    allowed = (repo / 'build/repository_cleanup').resolve()
    if output.exists() or output.is_symlink():
        raise ValueError('output already exists')
    if output.resolve() == allowed or not output.resolve().is_relative_to(allowed):
        raise ValueError('output must be a fresh child of build/repository_cleanup')
    prior_digest = digest(prior_path)
    prior = json.loads(prior_path.read_text())
    tools = [repo / 'tools' / name for name in
             ('regenerate_retention_graph.py', 'retention_dependencies.py', 'retention_paths.py', 'retention_tree.py')]
    tool_hashes = {str(p.relative_to(repo)): digest(p) for p in tools}
    old_hashes = {row['path']: row['sha256'] for row in prior['inputs']}
    names = sorted(set(old_hashes) | {row['path'] for row in prior['skipped_inputs']})
    for name in names:
        member_path(name)
    graph = dependency_graph(repo, [], input_paths=names)
    new_hashes = {row['path']: row['sha256'] for row in graph['inputs']}
    unchanged = {name for name in old_hashes if new_hashes.get(name) == old_hashes[name]}
    changes = [{'path': name, 'prior_sha256': old_hashes.get(name),
                'new_sha256': new_hashes.get(name),
                'status': 'changed_content' if name in old_hashes and name in new_hashes else
                          'newly_inspected' if name in new_hashes else 'not_inspected_now'}
               for name in names if name not in unchanged]
    def edges_for(data):
        return {(e['from'], e['to'], e['resolution']) for e in data['edges'] if e['from'] in unchanged}
    before, after = edges_for(prior), edges_for(graph)
    provenance = {'prior_graph': str(prior_path), 'prior_graph_sha256': prior_digest,
                  'tool_sha256': tool_hashes,
                  'input_set': 'exact union of prior inspected and skipped paths; no discovery',
                  'requested_input_count': len(names), 'unchanged_inspected_inputs': len(unchanged),
                  'identity_change_counts': dict(Counter(row['status'] for row in changes)),
                  'unchanged_source_edge_comparison': {'old': len(before), 'new': len(after),
                                                     'removed': len(before - after), 'added': len(after - before)},
                  'classification_changes': [], 'cleanup_authorized': False}
    capture_name = 'build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/capture.json'
    if digest(repo / capture_name) != new_hashes.get(capture_name):
        raise ValueError('actual capture source changed or was not inspected')
    capture = json.loads((repo / capture_name).read_text())
    expected = {Path(row['path']).relative_to(repo).as_posix() for row in capture['streams'].values()}
    found = {e['to'] for e in graph['edges'] if e['from'] == capture_name}
    resolved = all(e['resolution'] == 'exists' for e in graph['edges'] if e['from'] == capture_name)
    if found != expected or not resolved:
        raise ValueError('actual capture reference gate failed')
    if digest(prior_path) != prior_digest:
        raise ValueError('prior graph changed during regeneration')
    if any(digest(repo / name) != expected for name, expected in tool_hashes.items()):
        raise ValueError('graph tooling changed during regeneration')
    provenance['actual_capture_gate'] = {'status': 'PASS', 'from': capture_name,
                                       'expected_paths': sorted(expected), 'source_unchanged': capture_name in unchanged}
    graph['provenance'] = provenance
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [('dependency_graph.json', graph), ('source_identity_changes.json', changes),
                        ('regeneration_result.json', provenance)]:
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    result = {'output': str(output), 'input_count': len(graph['inputs']),
              'skipped_count': len(graph['skipped_inputs']), 'edge_count': len(graph['edges']), **provenance}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-graph', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    regenerate(Path(__file__).resolve().parents[1], args.prior_graph.absolute(), args.out.absolute())
