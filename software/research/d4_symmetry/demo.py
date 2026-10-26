"""Small deterministic D4 orbit-addressing demonstration."""

import argparse
import json
from pathlib import Path

from software.research.lattice_comparison import d4

from .canonical import GROUP, canonicalize, orbit
from .memory import OrbitMemory


def build_result():
    source = (1, 2, 4, 7)
    variants = orbit(source)
    memory = OrbitMemory()
    memory.store(source, "example-association", action=(1, 0, 0, 0))
    retrieved = [memory.lookup(value) for value in variants]
    return {
        "group_order": len(GROUP),
        "source": source,
        "orbit_size": len(variants),
        "raw_distinct_keys": len(variants),
        "canonical_keys": 1,
        "canonical_candidate_evaluations": len(GROUP),
        "canonical_key": canonicalize(source)[0],
        "witness": canonicalize(source)[1],
        "memory_entries": len(memory),
        "all_payloads_retrieved": all(row[0] == "example-association" for row in retrieved),
        "all_actions_reconstructed": all(
            action == d4.act(element, (1, 0, 0, 0))
            for element, action in zip(
                (next(g for g in GROUP if d4.act(g, source) == value) for value in variants),
                (row[1] for row in retrieved),
            )
        ),
        "claim_scope": "bounded exact orbit-addressing demonstration; no performance claim",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise SystemExit("refusing to overwrite output: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_result(), indent=2, sort_keys=True) + "\n")
    print(target)


if __name__ == "__main__":
    main()
