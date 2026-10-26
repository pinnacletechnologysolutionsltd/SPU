#!/usr/bin/env python3
"""Emit exact TGR1 golden fixtures and a small machine-readable manifest."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from lib.tensegrity_abi import encode_status, encode_table  # noqa: E402
from lib.tensegrity_vectors import golden_vectors, run_oracle  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "tools" / "build" / "tensegrity_vectors")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for vector in golden_vectors():
        state, fault = run_oracle(vector.system)
        if (state, fault) != (vector.expected_state, vector.expected_fault):
            raise RuntimeError(f"{vector.name}: oracle result {state}/{fault} disagrees with golden expectation")
        table = encode_table(vector.system)
        status = encode_status(state, fault, vector.vector_id)
        table_name = f"{vector.vector_id:02d}_{vector.name}.tgr"
        status_name = f"{vector.vector_id:02d}_{vector.name}.status"
        (args.output_dir / table_name).write_bytes(table)
        (args.output_dir / status_name).write_bytes(status)
        manifest.append({
            "id": vector.vector_id,
            "name": vector.name,
            "table": table_name,
            "status": status_name,
            "table_bytes": len(table),
            "state": state.name,
            "fault": fault.name,
        })
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"TGR1: emitted {len(manifest)} vectors to {args.output_dir}")


if __name__ == "__main__":
    main()
