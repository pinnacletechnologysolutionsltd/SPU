#!/usr/bin/env python3
"""Generate MCU inputs from the frozen reconstruction; no training."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = "6dcbb8e73597e0172531eca15baf3c2d666827e056c1eede45e59ab019188de6"


def initializer(value):
    if isinstance(value, list):
        return "{" + ",".join(map(initializer, value)) + "}"
    return str(value)


def generate(path):
    data = (ROOT / "docs/bench_captures/2026-09-08_spu4_ina226_freeze.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError("freeze hash changed")
    folds = json.loads(data)["folds"]
    lines = ["/* Generated; use tools/gen_spu4_benchmark_header.py. */",
             '#include "spu4_ina226_kernel.h"',
             'typedef struct { uint16_t w[4][4]; int32_t low[4], high[4]; uint8_t labels[4]; } bench_model;',
             'typedef struct { int32_t raw[32], features[4]; uint16_t scaled[4]; uint32_t distance; uint8_t fold, node, label; } bench_case;',
             f'#define FREEZE_SHA "{SHA}"',
             'static const bench_model models[5] = {']
    for fold in folds:
        lines.append(initializer([fold["weights_p"], fold["scaler"]["minima"],
                                  fold["scaler"]["maxima"], fold["labels"]]) + ",")
    lines += ['};', 'static const bench_case cases[120] = {']
    for fold in folds:
        for case in fold["cases"]:
            lines.append(initializer([case["raw_uA"], case["features"], case["scaled"],
                                      case["distance"], fold["fold"], case["best"],
                                      case["label"]]) + ",")
    lines += ['};', '']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    generate(parser.parse_args().output)
