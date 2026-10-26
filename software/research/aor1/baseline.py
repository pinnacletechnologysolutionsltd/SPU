"""Ordinary Surd mantissa plus exponent bookkeeping, with equivalent checks.

Uses the same checked arithmetic engine deliberately: comparison measures host
representation handling, not a second arithmetic algorithm or hardware advantage.
The mathematical oracle remains separate.
"""
from dataclasses import dataclass
from .bounded import execute


@dataclass
class MantissaCounter:
    mantissa: tuple = (17, -19)
    counter: int = 23
    norm_destination: int = 17

    def tuple(self):
        return (*self.mantissa, self.counter)

    def apply(self, operation, left, right=None, *, increment=None):
        destination = self.norm_destination if operation == 'NORM' else self.tuple()
        result = execute(operation, left, right, increment=increment, destination=destination)
        if result.committed:
            if operation == 'NORM':
                self.norm_destination = result.value
            else:
                # Sequential software model: no thread/concurrent atomicity claim.
                self.mantissa, self.counter = result.value[:2], result.value[2]
        return result
