"""Exact scalar operation vectors and modeled bits, not hardware cycle estimates."""
from collections import Counter
from fractions import Fraction


def signed_bits(value):
    return (value if value >= 0 else ~value).bit_length() + 1


def bits(value):
    if type(value) is int:
        return signed_bits(value)
    if type(value) is Fraction:
        return signed_bits(value.numerator) + value.denominator.bit_length()
    if type(value) in (list, tuple):
        return sum(bits(v) for v in value)
    raise ValueError('ACCOUNTING_TYPE')


class Work:
    def __init__(self):
        self.counts, self.peak_numerator_bits, self.peak_denominator_bits = Counter(), 0, 0
        self.peak_scalar_bits = 0

    def watch(self, value):
        if type(value) is Fraction:
            self.peak_numerator_bits = max(self.peak_numerator_bits, signed_bits(value.numerator))
            self.peak_denominator_bits = max(self.peak_denominator_bits, value.denominator.bit_length())
        else:
            self.peak_scalar_bits = max(self.peak_scalar_bits, signed_bits(value))
        return value

    def operation(self, name, left, right):
        self.watch(left); self.watch(right)
        self.counts[name] += 1
        if type(left) is Fraction or type(right) is Fraction:
            self.counts['fraction_normalization_calls'] += 1
            a, b = Fraction(left), Fraction(right)
            if name == 'multiply':
                raw = a.numerator * b.numerator, a.denominator * b.denominator
                self.counts['fraction_schoolbook_multiply'] += 2
            else:
                first, second = a.numerator * b.denominator, b.numerator * a.denominator
                self.watch(first); self.watch(second)
                raw = first + (1 if name == 'add' else -1) * second, a.denominator * b.denominator
                self.counts['fraction_schoolbook_multiply'] += 3
                self.counts['fraction_schoolbook_' + name] += 1
            for v in raw:
                self.watch(v)
        result = left + right if name == 'add' else left - right if name == 'subtract' else left * right
        return self.watch(result)

    def report(self):
        return dict(operations=dict(sorted(self.counts.items())),
                    peak_scalar_bits=self.peak_scalar_bits, peak_numerator_bits=self.peak_numerator_bits,
                    peak_denominator_bits=self.peak_denominator_bits,
                    fraction_growth_model='schoolbook; not CPython GCD internals',
                    gcd_internal_steps='NOT COUNTED', python_memory='UNMEASURED')
