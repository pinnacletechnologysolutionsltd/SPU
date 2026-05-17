#!/usr/bin/env python3
"""Generate deterministic RPLU metric vectors from the checked-in tables.

This is deliberately stdlib-only. It is a reference harness for metrics and
golden vectors, not a visualization tool.
"""

import argparse
import csv
import json
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "hardware" / "rtl" / "arch"
BUILD = ROOT / "build"
DEFAULT_OUT = BUILD / "rplu_metrics"

OPCODE_RPLU_CFG = 0xA5
R_MIN_Q16 = 0x0000C51F
R_MAX_Q16 = 0x00024F5C
R_MAX_Q12 = 0x000024F5
R_ADDR_RECIP_Q16 = 664
VECTOR_ADDRS = [
    0, 1, 2, 3, 4, 7, 8, 15,
    16, 31, 32, 63, 64, 127, 128, 255,
    256, 383, 384, 511, 512, 639, 640, 767,
    768, 895, 896, 1000, 1016, 1021, 1022, 1023,
]


def read_hex_words(path):
    words = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].split("//", 1)[0].strip()
            if line:
                words.append(int(line.replace("_", ""), 16))
    return words


def u32(value):
    return value & 0xFFFFFFFF


def s32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def q16_float(value):
    return s32(value) / 65536.0


def build_header(sel, material, addr):
    header = (OPCODE_RPLU_CFG & 0xFF) << 56
    header |= (sel & 0x7) << 48
    header |= (material & 0x1) << 47
    header |= (addr & 0x3FF) << 37
    return header


def build_records(params, vnorm, dissoc, material):
    records = []
    for idx in range(3):
        records.append((build_header(0, material, idx), params[(material * 3) + idx] & 0xFFFFFFFF))
    for addr, value in enumerate(vnorm):
        records.append((build_header(5, material, addr), value & 0xFFFFFFFF))
    for addr, value in enumerate(dissoc):
        records.append((build_header(6, material, addr), value & 0x1))
    return records


def payload_bytes(records):
    out = bytearray()
    for header, data in records:
        out.extend(header.to_bytes(8, "big"))
        out.extend((data & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "big"))
    return bytes(out)


def record_checksum(header, data):
    return (
        ((header >> 32) & 0xFFFFFFFF)
        + (header & 0xFFFFFFFF)
        + ((data >> 32) & 0xFFFFFFFF)
        + (data & 0xFFFFFFFF)
    ) & 0xFFFFFFFF


def table_checksum(records):
    total = 0
    for header, data in records:
        total = (total + record_checksum(header, data)) & 0xFFFFFFFF
    return total


def radius_q12_to_addr(radius_q12):
    if radius_q12 >= R_MAX_Q12:
        r_q16 = R_MAX_Q16
    else:
        r_q16 = (radius_q12 << 4) & 0xFFFFFFFF
    return r_q16_to_addr(r_q16), r_q16


def r_q16_to_addr(r_q16):
    r_q16 = s32(r_q16)
    if r_q16 <= R_MIN_Q16:
        return 0
    if r_q16 >= R_MAX_Q16:
        return 1023
    scaled = (r_q16 - R_MIN_Q16) * R_ADDR_RECIP_Q16
    addr = scaled >> 16
    return 1023 if addr > 1023 else addr


def table_metrics(r_rom, vnorm, dissoc):
    v_min = min(vnorm)
    v_max = max(vnorm)
    r_signed = [s32(x) for x in r_rom]
    monotonic = all(r_signed[i] <= r_signed[i + 1] for i in range(len(r_signed) - 1))
    return {
        "entries": len(r_rom),
        "r_min_q16": f"0x{u32(r_signed[0]):08X}",
        "r_max_q16": f"0x{u32(r_signed[-1]):08X}",
        "r_min_float": q16_float(r_signed[0]),
        "r_max_float": q16_float(r_signed[-1]),
        "r_monotonic": monotonic,
        "v_min_q16": f"0x{v_min & 0xFFFFFFFF:08X}",
        "v_max_q16": f"0x{v_max & 0xFFFFFFFF:08X}",
        "v_min_float": v_min / 65536.0,
        "v_max_float": v_max / 65536.0,
        "dissoc_count": sum(1 for x in dissoc if x),
    }


def axis_metrics():
    cases = [
        ("zero", 0),
        ("below_min", max(0, (R_MIN_Q16 >> 4) - 2)),
        ("at_min", R_MIN_Q16 >> 4),
        ("mid", ((R_MIN_Q16 + R_MAX_Q16) // 2) >> 4),
        ("near_max", R_MAX_Q12 - 1),
        ("at_max", R_MAX_Q12),
        ("large_overflow_guard", 0x10000000),
        ("signed_high_guard", 0x7FFFFFFF),
    ]
    rows = []
    for name, radius_q12 in cases:
        addr, r_q16 = radius_q12_to_addr(radius_q12)
        rows.append({
            "case": name,
            "radius_q12_hex": f"0x{radius_q12 & 0xFFFFFFFF:08X}",
            "r_q16_hex": f"0x{r_q16 & 0xFFFFFFFF:08X}",
            "r_addr": addr,
        })
    return rows


def write_vectors(out_dir, r_rom, vnorm, dissoc):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with (out_dir / "rplu_addr.mem").open("w", encoding="utf-8") as f_addr, \
            (out_dir / "rplu_r_q16.mem").open("w", encoding="utf-8") as f_r, \
            (out_dir / "rplu_v_q16.mem").open("w", encoding="utf-8") as f_v, \
            (out_dir / "rplu_dissoc.mem").open("w", encoding="utf-8") as f_d:
        for addr in VECTOR_ADDRS:
            r_q16 = r_rom[addr] & 0xFFFFFFFF
            v_q16 = vnorm[addr] & 0xFFFFFFFF
            d = dissoc[addr] & 0x1
            mapped_addr = r_q16_to_addr(r_q16)
            rows.append({
                "addr": addr,
                "r_q16_hex": f"0x{r_q16:08X}",
                "r_float": q16_float(r_q16),
                "mapped_addr_from_r": mapped_addr,
                "v_q16_hex": f"0x{v_q16:08X}",
                "v_float": v_q16 / 65536.0,
                "dissoc": d,
            })
            f_addr.write(f"{addr:03x}\n")
            f_r.write(f"{r_q16:08x}\n")
            f_v.write(f"{v_q16:08x}\n")
            f_d.write(f"{d:x}\n")

    with (out_dir / "rplu_metric_vectors.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material", default="carbon", choices=["carbon"])
    parser.add_argument("--material-id", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--payload", type=Path, default=BUILD / "rplu_boot_chords.bin")
    parser.add_argument("--require-payload", action="store_true")
    args = parser.parse_args()

    params = read_hex_words(ARCH / "params_elements.hex")
    r_rom = read_hex_words(ARCH / f"r_rom_{args.material}.mem")
    vnorm = read_hex_words(ARCH / f"vnorm_{args.material}.mem")
    dissoc = read_hex_words(ARCH / f"vnorm_dissoc_{args.material}.mem")

    errors = []
    if len(params) < (args.material_id + 1) * 3:
        errors.append("params_elements.hex does not contain material parameter triplet")
    if len(r_rom) != 1024:
        errors.append(f"r_rom_{args.material}.mem has {len(r_rom)} entries, expected 1024")
    if len(vnorm) != 1024:
        errors.append(f"vnorm_{args.material}.mem has {len(vnorm)} entries, expected 1024")
    if len(dissoc) != 1024:
        errors.append(f"vnorm_dissoc_{args.material}.mem has {len(dissoc)} entries, expected 1024")
    if any(x not in (0, 1) for x in dissoc):
        errors.append("dissoc table contains values other than 0/1")

    records = build_records(params, vnorm, dissoc, args.material_id)
    expected_payload = payload_bytes(records)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "rplu_boot_chords_expected.bin").write_bytes(expected_payload)

    payload_matches = None
    if args.payload.exists():
        actual = args.payload.read_bytes()
        payload_matches = actual == expected_payload
        if not payload_matches:
            errors.append(f"{args.payload} does not match expected RPLU chord payload")
    elif args.require_payload:
        errors.append(f"missing required payload {args.payload}")

    metric_rows = write_vectors(args.out_dir, r_rom, vnorm, dissoc)
    summary = {
        "material": args.material,
        "material_id": args.material_id,
        "table": table_metrics(r_rom, vnorm, dissoc),
        "flash": {
            "records": len(records),
            "bytes": len(expected_payload),
            "crc32": f"0x{zlib.crc32(expected_payload) & 0xFFFFFFFF:08X}",
            "rtl_checksum": f"0x{table_checksum(records):08X}",
            "payload": str(args.payload),
            "payload_matches_expected": payload_matches,
        },
        "axis_normalization": axis_metrics(),
        "vector_count": len(metric_rows),
        "vector_csv": str(args.out_dir / "rplu_metric_vectors.csv"),
    }
    with (args.out_dir / "rplu_metric_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"RPLU material: {args.material} id={args.material_id}")
    print(
        "table: "
        f"{summary['table']['entries']} entries "
        f"r={summary['table']['r_min_q16']}..{summary['table']['r_max_q16']} "
        f"v={summary['table']['v_min_q16']}..{summary['table']['v_max_q16']} "
        f"dissoc_count={summary['table']['dissoc_count']}"
    )
    print(
        "flash: "
        f"{summary['flash']['records']} records "
        f"{summary['flash']['bytes']} bytes "
        f"crc32={summary['flash']['crc32']} "
        f"rtl_checksum={summary['flash']['rtl_checksum']} "
        f"payload_match={summary['flash']['payload_matches_expected']}"
    )
    print(f"vectors: {len(metric_rows)} rows -> {summary['vector_csv']}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RPLU metric reference PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
