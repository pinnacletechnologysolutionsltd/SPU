"""Small symbolic producer; composition reads no concrete vectors."""
import json

IDENTITY = ((1, 0), (0, 1))
QUARTER = ((0, -1), (1, 0))


def compose(left, right):
    return tuple(tuple(sum(left[i][k] * right[k][j] for k in range(2))
                       for j in range(2)) for i in range(2))


def certificate(sequence):
    total = IDENTITY
    for matrix in sequence:
        total = compose(matrix, total)
    obj = {"format": "SYMREG-GEOM", "version": 1, "domain": "Qsqrt3-vectors-2",
           "form": "x2+y2", "sequence": sequence, "composition": total}
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("ascii")
