"""Standalone, bounded certificate verifier. No SYMREG inference imports."""
import hashlib
import json

DOMAIN = "Qsqrt3-integers-v1"
VALUE_SCALES = frozenset((-2, -1, 0, 1, 2))
NORM_SCALES = frozenset((-4, -2, -1, 0, 1, 2, 4))
MAX_BYTES, MAX_VALUES, MAX_BRANCHES, MAX_PREMISES, MAX_STEPS, MAX_DEPTH = 65536, 64, 3, 256, 128, 32


class Refusal(Exception):
    def __init__(self, code):
        self.code = code


def require(condition, code="INVALID"):
    if not condition:
        raise Refusal(code)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "DUPLICATE_KEY")
        result[key] = value
    return result


def parse(data):
    require(type(data) is bytes, "INVALID_ENCODING")
    require(len(data) <= MAX_BYTES, "RESOURCE_LIMIT")
    try:
        obj = json.loads(data.decode("ascii"), object_pairs_hook=_pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(Refusal("INVALID_ENCODING")))
        require(canonical(obj) == data, "NON_CANONICAL")
        return obj
    except Refusal:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise Refusal("INVALID_ENCODING")


def fields(obj, keys):
    require(type(obj) is dict and set(obj) == set(keys), "SCHEMA")


def ident(value):
    return type(value) is str and 1 <= len(value) <= 32 and value.isascii() and all(c.isalnum() or c in "_-" for c in value)


def descriptor(obj, values):
    fields(obj, ("kind", "source", "target", "k", "flip"))
    kind, a, b, k, flip = (obj[x] for x in ("kind", "source", "target", "k", "flip"))
    require(kind in ("value", "norm") and ident(a) and ident(b) and a in values and b in values, "DESCRIPTOR")
    require(type(k) is int and type(flip) is bool, "DESCRIPTOR")
    require((kind == "value" and k in VALUE_SCALES and (k != 0 or not flip)) or
            (kind == "norm" and k in NORM_SCALES and not flip), "UNSUPPORTED")
    return (kind, a, b, k, flip)


def exact_truth(desc, values):
    kind, x, y, k, flip = desc
    a, b = values[x]; c, d = values[y]
    if kind == "value":
        return (c, d) == (k*a, -k*b if flip else k*b)
    return c*c - 3*d*d == k*(a*a - 3*b*b)


def check_context(ctx):
    fields(ctx, ("version", "domain", "scope", "values", "branches"))
    require(type(ctx["version"]) is int and ctx["version"] == 1 and ctx["domain"] == DOMAIN, "UNSUPPORTED")
    require(ident(ctx["scope"]), "SCHEMA")
    values, branches = ctx["values"], ctx["branches"]
    require(type(values) is dict and type(branches) is dict, "SCHEMA")
    require(1 <= len(values) <= MAX_VALUES and 1 <= len(branches) <= MAX_BRANCHES, "RESOURCE_LIMIT")
    for key, pair in values.items():
        require(ident(key) and type(pair) is list and len(pair) == 2, "SCHEMA")
        require(all(type(v) is int and -(1 << 63) <= v < (1 << 63) for v in pair), "UNSUPPORTED")
    total = 0
    for name, branch in branches.items():
        require(ident(name), "SCHEMA")
        fields(branch, ("bindings", "premises"))
        bindings, premises = branch["bindings"], branch["premises"]
        require(type(bindings) is dict and type(premises) is dict, "SCHEMA")
        require(len(bindings) <= 8, "RESOURCE_LIMIT")
        for reg, value in bindings.items():
            require(reg in tuple("r" + str(i) for i in range(8)) and ident(value) and value in values, "BINDING")
        total += len(premises)
        require(total <= MAX_PREMISES, "RESOURCE_LIMIT")
        for name, claim in premises.items():
            require(ident(name), "SCHEMA")
            require(exact_truth(descriptor(claim, values), values), "FALSE_PREMISE")
    return values, branches


def _verify(cert_data, context_data):
    ctx = parse(context_data); values, branches = check_context(ctx)
    cert = parse(cert_data)
    fields(cert, ("version", "domain", "scope", "context_sha256", "branches", "steps", "conclusion"))
    require(type(cert["version"]) is int and cert["version"] == 1 and cert["domain"] == DOMAIN, "UNSUPPORTED")
    require(cert["scope"] == ctx["scope"], "STALE_SCOPE")
    require(cert["context_sha256"] == hashlib.sha256(context_data).hexdigest(), "STALE_CONTEXT")
    require(type(cert["branches"]) is list and cert["branches"] == sorted(branches), "BRANCH_COVERAGE")
    steps = cert["steps"]
    require(type(steps) is list and 1 <= len(steps) <= MAX_STEPS, "RESOURCE_LIMIT")
    verified = []; depths = []; used_premises = set()
    for index, step in enumerate(steps):
        fields(step, ("branch", "rule", "claim", "inputs", "premise"))
        branch, rule, refs = step["branch"], step["rule"], step["inputs"]
        require(type(branch) is str and branch in branches and type(refs) is list, "SCHEMA")
        claim = descriptor(step["claim"], values)
        if rule == "PREMISE":
            require(refs == [] and ident(step["premise"]) and step["premise"] in branches[branch]["premises"], "UNTRUSTED_PREMISE")
            expected = descriptor(branches[branch]["premises"][step["premise"]], values)
            require(claim == expected and exact_truth(expected, values), "FALSE_PREMISE")
            used_premises.add((branch, step["premise"]))
            depth = 1
        else:
            require(step["premise"] is None and rule in ("COMPOSE", "NORM"), "UNSUPPORTED_RULE")
            require(len(refs) == (2 if rule == "COMPOSE" else 1) and
                    all(type(r) is int and 0 <= r < index for r in refs), "REFERENCE")
            require(all(verified[r][0] == branch for r in refs), "CROSS_BRANCH")
            depth = 1 + max(depths[r] for r in refs)
            require(depth <= MAX_DEPTH, "RESOURCE_LIMIT")
            first = verified[refs[0]][1]
            if rule == "NORM":
                require(first[0] == "value", "RULE")
                expected = ("norm", first[1], first[2], first[3]**2, False)
            else:
                second = verified[refs[1]][1]
                require(first[0] == second[0] and first[2] == second[1], "RULE")
                k = first[3]*second[3]
                require(k in (VALUE_SCALES if first[0] == "value" else NORM_SCALES), "UNSUPPORTED")
                flip = (first[4] != second[4]) if first[0] == "value" and k else False
                expected = (first[0], first[1], second[2], k, flip)
            require(claim == expected, "RULE")
        verified.append((branch, claim)); depths.append(depth)
    conclusion = cert["conclusion"]
    fields(conclusion, ("rule", "claim", "witnesses", "current"))
    require(conclusion["rule"] == "ALL_FEASIBLE_PATHS", "UNSUPPORTED_RULE")
    goal = descriptor(conclusion["claim"], values)
    witnesses = conclusion["witnesses"]
    require(type(witnesses) is dict and set(witnesses) == set(branches), "BRANCH_COVERAGE")
    for name, ref in witnesses.items():
        require(type(ref) is int and 0 <= ref < len(verified), "REFERENCE")
        require(verified[ref] == (name, goal), "BRANCH_WITNESS")
    current = conclusion["current"]
    if current is not None:
        fields(current, ("source", "target"))
        require(all(type(current[k]) is str and current[k] in tuple("r" + str(i) for i in range(8)) for k in ("source", "target")), "BINDING")
        for branch in branches.values():
            require(branch["bindings"].get(current["source"]) == goal[1] and
                    branch["bindings"].get(current["target"]) == goal[2], "STALE_BINDING")
    return {"status": "VERIFIED", "steps": len(steps), "premises": len(used_premises), "depth": max(depths), "branches": len(branches)}


def verify(cert_data, context_data):
    try:
        return _verify(cert_data, context_data)
    except Refusal as exc:
        return {"status": "REJECTED", "reason": exc.code}


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Verify canonical SYMREG certificate against a trusted context")
    parser.add_argument("certificate")
    parser.add_argument("context")
    args = parser.parse_args()
    try:
        with open(args.certificate, "rb") as f: certificate = f.read(MAX_BYTES + 1)
        with open(args.context, "rb") as f: trusted_context = f.read(MAX_BYTES + 1)
        result = verify(certificate, trusted_context)
    except OSError as exc:
        result = {"status": "REJECTED", "reason": "IO", "detail": str(exc)}
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result["status"] == "VERIFIED" else 1)
