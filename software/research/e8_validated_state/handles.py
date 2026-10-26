"""Identity-only registry keys and immutable, explicitly leased export records."""
from dataclasses import dataclass


class StateKey:
    __slots__ = ()


class BufferKey:
    __slots__ = ()


@dataclass(frozen=True)
class Export:
    payload: object
    key: BufferKey
