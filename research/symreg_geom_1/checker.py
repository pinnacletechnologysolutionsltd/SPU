"""Independent exact verifier; never imports the inference producer."""
import json


def matrix(m, limit):
    if (type(m) is not list or len(m) != 2 or
        any(type(r) is not list or len(r) != 2 for r in m) or
        any(type(v) is not int or abs(v) > limit for r in m for v in r)):
        raise ValueError("matrix")
    return m


def check(data):
    try:
        if type(data) is not bytes or len(data) > 16384:
            raise ValueError("size")
        def pairs(items):
            out = {}
            for k, v in items:
                if k in out:
                    raise ValueError("duplicate")
                out[k] = v
            return out
        c = json.loads(data.decode("ascii"), object_pairs_hook=pairs)
        if json.dumps(c, sort_keys=True, separators=(",", ":")).encode("ascii") != data:
            raise ValueError("canonical")
        if type(c) is not dict or set(c) != {"format", "version", "domain", "form", "sequence", "composition"}:
            raise ValueError("schema")
        if c["format"] != "SYMREG-GEOM" or type(c["version"]) is not int or c["version"] != 2 or c["domain"] != "Qsqrt3-vectors-2":
            raise ValueError("version")
        g = matrix(c["form"], 3)
        if g[0][1] != g[1][0]:
            raise ValueError("symmetric")
        if type(c["sequence"]) is not list or len(c["sequence"]) > 32:
            raise ValueError("length")
        p = [[1, 0], [0, 1]]
        for item in c["sequence"]:
            m = matrix(item, 4)
            p = [[m[0][0]*p[0][0]+m[0][1]*p[1][0], m[0][0]*p[0][1]+m[0][1]*p[1][1]],
                 [m[1][0]*p[0][0]+m[1][1]*p[1][0], m[1][0]*p[0][1]+m[1][1]*p[1][1]]]
            matrix(p, 4096)
        if matrix(c["composition"], 4096) != p:
            raise ValueError("composition")
        # Deliberately independent loops implement the full matrix product.
        actual = [[sum(p[k][i]*g[k][l]*p[l][j] for k in range(2) for l in range(2))
                   for j in range(2)] for i in range(2)]
        if actual != g:
            raise ValueError("not preserving")
        return {"status": "VERIFIED", "steps": len(c["sequence"]), "identity": "M^T G M = G"}
    except (ValueError, TypeError, UnicodeError, KeyError, IndexError, RecursionError, OverflowError):
        return {"status": "REJECTED"}


if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "rb") as f:
        result = check(f.read(16385))
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result["status"] == "VERIFIED" else 1)
