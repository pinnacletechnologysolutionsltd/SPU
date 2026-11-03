"""Adapters emit certificates from real SYMREG-1/2/3 proof objects."""
import hashlib

from research.qaf_symreg_1.model import Key, Machine
from research.qaf_symreg_2.model import Sparse
from research.qaf_symreg_3.model import BranchRoster, Join
from research.qaf_symreg_4.checker import DOMAIN, canonical


def desc(key):
    return {"kind": key.kind, "source": "v" + str(key.source), "target": "v" + str(key.target),
            "k": key.k, "flip": key.flip}


def emit_fact(fact, branch, premises, steps):
    if fact.rule == "concrete_checked":
        name = "p" + str(len(premises))
        premises[name] = desc(fact.key)
        step = {"branch": branch, "rule": "PREMISE", "claim": desc(fact.key), "inputs": [], "premise": name}
    else:
        rules = {"compose": "COMPOSE", "norm_of_value": "NORM"}
        if fact.rule not in rules:
            raise ValueError("unsupported source provenance")
        refs = [emit_fact(parent, branch, premises, steps) for parent in fact.parents]
        step = {"branch": branch, "rule": rules[fact.rule], "claim": desc(fact.key), "inputs": refs, "premise": None}
    steps.append(step)
    return len(steps)-1


def emit_path(path, branch, premises, steps):
    if not path:
        raise ValueError("reflexive proof not encoded in this experiment")
    ref = emit_fact(path[0], branch, premises, steps)
    accumulated = path[0].key
    for fact in path[1:]:
        other = emit_fact(fact, branch, premises, steps)
        edge = fact.key
        if accumulated.kind != "value" or edge.kind != "value":
            raise ValueError("adapter handles value paths only")
        k = accumulated.k*edge.k
        accumulated = Key("value", accumulated.source, edge.target, k,
                          (accumulated.flip != edge.flip) if k else False)
        steps.append({"branch": branch, "rule": "COMPOSE", "claim": desc(accumulated),
                      "inputs": [ref, other], "premise": None})
        ref = len(steps)-1
    return ref


def build_example(which):
    m = Machine()
    for i, pair in enumerate(((1, 2), (1, -2), (2, -4), (2, 2))):
        m.write(i, *pair)
    x, y, z, _ = m.reg[:4]
    steps, branches, witnesses = [], {}, {}
    goal = Key("value", x, z, 2, True)
    if which in (1, 2):
        first = m.admit_value(x, y, 1, True); second = m.admit_value(y, z, 2)
        branches["A"] = {"bindings": {"r0": "v" + str(x), "r2": "v" + str(z)}, "premises": {}}
        if which == 1:
            fact = m.project_norm(m.compose(first, second))
            goal = fact.key
            witnesses["A"] = emit_fact(fact, "A", branches["A"]["premises"], steps)
        else:
            result, proof = Sparse(m).prove(x, z, 2, True)
            if result != "PROVEN": raise RuntimeError("SYMREG-2 proof unavailable")
            witnesses["A"] = emit_path(proof.path, "A", branches["A"]["premises"], steps)
    elif which == 3:
        # y=conj(x), z=2y, w=2x, z=conj(w), with shared endpoint identities.
        m.write(3, 2, 4); w = m.reg[3]
        group = m.branch(None); a, b = group.paths[False], group.paths[True]
        a.admit_value(x, y, 1, True); a.admit_value(y, z, 2)
        b.admit_value(x, w, 2); b.admit_value(w, z, 1, True)
        join = Join(BranchRoster([("A", a), ("B", b)]), [goal])
        result, proof = join.prove(goal, current=(0, 2))
        if result != "PROVEN" or not join.validate(proof): raise RuntimeError("SYMREG-3 proof unavailable")
        for branch, path_proof in proof.witnesses:
            branches[branch] = {"bindings": {"r0": "v" + str(x), "r2": "v" + str(z)}, "premises": {}}
            witnesses[branch] = emit_path(path_proof.path, branch, branches[branch]["premises"], steps)
    else:
        raise ValueError("example")
    context = {"version": 1, "domain": DOMAIN, "scope": "symreg_example_" + str(which),
               "values": {"v" + str(i): list(value) for i, value in m.domain.values.items()}, "branches": branches}
    context_bytes = canonical(context)
    cert = {"version": 1, "domain": DOMAIN, "scope": context["scope"], "context_sha256": hashlib.sha256(context_bytes).hexdigest(),
            "branches": sorted(branches), "steps": steps,
            "conclusion": {"rule": "ALL_FEASIBLE_PATHS", "claim": desc(goal), "witnesses": witnesses,
                           "current": {"source": "r0", "target": "r2"}}}
    return context_bytes, canonical(cert)


if __name__ == "__main__":
    from research.qaf_symreg_4.checker import verify
    for number in (1, 2, 3):
        context, certificate = build_example(number)
        print("SYMREG", number, "certificate_bytes", len(certificate), verify(certificate, context))
