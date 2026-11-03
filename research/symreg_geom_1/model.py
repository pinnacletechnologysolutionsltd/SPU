"""Certificate producer with symbolic matrix composition."""
import json


def compose(left, right):
    return [[sum(left[i][k]*right[k][j] for k in range(2)) for j in range(2)]
            for i in range(2)]


def certificate(form, sequence):
    total = [[1, 0], [0, 1]]
    for matrix in sequence:
        total = compose(matrix, total)
    return json.dumps({"format": "SYMREG-GEOM", "version": 2,
                       "domain": "Qsqrt3-vectors-2", "form": form,
                       "sequence": sequence, "composition": total},
                      sort_keys=True, separators=(",", ":")).encode("ascii")
