"""Limited counter and direct Pell references; different domains are explicit."""


def counter_steps(count):
    exponent = 0
    for _ in range(count):
        next_exponent = exponent + 1
        if not -(1 << 31) <= next_exponent < (1 << 31):
            return dict(status='EXPONENT_OVERFLOW',exponent=exponent)
        exponent = next_exponent
    return dict(status='OK',exponent=exponent,
                domain='Mantissa-one forward steps only; no mixed mantissas or full AOR API')


def direct_pell(count, signed64):
    real, radical = 1,0
    for completed in range(count):
        # Independent recurrence, no bounded-model arithmetic kernel.
        candidate_real = 2*real + 3*radical
        candidate_radical = real + 2*radical
        if signed64 and not (-(1 << 63) <= candidate_real < (1 << 63)
                             and -(1 << 63) <= candidate_radical < (1 << 63)):
            return dict(status='COEFFICIENT_OVERFLOW',completed=completed,
                        real=real,radical=radical)
        real,radical = candidate_real,candidate_radical
    return dict(status='OK',completed=count,real=real,radical=radical)
