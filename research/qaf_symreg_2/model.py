"""Bounded sparse and rooted canonical relations over the SYMREG-1 store."""
from collections import deque
from dataclasses import dataclass

from research.qaf_symreg_1.model import Fact, Key, NORM_SCALES, VALUE_SCALES

MAX_WORK = 4096
MAX_DEPTH = 32
MAX_PROVENANCE = 256


def admit_checked(machine, source, target, scale=1, flip=False, norm=False):
    """Admit only checked concrete facts; distinguish false from unsupported."""
    if (type(source) is not int or type(target) is not int or
            source not in machine.known or target not in machine.known or
            type(scale) is not int or type(flip) is not bool or type(norm) is not bool):
        return "UNKNOWN", None
    if (norm and (scale not in NORM_SCALES or flip)) or (not norm and scale not in VALUE_SCALES):
        return "UNKNOWN", None
    fact = (machine.admit_norm(source, target, scale) if norm else
            machine.admit_value(source, target, scale, flip))
    return ("PROVEN", fact) if fact is not None else ("DISPROVEN", None)


@dataclass(frozen=True)
class Proof:
    source: int
    target: int
    scale: int
    flip: bool
    path: tuple
    norm: bool = False


def extend(scale, flip, edge):
    k = scale * edge.k
    if k not in VALUE_SCALES:
        return None
    return k, (flip != edge.flip if k else False)


def valid_provenance(machine, roots):
    """Check supported derivations, bounded DAG size/depth; base admission is trusted."""
    done = {}; active = set()

    def visit(fact, depth):
        if type(fact) is not Fact or type(fact.key) is not Key or type(fact.parents) is not tuple or fact.valid is not True or depth > MAX_DEPTH:
            return False
        ident = id(fact)
        if ident in active:
            return False
        if ident in done:
            return depth + done[ident] - 1 <= MAX_DEPTH
        if len(done) + len(active) >= MAX_PROVENANCE:
            return False
        active.add(ident)
        key, parents = fact.key, fact.parents
        if any(type(p) is not Fact or type(p.key) is not Key for p in parents):
            return False
        if key.source not in machine.known or key.target not in machine.known:
            return False
        if fact.rule == "concrete_checked":
            ok = not parents
        elif fact.rule == "merge_all_feasible":
            ok = bool(parents) and all(p.key == key for p in parents)
        elif fact.rule == "compose" and len(parents) == 2:
            x, y = parents[0].key, parents[1].key
            ok = x.kind == y.kind == key.kind and x.target == y.source
            if ok and x.kind == "value":
                desc = extend(x.k, x.flip, y)
                ok = desc is not None and key == type(key)("value", x.source, y.target, *desc)
            elif ok and x.kind == "norm":
                ok = x.k*y.k in NORM_SCALES and key == type(key)("norm", x.source, y.target, x.k*y.k)
            else:
                ok = False
        elif fact.rule == "norm_of_value" and len(parents) == 1:
            p = parents[0].key
            ok = p.kind == "value" and key == type(key)("norm", p.source, p.target, p.k*p.k)
        else:
            ok = False
        if not ok or not all(visit(p, depth+1) for p in parents):
            return False
        height = 1 + max((done[id(p)] for p in parents), default=0)
        active.remove(ident); done[ident] = height
        return True

    return all(visit(f, 1) for f in roots)


def validate(machine, proof, source, target, scale, flip=False, norm=False):
    """Recheck trusted path, binding and derivation; never read concrete values."""
    if any(type(v) is not int for v in (source, target, scale)) or type(flip) is not bool or type(norm) is not bool:
        return False
    if type(proof) is not Proof or type(proof.path) is not tuple or any(type(v) is not int for v in (proof.source, proof.target, proof.scale)) or type(proof.flip) is not bool or type(proof.norm) is not bool or (proof.source, proof.target, proof.scale, proof.flip, proof.norm) != (source, target, scale, flip if scale else False, norm):
        return False
    if len(proof.path) > MAX_DEPTH:
        return False
    if not valid_provenance(machine, proof.path):
        return False
    node, k, f = source, 1, False
    for fact in proof.path:
        if machine.facts.get(fact.key) is not fact or not fact.valid:
            return False
        edge = fact.key
        if edge.source != node or edge.kind not in (("value", "norm") if norm else ("value",)):
            return False
        if norm:
            k *= edge.k if edge.kind == "norm" else edge.k * edge.k
            if k not in NORM_SCALES:
                return False
        else:
            desc = extend(k, f, edge)
            if desc is None:
                return False
            k, f = desc
        node = edge.target
    return node == target and ((k == scale and not flip) if norm else (k, f) == (scale, flip if scale else False))


class Sparse:
    """Directed BFS over already-admitted base facts; no persistent closure."""
    def __init__(self, machine, max_work=MAX_WORK, max_depth=MAX_DEPTH):
        if type(max_work) is not int or not 0 <= max_work <= MAX_WORK:
            raise ValueError("work limit")
        if type(max_depth) is not int or not 0 <= max_depth <= MAX_DEPTH:
            raise ValueError("depth limit")
        self.machine, self.max_work, self.max_depth = machine, max_work, max_depth
        self.work = 0

    def prove(self, source, target, scale=1, flip=False, norm=False):
        self.work = 0
        if type(source) is not int or type(target) is not int or source not in self.machine.known or target not in self.machine.known:
            return "UNKNOWN", None
        if type(scale) is not int or type(flip) is not bool or type(norm) is not bool:
            return "UNKNOWN", None
        if (norm and (scale not in NORM_SCALES or flip)) or (not norm and scale not in VALUE_SCALES):
            return "UNKNOWN", None
        if source == target and scale == 1 and not flip:
            return "PROVEN", Proof(source, target, scale, False, (), norm)
        todo = deque([(source, 1, False, ())]); seen = {(source, 1, False)}
        while todo:
            node, k, f, path = todo.popleft()
            if len(path) >= self.max_depth:
                continue
            for fact in self.machine.facts.values():
                if self.work >= self.max_work:
                    return "RESOURCE_LIMIT", None
                self.work += 1
                edge = fact.key
                if edge.source != node or edge.kind not in (("value", "norm") if norm else ("value",)):
                    continue
                if norm:
                    nk, nf = k * (edge.k if edge.kind == "norm" else edge.k*edge.k), False
                    if nk not in NORM_SCALES:
                        continue
                else:
                    desc = extend(k, f, edge)
                    if desc is None:
                        continue
                    nk, nf = desc
                next_path = path + (fact,)
                matches = (nk == scale if norm else (nk, nf) == (scale, flip if scale else False))
                if edge.target == target and matches:
                    proof = Proof(source, target, scale, False if norm else nf, next_path, norm)
                    return ("PROVEN", proof) if validate(self.machine, proof, source, target, scale, flip, norm) else ("UNKNOWN", None)
                state = (edge.target, nk, nf)
                if state not in seen:
                    seen.add(state); todo.append((edge.target, nk, nf, next_path))
        return "UNKNOWN", None

    def current(self, source_reg, target_reg, scale=1, flip=False, norm=False):
        source = self.machine.identity(source_reg); target = self.machine.identity(target_reg)
        if source is None or target is None:
            return "UNKNOWN", None
        return self.prove(source, target, scale, flip, norm)


@dataclass(frozen=True)
class Descriptor:
    node: int
    scale: int
    flip: bool
    depth: int
    parent: object = None
    edge: object = None


class Canonical:
    """One rooted directed tree of canonical transformations and linked proof nodes."""
    def __init__(self, machine, root, max_depth=MAX_DEPTH):
        if type(root) is not int or root not in machine.known or type(max_depth) is not int or not 0 <= max_depth <= MAX_DEPTH:
            raise ValueError("root or depth")
        self.machine, self.root, self.max_depth = machine, root, max_depth
        self.nodes = {root: Descriptor(root, 1, False, 0)}
        self.work = 0

    def attach(self, fact):
        if type(fact) is not Fact or self.machine.facts.get(fact.key) is not fact or fact.key.kind != "value":
            return "UNKNOWN"
        edge = fact.key
        if edge.source not in self.nodes or edge.target in self.nodes:
            return "UNKNOWN"  # cycles and alternate paths remain in sparse graph
        parent = self.nodes[edge.source]
        if parent.depth >= self.max_depth:
            return "RESOURCE_LIMIT"
        desc = extend(parent.scale, parent.flip, edge)
        if desc is None:
            return "UNKNOWN"
        self.nodes[edge.target] = Descriptor(edge.target, *desc, parent.depth+1, parent, fact)
        return "STORED"

    def prove(self, source, target, scale=1, flip=False, norm=False):
        self.work = 0
        if type(source) is not int or type(target) is not int or type(scale) is not int or type(flip) is not bool or type(norm) is not bool:
            return "UNKNOWN", None
        if source != self.root or source not in self.machine.known or target not in self.machine.known:
            return "UNKNOWN", None
        if norm and (target not in self.nodes or scale != self.nodes[target].scale**2):
            fallback = Sparse(self.machine, max_depth=self.max_depth)
            answer = fallback.prove(source, target, scale, flip, norm=True)
            self.work = fallback.work
            return answer
        if target not in self.nodes:
            return "UNKNOWN", None
        node = self.nodes[target]
        if norm:
            if flip or scale != node.scale*node.scale:
                return "UNKNOWN", None
        elif (scale, flip if scale else False) != (node.scale, node.flip):
            return "UNKNOWN", None
        edges = []
        while node.parent is not None:
            self.work += 1
            if self.work > self.max_depth:
                return "RESOURCE_LIMIT", None
            edges.append(node.edge); node = node.parent
        proof = Proof(source, target, scale, False if norm else flip if scale else False, tuple(reversed(edges)), norm)
        return ("PROVEN", proof) if validate(self.machine, proof, source, target, scale, flip, norm) else ("UNKNOWN", None)
