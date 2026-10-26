"""Independent logical action replay with rational-isolation boundary decisions."""
from .oracle import comparator


class Stop(Exception):
    pass


class Replay:
    def __init__(self, budget):
        self.budget, self.events, self.adjustments = budget, [], 0
        self.next_action = None

    def action(self, name, value, failure=None):
        self.next_action = name
        if len(self.events) >= self.budget:
            raise Stop('WORK_LIMIT')
        self.events.append(dict(action=name, value=value))
        if failure:
            raise Stop(failure)
        return value

    def width(self, name, value, bits, status):
        good = -(1 << (bits - 1)) <= value < (1 << (bits - 1))
        return self.action(name, value, None if good else status)

    def scalar(self, name, value, bits=136):
        self.action(name, value)
        return self.width(name + '.width', value, bits, 'TEMPORARY_LIMIT')

    def exponent(self, name, value):
        self.action(name, value)
        return self.width(name + '.signed32', value, 32, 'EXPONENT_OVERFLOW')

    def canonical(self, d, label):
        a, b, k = d
        if self.action(label + '.zero', a == b == 0):
            self.action(label + '.canonical_zero', k == 0, None if k == 0 else 'NONCANONICAL_INPUT')
            return
        c = comparator(a, b)
        self.action(label + '.lower', c['lower_sign'], 'NONCANONICAL_INPUT' if c['lower_sign'] < 0 else None)
        self.action(label + '.upper', c['upper_sign'], 'NONCANONICAL_INPUT' if c['upper_sign'] >= 0 else None)

    def normalize(self, state, allowance):
        a, b, k = state
        while True:
            c = comparator(a, b)
            low = self.action('scan.lower', c['lower_sign'])
            direction = 1 if low < 0 else 0
            if not direction:
                high = self.action('scan.upper', c['upper_sign'])
                if high < 0:
                    return (a, b, k)
                direction = -1
            if self.adjustments == allowance:
                raise Stop('WORK_LIMIT')
            exponent = self.exponent('adjust.exponent', k - direction)
            twice_a = self.scalar('adjust.2a', 2 * a)
            triple_b = self.scalar('adjust.3b', 3 * b)
            first = self.scalar('adjust.first', twice_a + direction * triple_b)
            identity_a = self.scalar('adjust.1a', a)
            twice_b = self.scalar('adjust.2b', 2 * b)
            second = self.scalar('adjust.second', twice_b + direction * identity_a)
            a, b, k = first, second, exponent
            self.adjustments += 1

    def final(self, state):
        for field, value, bits in zip(('a', 'b', 'k'), state, (64, 64, 32)):
            status = 'MANTISSA_OVERFLOW' if bits == 64 else 'EXPONENT_OVERFLOW'
            self.width('final.' + field, value, bits, status)
        return self.action('atomic.commit', tuple(state))

    def norm(self, state):
        a, b, _ = state
        aa = self.scalar('norm.aa', a * a, 280)
        bb = self.scalar('norm.bb', b * b, 280)
        triple = self.scalar('norm.3bb', 3 * bb, 280)
        return self.scalar('norm.difference', aa - triple, 280)

    def product(self, left, right):
        a, b, _ = left; c, d, _ = right
        ac = self.scalar('product.ac', a * c)
        bd = self.scalar('product.bd', b * d)
        triple = self.scalar('product.3bd', 3 * bd)
        first = self.scalar('product.first', ac + triple)
        ad = self.scalar('product.ad', a * d)
        bc = self.scalar('product.bc', b * c)
        return first, self.scalar('product.second', ad + bc)

    def observation(self, call, destination):
        try:
            result, status = call(), 'OK'
        except Stop as refusal:
            result, status = None, str(refusal)
        published = result if status == 'OK' and self.events[-1]['action'] == 'atomic.commit' else destination
        return dict(status=status, result=result, destination=published, charged_units=len(self.events),
                    adjustments=self.adjustments, events=tuple(self.events), next_action=self.next_action)
