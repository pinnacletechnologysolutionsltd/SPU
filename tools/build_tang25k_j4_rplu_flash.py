#!/usr/bin/env python3
"""Build a Tang Primer 25K J4 SPI flash image with SPU-13/RPLU boot assets."""

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
FLASH_MAP = ROOT / "hardware" / "rtl" / "arch" / "spu_flash_map.vh"

FLASH_SIZE = 16 * 1024 * 1024

OPCODE_RPLU_CFG = 0xA5


def read_verilog_define(name):
    pattern = re.compile(rf"`define\s+{re.escape(name)}\s+24'h([0-9A-Fa-f]+)\b")
    for line in FLASH_MAP.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match:
            return int(match.group(1), 16)
    raise SystemExit(f"Missing `{name} in {FLASH_MAP}")


FLASH_PELL_BASE = read_verilog_define("FLASH_PELL_BASE")
FLASH_GOLDEN_BASE = read_verilog_define("FLASH_GOLDEN_BASE")
FLASH_RPLU_CFG_BASE = read_verilog_define("FLASH_RPLU_CFG_BASE")


def read_hex_words(path):
    words = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].split("//", 1)[0].strip()
            if line:
                words.append(int(line, 16))
    return words


def build_header(sel, material, addr):
    header = (OPCODE_RPLU_CFG & 0xFF) << 56
    header |= (sel & 0xFF) << 48
    header |= (material & 0xF) << 44
    header |= (addr & 0x3FF) << 34
    return header


def add_chord(records, sel, material, addr, data):
    records.append((build_header(sel, material, addr), data & ((1 << 64) - 1)))


def build_rplu_records(material=0):
    arch = ROOT / "hardware" / "rtl" / "arch"
    params = read_hex_words(arch / "params_elements.hex")
    vnorm = read_hex_words(arch / "vnorm_carbon.mem")
    dissoc = read_hex_words(arch / "vnorm_dissoc_carbon.mem")

    if len(params) < 3:
        raise SystemExit("params_elements.hex has fewer than 3 entries")
    if len(vnorm) != 1024:
        raise SystemExit(f"vnorm_carbon.mem has {len(vnorm)} entries, expected 1024")
    if len(dissoc) != 1024:
        raise SystemExit(f"vnorm_dissoc_carbon.mem has {len(dissoc)} entries, expected 1024")

    records = []
    for idx in range(3):
        add_chord(records, 0, material, idx, params[(material * 3) + idx])
    for addr, value in enumerate(vnorm):
        add_chord(records, 5, material, addr, value)
    for addr, value in enumerate(dissoc):
        add_chord(records, 6, material, addr, value & 1)
    return records


def write_rplu_payload(records, path):
    with path.open("wb") as f:
        for header, data in records:
            f.write(header.to_bytes(8, "big"))
            f.write(data.to_bytes(8, "big"))


def place_blob(image, offset, path):
    data = path.read_bytes()
    end = offset + len(data)
    if end > len(image):
        raise SystemExit(f"{path} does not fit at 0x{offset:06x}")
    image[offset:end] = data
    return len(data)


def read_base_image(path):
    if path is None:
        return bytearray([0xFF]) * FLASH_SIZE

    data = path.read_bytes()
    if len(data) != FLASH_SIZE:
        raise SystemExit(f"{path} is {len(data)} bytes, expected {FLASH_SIZE}")
    return bytearray(data)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-image",
        type=Path,
        help="optional 16MiB image to preserve outside the SPU/RPLU regions",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BUILD / "tang25k_j4_rplu_flash.bin",
        help="output flash image path",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)

    records = build_rplu_records(material=0)
    rplu_payload = BUILD / "rplu_boot_chords.bin"
    write_rplu_payload(records, rplu_payload)

    image = read_base_image(args.base_image)
    pell_len = place_blob(image, FLASH_PELL_BASE, ROOT / "software" / "flash" / "pell_13.bin")
    golden_len = place_blob(image, FLASH_GOLDEN_BASE, ROOT / "software" / "flash" / "golden_prime_lut.bin")
    rplu_len = place_blob(image, FLASH_RPLU_CFG_BASE, rplu_payload)

    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(image)

    print(f"Wrote {rplu_payload} ({len(records)} records, {rplu_len} bytes)")
    if args.base_image:
        print(f"Preserved base image {args.base_image}")
    else:
        print("Warning: no base image supplied; bytes outside SPU/RPLU regions are 0xFF")
    print(f"Wrote {out} ({len(image)} bytes)")
    print(f"  Pell:   0x{FLASH_PELL_BASE:06x} + {pell_len} bytes")
    print(f"  Golden: 0x{FLASH_GOLDEN_BASE:06x} + {golden_len} bytes")
    print(f"  RPLU:   0x{FLASH_RPLU_CFG_BASE:06x} + {rplu_len} bytes")


if __name__ == "__main__":
    main()
