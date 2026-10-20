"""Byte-cycle raw loader and prepared-scene activation gate for T1d."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


SCENE_BITS = 504
PAYLOAD_BYTES = 63
SCENE_MASK = (1 << SCENE_BITS) - 1
T = TypeVar("T")


@dataclass(frozen=True)
class LoaderEvent:
    start_accepted: bool = False
    payload_accepted: bool = False
    packet_complete: bool = False
    bank_activated: bool = False


class RawSceneLoader:
    def __init__(self) -> None:
        self.banks = [0, 0]
        self.active_bank = 0
        self.receiving = False
        self.payload_count = 0
        self.commit_pending = False

    def tick(self, rx_valid: bool = False, rx_byte: int = 0,
             activate_raw_bank: bool = False) -> LoaderEvent:
        if type(rx_byte) is not int or not 0 <= rx_byte <= 255:
            raise ValueError("rx_byte must be an unsigned byte")
        if self.commit_pending:
            if activate_raw_bank:
                self.active_bank ^= 1
                self.commit_pending = False
                return LoaderEvent(bank_activated=True)
            return LoaderEvent()
        if self.receiving:
            if not rx_valid:
                return LoaderEvent()
            target = self.active_bank ^ 1
            self.banks[target] = ((self.banks[target] >> 8) | (rx_byte << (SCENE_BITS - 8))) & SCENE_MASK
            self.payload_count += 1
            if self.payload_count == PAYLOAD_BYTES:
                self.payload_count = 0
                self.receiving = False
                self.commit_pending = True
                return LoaderEvent(payload_accepted=True, packet_complete=True)
            return LoaderEvent(payload_accepted=True)
        if rx_valid and rx_byte == 0xA5:
            self.receiving = True
            self.payload_count = 0
            return LoaderEvent(start_accepted=True)
        return LoaderEvent()

    def packet_for_bank(self, bank: int) -> bytes:
        if bank not in (0, 1):
            raise ValueError("bank must be 0 or 1")
        return b"\xA5" + self.banks[bank].to_bytes(PAYLOAD_BYTES, "little")

    @property
    def active_packet(self) -> bytes:
        return self.packet_for_bank(self.active_bank)

    @property
    def candidate_packet(self) -> bytes:
        return self.packet_for_bank(self.active_bank ^ 1)


@dataclass(frozen=True)
class ControlEvent(Generic[T]):
    prepare0: bool = False
    prepare1: bool = False
    activate: bool = False
    active0: T | None = None
    active1: T | None = None


class PreparedSceneControl(Generic[T]):
    def __init__(self) -> None:
        self.preparing = False
        self.candidate_generation = 0
        self.ready0_seen = False
        self.ready1_seen = False
        self.result_generation0 = 0
        self.result_generation1 = 0
        self.active0: T | None = None
        self.active1: T | None = None

    def tick(self, commit_pending: bool, frame_start: bool,
             ready0: bool = False, ready1: bool = False,
             candidate0: T | None = None, candidate1: T | None = None) -> ControlEvent[T]:
        activate = (self.preparing and commit_pending and self.ready0_seen and self.ready1_seen
                    and self.result_generation0 == self.candidate_generation
                    and self.result_generation1 == self.candidate_generation and frame_start)
        if not self.preparing and commit_pending:
            self.candidate_generation ^= 1
            self.ready0_seen = self.ready1_seen = False
            self.preparing = True
            return ControlEvent(True, True, False, self.active0, self.active1)
        if self.preparing:
            if ready0:
                self.ready0_seen = True
                self.result_generation0 = self.candidate_generation
            if ready1:
                self.ready1_seen = True
                self.result_generation1 = self.candidate_generation
            if activate:
                self.active0, self.active1 = candidate0, candidate1
                self.ready0_seen = self.ready1_seen = False
                self.preparing = False
        return ControlEvent(False, False, activate, self.active0, self.active1)
