"""Independent certificate checker: no imports from the symbolic producer."""
import json


def check(data):
    try:
        if type(data) is not bytes or len(data) > 16384:
            raise ValueError("size")
        def pairs(items):
            d = {}
            for k, v in items:
                if k in d:
                    raise ValueError("duplicate")
                d[k] = v
            return d
        c = json.loads(data.decode("ascii"), object_pairs_hook=pairs)
        if json.dumps(c, sort_keys=True, separators=(",", ":")).encode("ascii") != data:
            raise ValueError("canonical")
        if type(c) is not dict or set(c) != {"format", "version", "domain", "form", "sequence", "composition"}:
            raise ValueError("schema")
        if c["format"] != "SYMREG-GEOM" or type(c["version"]) is not int or c["version"] != 1 or c["domain"] != "Qsqrt3-vectors-2" or c["form"] != "x2+y2":
            raise ValueError("version")
        seq = c["sequence"]
        if type(seq) is not list or len(seq) > 32:
            raise ValueError("sequence")
        product = [[1, 0], [0, 1]]
        for m in seq:
            if type(m) is not list or len(m) != 2 or any(type(row) is not list or len(row) != 2 for row in m):
                raise ValueError("matrix")
            if any(type(v) is not int or abs(v) > 2 for row in m for v in row):
                raise ValueError("entry")
            a, b, c0, d = m[0][0], m[0][1], m[1][0], m[1][1]
            product = [[a*product[0][0]+b*product[1][0], a*product[0][1]+b*product[1][1]],
                       [c0*product[0][0]+d*product[1][0], c0*product[0][1]+d*product[1][1]]]
            if any(abs(v) > 1024 for row in product for v in row):
                raise ValueError("resource")
        if c["composition"] != product or any(type(v) is not int for row in c["composition"] for v in row):
            raise ValueError("composition")
        a, b = product[0]; c0, d = product[1]
        if (a*a+c0*c0, a*b+c0*d, b*b+d*d) != (1, 0, 1):
            raise ValueError("not universally preserving")
        return {"status": "VERIFIED", "scope": "universal matrix identity", "steps": len(seq)}
    except (ValueError, TypeError, UnicodeError, KeyError, IndexError, RecursionError, OverflowError):
        return {"status": "REJECTED"}


if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "rb") as f:
        result = check(f.read(16385))
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result["status"] == "VERIFIED" else 1)
