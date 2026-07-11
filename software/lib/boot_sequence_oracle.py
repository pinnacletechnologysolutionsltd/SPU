#!/usr/bin/env python3
"""Exact finite-state oracle for the canonical SPU boot sequence."""

from dataclasses import dataclass
from enum import IntEnum
from itertools import product
from typing import Iterable, List, Tuple


class BootState(IntEnum):
    RESET = 0
    HYDRATING = 1
    READY = 2
    FAULT_HYDRATION_TIMEOUT = 3


@dataclass(frozen=True)
class BootConfig:
    enable_ve: bool = True
    enable_rplu: bool = False
    enable_som: bool = False
    ve_cycles: int = 13
    rplu_cycles: int = 149
    som_cycles: int = 28
    watchdog_cycles: int = 149

    def enabled_lengths(self) -> List[int]:
        lengths: List[int] = []
        if self.enable_ve:
            lengths.append(self.ve_cycles)
        if self.enable_rplu:
            lengths.append(self.rplu_cycles)
        if self.enable_som:
            lengths.append(self.som_cycles)
        return lengths

    def derived_watchdog(self) -> int:
        lengths = self.enabled_lengths()
        return max(lengths) if lengths else 0

    def with_derived_watchdog(self) -> "BootConfig":
        return BootConfig(
            enable_ve=self.enable_ve,
            enable_rplu=self.enable_rplu,
            enable_som=self.enable_som,
            ve_cycles=self.ve_cycles,
            rplu_cycles=self.rplu_cycles,
            som_cycles=self.som_cycles,
            watchdog_cycles=self.derived_watchdog(),
        )


@dataclass(frozen=True)
class BootInputs:
    reset: bool = False
    ve_ready: bool = False
    rplu_ready: bool = False
    som_ready: bool = False
    instr_valid: bool = False


@dataclass(frozen=True)
class BootSnapshot:
    state: BootState
    elapsed: int
    instr_accepted: bool


class BootSequenceOracle:
    def __init__(self, config: BootConfig):
        self.config = config
        self.state = BootState.RESET
        self.elapsed = 0
        self.instr_accepted = False

    def join_ready(self, inputs: BootInputs) -> bool:
        return (
            (inputs.ve_ready or not self.config.enable_ve) and
            (inputs.rplu_ready or not self.config.enable_rplu) and
            (inputs.som_ready or not self.config.enable_som)
        )

    def step(self, inputs: BootInputs) -> BootSnapshot:
        self.instr_accepted = False

        if inputs.reset:
            self.state = BootState.RESET
            self.elapsed = 0
            return self.snapshot()

        if self.state == BootState.RESET:
            self.state = BootState.HYDRATING
            self.elapsed = 0
        elif self.state == BootState.HYDRATING:
            if self.join_ready(inputs):
                self.state = BootState.READY
            else:
                self.elapsed += 1
                if self.elapsed > self.config.watchdog_cycles:
                    self.state = BootState.FAULT_HYDRATION_TIMEOUT
        elif self.state == BootState.READY:
            self.instr_accepted = inputs.instr_valid
        elif self.state == BootState.FAULT_HYDRATION_TIMEOUT:
            pass

        return self.snapshot()

    def snapshot(self) -> BootSnapshot:
        return BootSnapshot(self.state, self.elapsed, self.instr_accepted)


def ready_inputs_for_cycle(config: BootConfig, cycle: int,
                           instr_valid: bool = False) -> BootInputs:
    return BootInputs(
        ve_ready=(cycle >= config.ve_cycles),
        rplu_ready=(cycle >= config.rplu_cycles),
        som_ready=(cycle >= config.som_cycles),
        instr_valid=instr_valid,
    )


def generate_configs() -> Iterable[BootConfig]:
    for enable_ve, enable_rplu, enable_som in product((False, True), repeat=3):
        yield BootConfig(enable_ve, enable_rplu, enable_som).with_derived_watchdog()


def enumerate_reachable(config: BootConfig, depth: int
                        ) -> List[Tuple[BootSnapshot, BootInputs, BootSnapshot]]:
    start = (BootState.RESET, 0)
    frontier = {start}
    transitions: List[Tuple[BootSnapshot, BootInputs, BootSnapshot]] = []
    input_space = [
        BootInputs(reset=reset, ve_ready=ve, rplu_ready=rplu,
                   som_ready=som, instr_valid=instr)
        for reset, ve, rplu, som, instr in product((False, True), repeat=5)
    ]

    for _ in range(depth):
        next_frontier = set()
        for state, elapsed in frontier:
            for inputs in input_space:
                oracle = BootSequenceOracle(config)
                oracle.state = state
                oracle.elapsed = elapsed
                before = oracle.snapshot()
                after = oracle.step(inputs)
                transitions.append((before, inputs, after))
                next_frontier.add((after.state, after.elapsed))
        frontier = next_frontier
    return transitions
