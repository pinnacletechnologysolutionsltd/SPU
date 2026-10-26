#!/usr/bin/env python3
"""Canonical boot-sequence FSM oracle tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.boot_sequence_oracle import (
    BootConfig,
    BootInputs,
    BootSequenceOracle,
    BootState,
    enumerate_reachable,
    generate_configs,
    ready_inputs_for_cycle,
)


passed = 0
failed = 0


def check(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {msg}")
    else:
        failed += 1
        print(f"  FAIL  {msg}")


def run_case(fn):
    try:
        fn()
    except Exception as exc:
        check(False, f"{fn.__name__}: unexpected exception {exc}")


def test_watchdog_boundary():
    cfg = BootConfig(enable_ve=True, enable_rplu=True,
                     enable_som=True).with_derived_watchdog()
    check(cfg.watchdog_cycles == 149, "watchdog derives to max enabled hydration length")

    oracle = BootSequenceOracle(cfg)
    oracle.step(BootInputs())
    for cycle in range(cfg.watchdog_cycles):
        snap = oracle.step(ready_inputs_for_cycle(cfg, cycle))
    check(snap.state == BootState.HYDRATING,
          "hydration remains active before the watchdog boundary")
    snap = oracle.step(ready_inputs_for_cycle(cfg, cfg.watchdog_cycles))
    check(snap.state == BootState.READY, "hydration completing at bound reaches READY")

    oracle = BootSequenceOracle(cfg)
    oracle.step(BootInputs())
    for _ in range(cfg.watchdog_cycles + 1):
        snap = oracle.step(BootInputs())
    check(snap.state == BootState.FAULT_HYDRATION_TIMEOUT,
          "hydration missing bound+1 faults")


def test_disabled_subsystem_join_configs():
    seen = 0
    for cfg in generate_configs():
        seen += 1
        oracle = BootSequenceOracle(cfg)
        oracle.step(BootInputs())
        ready_at = cfg.watchdog_cycles
        snap = oracle.step(ready_inputs_for_cycle(cfg, ready_at))
        if cfg.watchdog_cycles == 0:
            check(snap.state == BootState.READY,
                  "all-disabled configuration collapses join immediately")
        else:
            check(snap.state == BootState.READY,
                  f"enabled join reaches READY for config {cfg}")
    check(seen == 8, "all 2^3 generate combinations enumerated")


def test_instruction_acceptance_invariant():
    for cfg in generate_configs():
        transitions = enumerate_reachable(cfg, cfg.watchdog_cycles + 3)
        bad = [
            (before, after)
            for before, _inputs, after in transitions
            if after.instr_accepted and before.state != BootState.READY
        ]
        check(not bad, f"no non-READY instruction accept for config {cfg}")


def test_fault_terminal_except_reset():
    cfg = BootConfig(enable_ve=True, enable_rplu=True,
                     enable_som=True).with_derived_watchdog()
    transitions = enumerate_reachable(cfg, cfg.watchdog_cycles + 3)
    bad = [
        (inputs, after)
        for before, inputs, after in transitions
        if before.state == BootState.FAULT_HYDRATION_TIMEOUT
        and not inputs.reset
        and after.state != BootState.FAULT_HYDRATION_TIMEOUT
    ]
    check(not bad, "hydration fault has no outgoing edge except explicit reset")

    reset_edges = [
        after for before, inputs, after in transitions
        if before.state == BootState.FAULT_HYDRATION_TIMEOUT and inputs.reset
    ]
    check(reset_edges and all(edge.state == BootState.RESET for edge in reset_edges),
          "explicit reset exits hydration fault to RESET")


if __name__ == "__main__":
    print("=== Boot sequence FSM oracle tests ===")
    for case in (
        test_watchdog_boundary,
        test_disabled_subsystem_join_configs,
        test_instruction_acceptance_invariant,
        test_fault_terminal_except_reset,
    ):
        run_case(case)

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print("FAIL")
        sys.exit(1)
    print("PASS")
