"""Coefficient truth by signed recurrence, independent of ladder evaluation."""


def integer(value):
    if type(value) is not int:
        raise TypeError('exact integer required')
    return value


def step(pair, delta, charge=lambda kind, stage: None):
    charge('ENTER','signed_recurrence')
    for name in ('a_type','b_type','delta_type','delta_domain'):
        charge('K',name)
    a, b = map(integer, pair)
    if integer(delta) not in (-1, 1):
        raise ValueError('signed unit step required')
    # Oracle arithmetic has a separate reference ledger, never candidate counts.
    charge('M', 'two_a'); two_a = 2 * a
    charge('M', 'three_b'); three_b = 3 * b
    charge('A', 'next_a'); next_a = two_a + three_b if delta == 1 else two_a - three_b
    charge('M', 'two_b'); two_b = 2 * b
    charge('A', 'next_b'); next_b = two_b + a if delta == 1 else two_b - a
    return next_a, next_b


def coefficients(exponent, charge=lambda kind, stage: None):
    charge('ENTER','coefficient_recurrence')
    charge('K','exponent_type')
    integer(exponent)
    pair = (1, 0)
    charge('COPY','identity_a'); charge('COPY','identity_b')
    charge('K','sign'); charge('N','magnitude')
    delta = -1 if exponent < 0 else 1
    for index in range(abs(exponent)):
        pair = step(pair, delta,
                    lambda kind, stage: charge(kind, str(index) + '.' + stage))
    return pair


def product(left, right, charge=lambda kind, stage: None):
    charge('ENTER','general_product')
    for name in ('a_type','b_type','c_type','d_type'):
        charge('K',name)
    a, b = map(integer, left)
    c, d = map(integer, right)
    charge('M', 'ac'); ac = a * c
    charge('M', 'bd'); bd = b * d
    charge('M', 'three_bd'); three_bd = 3 * bd
    charge('M', 'ad'); ad = a * d
    charge('M', 'bc'); bc = b * c
    charge('A', 'a'); out_a = ac + three_bd
    charge('A', 'b'); out_b = ad + bc
    return out_a, out_b


def norm(pair, charge=lambda kind, stage: None):
    charge('ENTER','general_norm')
    charge('K','a_type'); charge('K','b_type')
    a, b = map(integer, pair)
    charge('M', 'aa'); aa = a * a
    charge('M', 'bb'); bb = b * b
    charge('M', 'three_bb'); bb3 = 3 * bb
    charge('A', 'difference')
    return aa - bb3


class Truth:
    def __init__(self):
        self.sources, self.recurrent_product = [(1, 0), (1, 0)], (1, 0)

    def advance(self, target, delta, charge=lambda kind, stage: None):
        if type(target) is not int or target not in (0, 1):
            raise ValueError('source target required')
        source = step(self.sources[target], delta, charge)
        combined = step(self.recurrent_product, delta, charge)
        self.sources[target], self.recurrent_product = source, combined

    def observe(self, charge=lambda kind, stage: None):
        checked = product(*self.sources, charge=charge)
        charge('K', 'product_check')
        if checked != self.recurrent_product:
            raise AssertionError('independent product disagreement')
        pairs = self.sources + [checked]
        norms = [norm(pair, charge) for pair in pairs]
        for index in range(3):
            charge('K', 'norm_check.' + str(index))
        if norms != [1, 1, 1]:
            raise AssertionError('unit norm invariant')
        charge('K', 'equality')
        return pairs, norms, self.sources[0] == self.sources[1]
