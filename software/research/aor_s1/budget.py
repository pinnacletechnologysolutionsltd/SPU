"""Charge-before-action meter and exact checked scalar operations."""
from collections import Counter


class Refusal(Exception):
    """A specified finite-profile refusal, not an implementation defect."""


class InvariantError(RuntimeError):
    """A violated proof precondition or certified local invariant."""


def fits(value, bits):
    return -(1 << (bits - 1)) <= value < (1 << (bits - 1))


class Meter:
    def __init__(self, budget=4096):
        if type(budget) is not int or not 0 <= budget <= 4096:
            raise ValueError('invalid diagnostic budget configuration')
        self.budget = budget
        self.used = 0
        self.events = []
        self.adjustments = 0
        self.next_action = None
        self.primitive_counts = Counter()

    def action(self, name, calculate):
        self.next_action = name
        if self.used == self.budget:
            raise Refusal('WORK_LIMIT')
        self.used += 1
        value = calculate()
        self.events.append({'action': name, 'value': value})
        return value

    def test(self, name, calculate, failure=None):
        result = self.action(name, calculate)
        if failure is not None and not result:
            raise Refusal(failure)
        return result

    def width(self, name, value, bits, failure):
        def check():
            self.primitive_counts['width_checks'] += 1
            return value
        checked = self.action(name, check)
        if not fits(checked, bits):
            raise Refusal(failure)
        return checked

    def scalar(self, name, calculate, bits=136, kind='add'):
        def arithmetic():
            self.primitive_counts['scalar_' + kind] += 1
            return calculate()
        value = self.action(name, arithmetic)
        return self.width(name + '.width', value, bits, 'TEMPORARY_LIMIT')

    def exponent(self, name, calculate):
        def arithmetic():
            self.primitive_counts['exponent_arithmetic'] += 1
            return calculate()
        value = self.action(name, arithmetic)
        return self.width(name + '.signed32', value, 32, 'EXPONENT_OVERFLOW')
