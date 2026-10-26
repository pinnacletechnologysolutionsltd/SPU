"""Adapters invoke candidate and independent verification; qualification orchestration."""
from copy import deepcopy
from importlib import import_module
from . import codec, mutations, obligations, oracle


def observe(scope, fixture, operations):
    api = import_module('software.research.aor_s1.execute')
    if scope == 'operation':
        args = codec.arguments(fixture['operation'], fixture['arguments'])
        initial = codec.destination(fixture['initial_destination'])
        before = deepcopy(args)
        result = api.execute(fixture['operation'], args, initial, budget=fixture['budget'])
        if not codec.identical(args, before):
            raise RuntimeError('CANDIDATE_INPUT_MUTATION')
        return codec.plain(result)
    if scope == 'kernel':
        return codec.plain(api.run_kernel(tuple(fixture['input_mantissa']), fixture['input_exponent'],
                                         fixture['work_budget'], fixture['adjustment_allowance']))
    if scope == 'comparator':
        return codec.plain(import_module('software.research.aor_s1.comparator').probe(*fixture['mantissa']))
    source = operations[fixture['fixture_id']]
    registers = {k: tuple(v) for k, v in fixture['pre_state'].items()}
    initial = deepcopy(registers)
    args = codec.arguments(source['operation'], source['arguments'])
    count = 1 if source['operation'] == 'step' else len(args)
    args = tuple(registers[f'R{i}'] if i < count else item for i, item in enumerate(args))
    result = api.execute(source['operation'], args, registers[fixture['destination']], budget=source['budget'])
    if registers != initial:
        raise RuntimeError('ALIASED_SOURCE_MUTATION')
    post = dict(registers)
    post[fixture['destination']] = result.destination
    return codec.plain(dict(status=result.status, post_state=post, input_snapshot=registers, outcome=result))


def check(scope, fixture, observed, record=None):
    if scope == 'operation':
        return obligations.operation(fixture, observed, record)
    if scope == 'kernel':
        return obligations.kernel(fixture, observed)
    if scope == 'comparator':
        return obligations.comparison(fixture, observed)
    return obligations.alias(fixture, observed)


def run(groups, controls):
    operations = {f['id']: f for f in groups['operation']}
    index = {scope: {f['id']: f for f in rows} for scope, rows in groups.items()}
    rows, clean = [], {}
    for scope, fixtures in groups.items():
        for fixture in fixtures:
            observation = observe(scope, fixture, operations)
            record = oracle.answer(fixture) if scope == 'operation' else None
            labels = check(scope, fixture, observation, record)
            clean[(scope, fixture['id'])] = observation
            rows.append(dict(scope=scope, id=fixture['id'], expected=fixture, observed=observation,
                             oracle=record, rejections=sorted(labels), passed=not labels))
    control_rows, candidate_rows = [], {}
    for control in controls:
        scope, name = control['scope'], control['fixture_id']
        fixture = index[scope][name]; baseline = clean[(scope, name)]
        baseline_labels = check(scope, fixture, baseline)
        layer = control['layer']
        if layer == 'CANDIDATE':
            changed = mutations.candidate(control, baseline, lambda: observe(scope, fixture, operations))
            labels = check(scope, fixture, changed)
            different = not codec.identical(baseline, changed)
            candidate_rows[control['id']] = (changed, labels, control['required_rejection'])
            clean_observation = baseline
        elif layer == 'ORACLE':
            clean_observation = oracle.answer(fixture)
            changed = mutations.oracle(control, clean_observation)
            labels = check(scope, fixture, baseline, changed)
            different = not codec.identical(clean_observation, changed)
        else:
            corrupted, original_labels, required = candidate_rows[control['paired_candidate_control']]
            changed_labels, labels = mutations.checker_meta(original_labels, required)
            clean_observation = dict(observation=corrupted, rejections=sorted(original_labels))
            changed = dict(observation=corrupted, rejections=sorted(changed_labels))
            different = required in original_labels and required not in changed_labels
        passed = not baseline_labels and different and control['required_rejection'] in labels
        control_rows.append(dict(id=control['id'], layer=layer, baseline=clean_observation,
                                 candidate_baseline=baseline, injection=control['injection_mode'],
                                 adapter_source='software/research/aor_s1_verification/mutations.py',
                                 changed=changed, baseline_rejections=sorted(baseline_labels),
                                 changed_observation=different, rejections=sorted(labels), passed=passed))
    failures = [r for r in rows + control_rows if not r['passed']]
    return dict(fixtures=rows, controls=control_rows, first_counterexample=failures[0] if failures else None,
                passed=all(r['passed'] for r in rows + control_rows),
                limitations='Software evidence only; repository and synthesis gates pending')
