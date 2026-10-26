#!/usr/bin/env python3
"""Train a validated seven-node SPU SOM v1 map from a labeled CSV file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from som_map import SomMapError, load_map, write_map
from som_trainer import (
    DEFAULT_SCALE,
    SomTrainingError,
    build_map_document,
    load_csv_dataset,
)


def _csv_tokens(value: str) -> tuple[str, ...]:
    tokens = tuple(token.strip() for token in value.split(","))
    if any(not token for token in tokens):
        raise argparse.ArgumentTypeError("column/name lists cannot contain empty entries")
    return tokens


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", help="UTF-8 labeled CSV dataset")
    parser.add_argument("--output", "-o", required=True, help="output map JSON")
    parser.add_argument(
        "--features",
        type=_csv_tokens,
        default=("0", "1", "2", "3"),
        help="four comma-separated zero-based indices or header names",
    )
    parser.add_argument(
        "--label",
        default="4",
        help="zero-based label index or header name (default: 4)",
    )
    parser.add_argument(
        "--header", action="store_true", help="treat the first CSV row as a header"
    )
    parser.add_argument(
        "--feature-names",
        type=_csv_tokens,
        help="four artifact feature names (defaults to header names or feature_0..3)",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=DEFAULT_SCALE,
        help="exact decimal scale, constrained to a power of ten (default: 1000)",
    )
    parser.add_argument(
        "--model",
        help="stable model identifier; default is <csv-stem>-som-v1",
    )
    parser.add_argument(
        "--dataset-name", help="human-readable dataset name; default is CSV filename"
    )
    parser.add_argument(
        "--dataset-path",
        help="stable logical source path stored in the artifact; default is CSV filename",
    )
    args = parser.parse_args(argv)

    csv_path = Path(args.csv_file)
    model = args.model or f"{csv_path.stem}-som-v1"
    dataset_name = args.dataset_name or csv_path.name
    try:
        dataset = load_csv_dataset(
            csv_path,
            feature_columns=args.features,
            label_column=args.label,
            has_header=args.header,
            scale=args.scale,
            feature_names=args.feature_names,
        )
        document = build_map_document(
            dataset.samples,
            model=model,
            dataset=dataset_name,
            dataset_path=args.dataset_path or csv_path.name,
            dataset_sha256=dataset.sha256,
            scale=args.scale,
            feature_names=dataset.feature_names,
            class_names=dataset.class_names,
        )
        write_map(args.output, document)
        checked = load_map(args.output)
    except (OSError, SomMapError, SomTrainingError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"SOM_CSV_TRAIN: PASS rows={len(dataset.samples)} "
        f"classes={len(dataset.class_names)} map={checked['map_sha256']}"
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
