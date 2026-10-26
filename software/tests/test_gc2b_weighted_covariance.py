#!/usr/bin/env python3
"""Bounded exact GC-2B finite-fixture qualification command."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software" / "lib"))

from gc2b_weighted_cycle import (  # noqa: E402
    Q3, admissible_rotations, apply_f, apply_left, apply_right, p_transport,
    q3, q_map, rotate, trajectory, transported_weights, vector,
    vector_payload,
)
from rational_field import MultiSurd  # noqa: E402


def must(condition, message):
    if not condition:
        raise AssertionError(message)


def read_vec(items):
    return vector(tuple(Q3(int(p), int(q)) for p, q in items))


def basis(i):
    return vector(tuple(1 if j == i else 0 for j in range(4)))


def mvalue(value):
    return MultiSurd(value.p, value.q)


def mtransport(x):
    return tuple(x[(-j) % 4] for j in range(4))


def mleft(x, weights):
    out = [MultiSurd(0)] * 4
    for i in range(4):
        out[(i + 1) % 4] = weights[i] * x[i]
    return tuple(out)


def mright(x, weights):
    return tuple(weights[i] * x[(i + 1) % 4] for i in range(4))


def mf(x, weights, a, b):
    lft, rgt = mleft(x, weights), mright(x, weights)
    return tuple(mvalue(a) * lft[i] + mvalue(b) * rgt[i]
                 for i in range(4))


def check_independent_oracle(x, weights, a, b):
    main = apply_f(x, weights, a, b)
    other = mf(tuple(mvalue(v) for v in x),
               tuple(mvalue(v) for v in weights), a, b)
    must(all(mvalue(v) == w for v, w in zip(main, other)),
         "Q3 and MultiSurd field/matrix results differ")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest
    manifest = json.loads(manifest_path.read_text())
    state = read_vec(manifest["state"])
    law_neutral = tuple(read_vec((pair,))[0] for pair in manifest["law_neutral"])
    law_biased = tuple(read_vec((pair,))[0] for pair in manifest["law_biased"])
    steps = int(manifest["steps"])
    executed = []
    details = {}
    fixture_results = []

    for fixture in manifest["fixtures"]:
        fid = fixture["id"]
        weights = read_vec(fixture["weights"])
        wp = transported_weights(weights)
        must(all(w.is_positive() for w in weights + wp),
             f"{fid}: nonpositive edge weight")

        # Operator exchange and the two covariance laws on the full basis.
        for i in range(4):
            x = basis(i)
            lhs_l = p_transport(apply_left(x, weights))
            rhs_l = apply_right(p_transport(x), wp)
            lhs_r = p_transport(apply_right(x, weights))
            rhs_r = apply_left(p_transport(x), wp)
            must(lhs_l == rhs_l and lhs_r == rhs_r,
                 f"{fid}: basis operator exchange failed at e_{i}")
        executed.append(f"{fid}.basis_operator_exchange.all4")
        details[f"{fid}.basis_operator_exchange.all4"] = "PASS"

        for label, (a, b) in (("neutral", law_neutral), ("biased", law_biased)):
            residuals = []
            for i in range(4):
                x = basis(i)
                lhs = p_transport(apply_f(x, weights, a, b))
                rhs = apply_f(p_transport(x), wp, b, a)
                must(lhs == rhs, f"{fid}: {label} covariance failed at e_{i}")
                residuals.append(vector_payload(tuple(lhs[j] - rhs[j] for j in range(4))))
                check_independent_oracle(x, weights, a, b)
                check_independent_oracle(p_transport(x), wp, b, a)
            cid = f"{fid}.covariance.{label}.all4"
            executed.append(cid)
            details[cid] = {"status": "PASS", "a": a.to_pair(), "b": b.to_pair(),
                            "basis_residuals": residuals,
                            "independent_oracles": ["Q3/Fraction-pair", "MultiSurd/general-basis"]}

        actual_h = admissible_rotations(weights, wp)
        expected_h = fixture["admissible_rotations"]
        must(actual_h == expected_h,
             f"{fid}: admissible rotations {actual_h} != {expected_h}")
        cid = f"{fid}.admissible_h.exhaustive"
        executed.append(cid)
        details[cid] = {"tested_rotations": [0, 1, 2, 3], "admissible": actual_h}

        # Trajectory covariance is checked for n=0..8, with transported seeds.
        for label, (a, b) in (("neutral", law_neutral), ("biased", law_biased)):
            lhs_states = trajectory(p_transport(state), wp, b, a, steps)
            rhs_states = tuple(p_transport(v) for v in trajectory(state, weights, a, b, steps))
            must(lhs_states == rhs_states, f"{fid}: {label} trajectory covariance failed")
            cid = f"{fid}.trajectory.substrate_covariance.{label}"
            executed.append(cid)
            details[cid] = {"steps_checked": list(range(steps + 1)), "status": "PASS",
                            "lhs_states": [vector_payload(v) for v in lhs_states],
                            "rhs_states": [vector_payload(v) for v in rhs_states]}

        # Independent fault injections, each with its own witness.
        e0 = basis(0)
        correct_first = p_transport(apply_left(e0, weights))
        double_swap = apply_left(p_transport(e0), wp)
        must(correct_first != double_swap,
             f"{fid}: double left/right swap was not detected")
        cid = f"{fid}.negative.double_swap"
        executed.append(cid)
        details[cid] = {"status": "DETECTED", "correct": vector_payload(correct_first),
                        "faulty": vector_payload(double_swap)}

        corrupted = list(wp)
        corrupted[0] = corrupted[0] + 1
        correct_second = p_transport(apply_right(e0, weights))
        faulty_second = apply_left(p_transport(e0), tuple(corrupted))
        must(correct_second != faulty_second,
             f"{fid}: edge-weight transport fault was not detected")
        cid = f"{fid}.negative.weight_transport"
        executed.append(cid)
        details[cid] = {"status": "DETECTED", "correct": vector_payload(correct_second),
                        "faulty": vector_payload(faulty_second)}

        if actual_h:
            neutral_commutators = {}
            biased_commutators = {}
            for k in actual_h:
                # Q=h_*P_*; verify operator symmetry by all basis vectors.
                neutral_rows = []
                biased_rows = []
                for i in range(4):
                    x = basis(i)
                    qfx = rotate(p_transport(apply_f(x, weights, *law_neutral)), k)
                    fqx = apply_f(q_map(x, k), weights, *law_neutral)
                    must(qfx == fqx, f"{fid}: neutral internal symmetry failed for h={k}")
                    qfx_b = rotate(p_transport(apply_f(x, weights, *law_biased)), k)
                    fqx_b = apply_f(q_map(x, k), weights, *law_biased)
                    must(qfx_b != fqx_b,
                         f"{fid}: biased internal symmetry unexpectedly held for h={k}")
                    neutral_rows.append(vector_payload(tuple(qfx[j] - fqx[j] for j in range(4))))
                    biased_rows.append(vector_payload(tuple(qfx_b[j] - fqx_b[j] for j in range(4))))
                neutral_commutators[str(k)] = neutral_rows
                biased_commutators[str(k)] = biased_rows
                # Neutral and coefficient-exchanged biased trajectory pairs.
                qx = q_map(state, k)
                f_qx = trajectory(qx, weights, *law_neutral, steps)
                q_f = tuple(q_map(v, k) for v in trajectory(state, weights, *law_neutral, steps))
                must(f_qx == q_f, f"{fid}: neutral Q trajectory relation failed for h={k}")
                f_qx_b = trajectory(qx, weights, law_biased[1], law_biased[0], steps)
                q_f_b = tuple(q_map(v, k) for v in trajectory(state, weights, *law_biased, steps))
                must(f_qx_b == q_f_b,
                     f"{fid}: biased exchanged-coefficient trajectory relation failed for h={k}")
            cid = f"{fid}.internal.neutral.all_h"
            executed.append(cid)
            details[cid] = {"status": "PASS", "h": actual_h,
                            "commutator_columns_by_h": neutral_commutators}
            cid = f"{fid}.internal.biased.noncommuting.all_h"
            executed.append(cid)
            details[cid] = {"status": "EXPECTED_NONZERO", "h": actual_h,
                            "commutator_columns_by_h": biased_commutators}
            cid = f"{fid}.trajectory.neutral.all_h"
            executed.append(cid)
            details[cid] = {"status": "PASS", "steps_checked": list(range(steps + 1)), "h": actual_h,
                            "paired_states": {str(k): {
                                "F_n_Qx": [vector_payload(v) for v in trajectory(q_map(state, k), weights, *law_neutral, steps)],
                                "Q_F_n_x": [vector_payload(q_map(v, k)) for v in trajectory(state, weights, *law_neutral, steps)]
                            } for k in actual_h}}
            cid = f"{fid}.trajectory.biased.all_h"
            executed.append(cid)
            details[cid] = {"status": "PASS", "steps_checked": list(range(steps + 1)), "h": actual_h,
                            "paired_states": {str(k): {
                                "F_ba_n_Qx": [vector_payload(v) for v in trajectory(q_map(state, k), weights, law_biased[1], law_biased[0], steps)],
                                "Q_F_ab_n_x": [vector_payload(q_map(v, k)) for v in trajectory(state, weights, *law_biased, steps)]
                            } for k in actual_h}}
            omitted = state
            transported = p_transport(state)
            must(omitted != transported, f"{fid}: state-transport negative control is not distinct")
            cid = f"{fid}.negative.state_transport"
            executed.append(cid)
            details[cid] = {"status": "DETECTED_AT_STEP_ZERO",
                            "original": vector_payload(omitted),
                            "transported": vector_payload(transported)}
        else:
            cid = f"{fid}.internal.not_applicable_no_h"
            executed.append(cid)
            details[cid] = {"status": "NOT_APPLICABLE_NO_ADMISSIBLE_H"}

        fixture_results.append({"id": fid, "weights": vector_payload(weights),
                                "mirrored_weights": vector_payload(wp),
                                "admissible_rotations": actual_h})

    declared_fixtures = {fixture["id"] for fixture in manifest["fixtures"]}
    expected_checks = {check for fixture in manifest["fixtures"] for check in fixture["checks"]}
    must(len(declared_fixtures) == len(manifest["fixtures"]), "duplicate declared fixture ID")
    must(len(expected_checks) == sum(len(fixture["checks"]) for fixture in manifest["fixtures"]),
         "duplicate declared check ID")
    must(len(executed) == len(set(executed)), "duplicate check execution ID")
    must(set(details) == set(executed), "detail/execution ID mismatch")
    must(set(details) == expected_checks,
         f"declared/executed check mismatch: missing={sorted(expected_checks-set(details))}, "
         f"extra={sorted(set(details)-expected_checks)}")
    must({r["id"] for r in fixture_results} == declared_fixtures,
         "declared/executed fixture mismatch")

    report = {
        "contract_id": manifest["contract_id"],
        "status": "BOUNDED_FINITE_FIXTURES_PASS",
        "qualification_scope": "These fixtures/operators only; no general theorem or physical claim.",
        "domain": manifest["domain"],
        "fixed_real_embedding": "sqrt(3) -> positive real root",
        "independent_arithmetic_implementations": [
            "Q3/Fraction-pair exact field arithmetic",
            "rational_field.MultiSurd general four-component basis arithmetic",
        ],
        "fixtures": fixture_results,
        "initial_state": vector_payload(state),
        "steps": steps,
        "checks": details,
        "declared_fixture_ids": sorted(declared_fixtures),
        "executed_fixture_ids": sorted(r["id"] for r in fixture_results),
        "declared_check_ids": sorted(expected_checks),
        "executed_check_ids": sorted(executed),
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (Path(__file__).resolve(), Path(__file__).resolve().parents[1] / "lib" / "gc2b_weighted_cycle.py", manifest_path.resolve(), ROOT / "spu_strategy" / "contract_gc2b_weighted_geometry_2026-10-16.md")
        },
        "argv": sys.argv,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"GC-2B PASS: {len(expected_checks)} declared checks matched execution")
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
