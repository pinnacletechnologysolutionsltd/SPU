"""Deterministic finite-domain D4-NL-0 equivariance and width report."""

import argparse
import json
from itertools import product
from pathlib import Path

from software.research.lattice_comparison import d4

from . import nonlinear


BOUND = 4
OPERATORS = (("radial", nonlinear.radial),
             ("cubic_coupled", nonlinear.cubic_coupled),
             ("odd_threshold", nonlinear.odd_threshold))


def domain():
    return tuple(vector for vector in product(range(-BOUND, BOUND + 1), repeat=4)
                 if sum(vector) % 2 == 0)


def _direct_action(descriptor, vector):
    permutation, signs = descriptor
    return tuple(-vector[permutation[i]] if signs[i] else vector[permutation[i]]
                 for i in range(4))


def evaluate():
    states = domain()
    group = tuple(d4.group())
    if len(states) != 3281 or len(set(group)) != 192:
        raise AssertionError("D4_NL_FIXTURE_COUNTS")
    reports = {}
    for name, operator in OPERATORS:
        checks = 0
        max_observed = 0
        for vector in states:
            output = operator(vector)
            max_observed = max(max_observed, *(abs(value) for value in output))
            for element in group:
                lhs = operator(_direct_action(element, vector))
                rhs = _direct_action(element, output)
                checks += 1
                if lhs != rhs:
                    raise AssertionError("D4_NL_NOT_EQUIVARIANT:" + name)
        reports[name] = {"equivariance_checks": checks,
                         "all_exact": True,
                         "max_observed_output_magnitude": max_observed}
    return {
        "study": "D4-NL-0",
        "group_order": len(group),
        "domain": {"coordinates": [-BOUND, BOUND], "even_coordinate_sum": True,
                   "state_count": len(states)},
        "operator_results": reports,
        "widths": nonlinear.width_report(BOUND),
        "source_level_primitive_counts": nonlinear.primitive_counts(),
        "claim_scope": "exact equivariance on the frozen finite integer domain; no task, learning, runtime, energy, or hardware claim",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise SystemExit("refusing to overwrite output: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evaluate(), indent=2, sort_keys=True) + "\n")
    print(target)


if __name__ == "__main__":
    main()
