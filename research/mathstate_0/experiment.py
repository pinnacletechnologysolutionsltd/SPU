"""Bounded mathematical modes and selected explicit-denominator reference."""
U = ((2, 3), (1, 2))
INV = ((2, -3), (-1, 2))
NEG = ((-1, 0), (0, -1))
ID = ((1, 0), (0, 1))
LOW, HIGH = -(1 << 63), (1 << 63) - 1


def multiply(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2)) for i in range(2))


def apply(m, v):
    return tuple(sum(m[i][j]*v[j] for j in range(2)) for i in range(2))


def power(n):
    result = ID
    for _ in range(abs(n)):
        result = multiply(U if n >= 0 else INV, result)
    return result


def width(n):
    return n.bit_length() + 1 if n >= 0 else (~n).bit_length() + 1


def run(start, matrices):
    value = start
    max_width = max(map(width, value))
    for i, m in enumerate(matrices, 1):
        nxt = apply(m, value)
        max_width = max(max_width, *(map(width, nxt)))
        if any(x < LOW or x > HIGH for x in nxt):
            return {"status": 2, "refusal": i, "value": value,
                    "valid": True, "maximum_width": max_width}
        value = nxt
    return {"status": 0, "refusal": None, "value": value,
            "valid": True, "maximum_width": max_width}


def fuse(start, matrices):
    m = ID
    for matrix in matrices:
        m = multiply(matrix, m)
    result = apply(m, start)
    return {"matrix": m, "value": result,
            "matrix_width": max(width(v) for row in m for v in row),
            "result_width": max(map(width, result))}


def fixtures():
    x = apply(power(-17), (1, 0))
    return {"F1": ((1, 0), [U, U]),
            "F2": (x, [U]*34),
            "F3": (((1 << 63)-1, 0), [U, INV]),
            "F4": ((2, 3), [U, NEG]),
            "F7": ((3, -2), [U, INV])}


def certified(start, matrices, status, intermediate_observed):
    # A proposed sufficient condition, not an RTL-validated compiler rewrite.
    # The caller also assumes no observer of omitted retirement/write events.
    if matrices != [U, INV] or status != 0 or intermediate_observed:
        return "UNKNOWN"
    if not all(-16 <= x <= 16 for x in start):
        return "UNKNOWN"
    return "CONDITIONAL_FINAL_STATE_ONLY"


def cost_report():
    for name, (initial, seq) in fixtures().items():
        eager, fused = run(initial, seq), fuse(initial, seq)
        cyclic = all(m in (U, INV) for m in seq)
        exponent = sum(1 if m == U else -1 for m in seq) if cyclic else None
        print(name, "EAGER", eager, "tuple_ops", len(seq) if eager['refusal'] is None else eager['refusal'],
              "successful_materializations", len(seq) if eager['refusal'] is None else eager['refusal']-1,
              "resident_tuple_bits", 192, "initial_valid", True, "initial_status", 0)
        print(name, "FUSED", fused, "matrix_compositions", len(seq), "materializations", 1)
        if cyclic:
            print(name, "GENERATOR exponent", exponent, "retained_exponent_bits", width(exponent),
                  "power_width", max(width(v) for row in power(exponent) for v in row),
                  "power_matrix_compositions", abs(exponent), "materializations", 1)
        else:
            print(name, "GENERATOR unsupported")
        print(name, "CERTIFIED", certified(initial, seq, 0, False),
              "if_intermediate_read", certified(initial, seq, 0, True))


if __name__ == '__main__':
    cost_report()
