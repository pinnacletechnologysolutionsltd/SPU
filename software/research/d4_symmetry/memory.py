"""Associative addressing over exact D4 symmetry orbits."""

from software.research.lattice_comparison import d4

from .canonical import GROUP, canonicalize, inverse, validate_vector


class OrbitMemory:
    """Store invariant payloads and stabilizer-safe equivariant actions."""

    def __init__(self):
        self._entries = {}

    def __len__(self):
        return len(self._entries)

    def store(self, vector, payload, action=None):
        key, witness = canonicalize(vector)
        canonical_action = None
        if action is not None:
            action = validate_vector(action)
            canonical_action = d4.act(witness, action)
            for element in GROUP:
                if (d4.act(element, key) == key
                        and d4.act(element, canonical_action) != canonical_action):
                    raise ValueError("D4_ACTION_NOT_STABILIZER_FIXED")
        entry = (payload, canonical_action)
        if key in self._entries and self._entries[key] != entry:
            raise ValueError("D4_CONFLICTING_ASSOCIATION")
        self._entries[key] = entry
        return key

    def lookup(self, vector):
        key, witness = canonicalize(vector)
        if key not in self._entries:
            raise KeyError("D4_MEMORY_MISS")
        payload, canonical_action = self._entries[key]
        action = None
        if canonical_action is not None:
            action = d4.act(inverse(witness), canonical_action)
        return payload, action

    def keys(self):
        return tuple(sorted(self._entries))
