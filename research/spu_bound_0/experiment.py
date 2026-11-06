"""Exact integer exploration; no Gen-1 instruction semantics are modeled."""
from itertools import product

U = ((2, 3), (1, 2))
V = ((2, -3), (-1, 2))
I = ((1, 0), (0, 1))


def width(x):
    return (x if x >= 0 else ~x).bit_length() + 1


def compose(m, n):
    return tuple(tuple(sum(m[i][k] * n[k][j] for k in range(2)) for j in range(2)) for i in range(2))


def extrema(m, box):
    return tuple((sum(min(c * lo, c * hi) for c, (lo, hi) in zip(row, box)),
                  sum(max(c * lo, c * hi) for c, (lo, hi) in zip(row, box))) for row in m)


def direct(v, sign):
    # Pair multiplication by (2, sign), independent of matrix code.
    a, b = v
    return (2*a + 3*sign*b, sign*a + 2*b)


def cases():
    x = (1, 0)
    for _ in range(17):
        x = direct(x, -1)
    return [('cancel-box', ((-2, 2), (-2, 2)), [1, -1]),
            ('mixed-box', ((-2, 2), (-1, 1)), [1, 1, -1, 1]),
            ('contract', ((x[0], x[0]), (x[1], x[1])), [1]*34),
            ('refusal', (((1 << 63)-1, (1 << 63)-1), (0, 0)), [1, -1]),
            ('small-cancel', ((3, 3), (-2, -2)), [1, -1])]


def analyze(box, seq):
    vals = list(product(*(range(lo, hi+1) for lo, hi in box)))
    matrix, interval = I, box
    max_coeff = max(width(x) for v in vals for x in v)
    max_temp = max_coeff
    matrix_width = 1
    exact_bounds, interval_bounds, actual = [], [], []
    for sign in seq:
        m = U if sign == 1 else V
        matrix = compose(m, matrix)
        matrix_width = max(matrix_width, *(width(x) for row in matrix for x in row))
        exact_bounds.append(extrema(matrix, box))
        interval = extrema(m, interval)
        interval_bounds.append(interval)
        next_vals = []
        for a, b in vals:
            # Products and sums used by the direct pair implementation.
            terms = (2*a, 3*sign*b, sign*a, 2*b)
            v = direct((a, b), sign)
            max_temp = max(max_temp, *(width(x) for x in terms + v))
            max_coeff = max(max_coeff, *(width(x) for x in v))
            next_vals.append(v)
        vals = next_vals
        actual.append(tuple((min(v[i] for v in vals), max(v[i] for v in vals)) for i in range(2)))
    return exact_bounds, interval_bounds, actual, max_coeff, max_temp, matrix_width, vals


def main():
    for name, box, seq in cases():
        exact, interval, observed, cw, tw, mw, vals = analyze(box, seq)
        n, exp = len(seq), sum(seq)
        assert exact == observed
        assert all(lo <= alo <= ahi <= hi for step, obs in zip(interval, observed)
                   for (lo, hi), (alo, ahi) in zip(step, obs))
        # Naive matrix multiplication: 8 multiplies + 4 adds per composition.
        print(f'{name}: inputs={len(vals)} steps={n} exponent={exp} signed_exp_bits={width(exp)}')
        print(f'  final exact={exact[-1]} interval={interval[-1]} observed={observed[-1]}')
        print(f'  widths: eager_coeff={cw} eager_products_and_sums={tw} prefix_matrix={mw}')
        print(f'  per input eager={4*n} mul + {2*n} add; fused={8*n+4} mul + {4*n+2} add; generator_linear={8*abs(exp)+4} mul + {4*abs(exp)+2} add')
        print(f'  bounds: matrix={8*n} mul + {4*n} add; endpoints={8*n} mul + {4*n} add; interval={8*n} mul + {4*n} add; checks={4*n*len(vals)} comparisons')
        print(f'  retained: original 2 coefficients; matrix 4 entries; generator exponent {width(exp)} bits; interval or exact current endpoints 4 integers')


if __name__ == '__main__':
    main()
