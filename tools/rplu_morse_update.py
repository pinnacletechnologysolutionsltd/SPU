#!/usr/bin/env python3
"""
rplu_morse_update.py — Runtime Morse table update via RPLU config interface.

Streams updated Morse potential values (from simulation, SD card, or
recalculated parameters) into the RPLU material ROMs at runtime using
the Artery chord protocol.

Modes:
  --from-csv CSV      Load updated V(r) values from a CSV (same format as
                      material_morse_vectors.csv)
  --from-sim VALUE    Apply a uniform De scaling factor (e.g. 1.05 = +5%
                      bond strength to simulate alloy hardening)
  --from-scratch      Regenerate Morse from empirical parameters with new
                      a, re, De values (bond length, stiffness, energy)
  --update-all        Write all 1024 entries for the selected material
  --update-range A B  Write entries A through B (inclusive)

Output formats:
  --uart              Print Artery chords (default, for UART upload)
  --flash BIN         Write updated flash sector image
  --sd-card DIR       Write batch file for SD card streaming

Usage:
  # Simulate 5% stronger carbon bonds:
  python3 tools/rplu_morse_update.py --from-sim 1.05 --material carbon --update-all --uart

  # Load alloy-specific table from simulation CSV:
  python3 tools/rplu_morse_update.py --from-csv my_alloy.csv --material iron --update-all --uart

  # Generate flash image with custom parameters:
  python3 tools/rplu_morse_update.py --from-scratch --a 1.8 --re 1.42 --De 400 \\
      --material carbon --update-all --flash build/custom_carbon.bin

  # Update just the dissociation flag range (e.g., after re-measurement):
  python3 tools/rplu_morse_update.py --from-csv recalibrated.csv --material iron \\
      --update-range 500 600 --uart
"""

import argparse
import csv
import struct
import sys
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 80
SQRT3 = Decimal(3).sqrt()
SCALE32 = Decimal(2147483647)
AVOGADRO = Decimal("6.02214076e23")

# Default empirical parameters (8 engineering elements)
DEFAULT_PARAMS = {
    "carbon":   {"De_kJ_per_mol": Decimal("348"), "a": Decimal("1.5"), "re": Decimal("1.54")},
    "iron":     {"De_kJ_per_mol": Decimal("413"), "a": Decimal("1.2"), "re": Decimal("2.48")},
    "aluminum": {"De_kJ_per_mol": Decimal("186"), "a": Decimal("1.3"), "re": Decimal("2.86")},
    "silicon":  {"De_kJ_per_mol": Decimal("222"), "a": Decimal("1.4"), "re": Decimal("2.35")},
    "titanium": {"De_kJ_per_mol": Decimal("284"), "a": Decimal("1.2"), "re": Decimal("2.93")},
    "nickel":   {"De_kJ_per_mol": Decimal("203"), "a": Decimal("1.4"), "re": Decimal("2.49")},
    "copper":   {"De_kJ_per_mol": Decimal("202"), "a": Decimal("1.3"), "re": Decimal("2.56")},
    "tungsten": {"De_kJ_per_mol": Decimal("480"), "a": Decimal("1.4"), "re": Decimal("2.74")},
}

MATERIAL_ORDER = list(DEFAULT_PARAMS.keys())
MATERIAL_IDS = {n: i for i, n in enumerate(MATERIAL_ORDER)}
ATOMIC_NUMBERS = {
    "carbon": 6,
    "iron": 26,
    "aluminum": 13,
    "silicon": 14,
    "titanium": 22,
    "nickel": 28,
    "copper": 29,
    "tungsten": 74,
}

OPCODE = 0xA5
SEL_ROM = 0  # cfg_wr_sel for V(r) ROM
SEL_DISSOC = 1  # cfg_wr_sel for dissociation bits
FLASH_MAGIC = 0x4D525345  # "MRSE"


def morse_potential(r: Decimal, De: Decimal, a: Decimal, re: Decimal) -> Decimal:
    """V(r) = De * (1 - exp(-a*(r-re)))^2"""
    x = -(a * (r - re))
    ex = x.exp()
    return De * (Decimal(1) - ex) ** 2


def to_surd_pq(value: Decimal) -> tuple[int, int]:
    """Convert float to Q(√3) integer pair with Q31 scaling."""
    v = Decimal(value)
    qf = v / SQRT3
    q_int = int((qf * SCALE32).to_integral_value(rounding="ROUND_HALF_EVEN"))
    q = Decimal(q_int) / SCALE32
    p = v - q * SQRT3
    p_int = int((p * SCALE32).to_integral_value(rounding="ROUND_HALF_EVEN"))

    def clamp32(x):
        return max(-(2**31), min(2**31 - 1, x))

    return clamp32(p_int), clamp32(q_int)


def pack_header(sel: int, material: int, addr: int) -> int:
    """Pack Artery chord header."""
    h = (OPCODE & 0xFF) << 56
    h |= (sel & 0xFF) << 48
    h |= (material & 0xF) << 44
    h |= (addr & 0x3FF) << 34
    return h


def emit_uart_chords(material: int, entries: list[tuple[int, int, int]]):
    """Print Artery chords for UART upload."""
    for addr, p_int, q_int in entries:
        data = ((p_int & 0xFFFFFFFF) << 32) | (q_int & 0xFFFFFFFF)
        header = pack_header(SEL_ROM, material, addr)
        print(f"0x{header:016X} 0x{data:016X}")


def emit_dissoc_chords(material: int, entries: list[tuple[int, int]]):
    """Print Artery chords for dissociation bit updates."""
    for addr, dissoc in entries:
        header = pack_header(SEL_DISSOC, material, addr)
        data = 1 if dissoc else 0
        print(f"0x{header:016X} 0x{data:016X}")


def load_default_material_tables() -> dict[str, list[tuple[float, float, int, int, int]]]:
    """Load baseline tables from material_morse_vectors.csv when present."""
    csv_path = (
        Path(__file__).resolve().parent.parent
        / "hardware/rtl/arch/material_morse_vectors.csv"
    )
    tables: dict[str, list[tuple[float, float, int, int, int]]] = {
        name: [] for name in MATERIAL_ORDER
    }
    if csv_path.exists():
        with open(csv_path) as f:
            for row in csv.DictReader(f):
                name = row["material"]
                if name in tables:
                    tables[name].append(
                        (
                            float(row["r"]),
                            float(row["V"]),
                            int(row["p_int"]),
                            int(row["q_int"]),
                            int(row["dissoc"]),
                        )
                    )

    for name in MATERIAL_ORDER:
        if len(tables[name]) != 1024:
            params = DEFAULT_PARAMS[name]
            tables[name] = generate_from_params(
                name,
                params["a"],
                params["re"],
                params["De_kJ_per_mol"],
            )
    return tables


def emit_flash_image(
    path: str,
    material_name: str,
    entries: list[tuple[float, float, int, int, int]],
):
    """Write a complete multi-material MRSE flash image with one table updated."""
    entries_per = 1024
    if len(entries) != entries_per:
        raise ValueError("--flash requires --update-all so each table has 1024 entries")

    tables = load_default_material_tables()
    tables[material_name] = entries

    sector_size = 65536
    header_size = 16
    dir_entry_size = 16
    dir_size = len(MATERIAL_ORDER) * dir_entry_size
    v_table_start = header_size + dir_size
    v_bytes_per_element = entries_per * 8
    v_table_size = len(MATERIAL_ORDER) * v_bytes_per_element
    dissoc_start = v_table_start + v_table_size
    dissoc_bytes_per_element = (entries_per + 7) // 8
    total_size = dissoc_start + len(MATERIAL_ORDER) * dissoc_bytes_per_element
    padded_size = ((total_size + sector_size - 1) // sector_size) * sector_size
    image = bytearray(padded_size)

    struct.pack_into(
        ">IHHHH",
        image,
        0,
        FLASH_MAGIC,
        len(MATERIAL_ORDER),
        0,
        entries_per,
        8,
    )

    for i, name in enumerate(MATERIAL_ORDER):
        dir_pos = header_size + i * dir_entry_size
        name_bytes = name.encode("ascii")[:8].ljust(8, b"\0")
        v_offset = v_table_start + i * v_bytes_per_element
        d_offset = dissoc_start + i * dissoc_bytes_per_element
        struct.pack_into(
            ">8sHHII",
            image,
            dir_pos,
            name_bytes,
            ATOMIC_NUMBERS[name],
            entries_per,
            v_offset,
            d_offset,
        )

        for j, (_r, _v, p_int, q_int, dissoc) in enumerate(tables[name]):
            struct.pack_into(
                ">II",
                image,
                v_offset + j * 8,
                p_int & 0xFFFFFFFF,
                q_int & 0xFFFFFFFF,
            )
            if dissoc:
                byte_idx = j // 8
                bit_idx = 7 - (j % 8)
                image[d_offset + byte_idx] |= 1 << bit_idx

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(image)
    print(f"Wrote MRSE flash image: {path} ({len(image)} bytes)")


def load_from_csv(csv_path: str, material: str) -> list:
    """Load entries from CSV matching material name."""
    entries = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            if row["material"] == material:
                entries.append(
                    (
                        float(row["r"]),
                        float(row["V"]),
                        int(row["p_int"]),
                        int(row["q_int"]),
                        int(row["dissoc"]),
                    )
                )
    return entries


def generate_from_params(
    material: str, a: Decimal, re: Decimal, De_kj: Decimal
) -> list:
    """Generate Morse table from empirical parameters."""
    De_j = (De_kj * Decimal("1000")) / AVOGADRO
    entries = []
    r_min = float(re) * 0.5
    r_max = float(re) * 1.5
    for i in range(1024):
        rf = Decimal(str(r_min + (r_max - r_min) * i / 1023))
        V = morse_potential(rf, De_j, a, re)
        p_int, q_int = to_surd_pq(V)
        dissoc = 1 if V > De_j else 0
        entries.append((float(rf), float(V), p_int, q_int, dissoc))
    return entries


def scale_from_csv(csv_path: str, material: str, scale: float) -> list:
    """Load CSV entries and scale V(r) by a factor (simulate bond strength change)."""
    entries = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            if row["material"] == material:
                V = float(row["V"]) * scale
                p_int, q_int = to_surd_pq(Decimal(str(V)))
                dissoc = int(row["dissoc"])
                entries.append(
                    (float(row["r"]), V, p_int, q_int, dissoc)
                )
    return entries


def main():
    parser = argparse.ArgumentParser(description="Runtime Morse table update via RPLU")
    parser.add_argument("--material", default="carbon",
                        choices=MATERIAL_ORDER)
    parser.add_argument(
        "--from-csv", type=str, help="Load updated V(r) values from CSV"
    )
    parser.add_argument(
        "--from-sim",
        type=float,
        help="Scale existing V(r) by factor (e.g. 1.05 = 5%% stronger)",
    )
    parser.add_argument("--from-scratch", action="store_true",
                        help="Regenerate from parameters")
    parser.add_argument("--a", type=float, help="Morse a parameter (angstrom^-1)")
    parser.add_argument("--re", type=float, help="Equilibrium bond length (angstrom)")
    parser.add_argument("--De", type=float, help="Dissociation energy (kJ/mol)")
    parser.add_argument(
        "--update-all", action="store_true", help="Update all 1024 entries"
    )
    parser.add_argument(
        "--update-range", type=int, nargs=2, metavar=("START", "END"),
        help="Update entries in range [START, END]"
    )
    parser.add_argument("--uart", action="store_true", help="Output Artery UART chords")
    parser.add_argument("--flash", type=str, help="Write updated flash sector to PATH")
    parser.add_argument("--sd-card", type=str, help="Write batch file for SD card")
    args = parser.parse_args()

    if not (args.from_csv or args.from_sim or args.from_scratch):
        parser.error("Must specify --from-csv, --from-sim, or --from-scratch")

    material = args.material
    mat_id = MATERIAL_IDS[material]

    # Load or generate entries
    if args.from_scratch:
        params = DEFAULT_PARAMS[material]
        a = Decimal(str(args.a)) if args.a else params["a"]
        re = Decimal(str(args.re)) if args.re else params["re"]
        De_kj = Decimal(str(args.De)) if args.De else params["De_kJ_per_mol"]
        all_entries = generate_from_params(material, a, re, De_kj)
        print(
            f"Generated {len(all_entries)} entries: a={float(a)}, re={float(re)}, De={float(De_kj)} kJ/mol"
        )
    elif args.from_sim:
        csv_path = args.from_csv if isinstance(args.from_csv, str) else str(
            Path(__file__).resolve().parent.parent
            / "hardware/rtl/arch/material_morse_vectors.csv"
        )
        all_entries = scale_from_csv(csv_path, material, args.from_sim)
        print(
            f"Scaled {len(all_entries)} entries by factor {args.from_sim} from {csv_path}"
        )
    else:  # from_csv
        all_entries = load_from_csv(args.from_csv, material)
        print(f"Loaded {len(all_entries)} entries from {args.from_csv}")

    # Select range
    if args.update_all:
        entries = all_entries
    elif args.update_range:
        start, end = args.update_range
        entries = all_entries[start : end + 1]
        print(f"Range: [{start}, {end}] → {len(entries)} entries")
    else:
        parser.error("Must specify --update-all or --update-range")

    # Output
    if args.flash:
        emit_flash_image(args.flash, material, entries)
    elif args.sd_card:
        sd_path = Path(args.sd_card)
        sd_path.mkdir(parents=True, exist_ok=True)
        batch_file = sd_path / f"morse_{material}.batch"
        with open(batch_file, "w") as f:
            # Redirect UART output to file
            import io

            old_stdout = sys.stdout
            sys.stdout = f
            emit_uart_chords(mat_id, [(i, e[2], e[3]) for i, e in enumerate(entries)])
            emit_dissoc_chords(mat_id, [(i, e[4]) for i, e in enumerate(entries)])
            sys.stdout = old_stdout
        print(f"Wrote SD card batch: {batch_file} ({len(entries)} V(r) + dissoc)")
    else:
        # Default: UART chords
        if entries:
            # Build indexed entry list
            idx_entries = []
            dissoc_entries = []
            base_idx = 0 if args.update_all else args.update_range[0]
            for i, e in enumerate(entries):
                idx_entries.append((base_idx + i, e[2], e[3]))
                dissoc_entries.append((base_idx + i, e[4]))

            emit_uart_chords(mat_id, idx_entries)
            emit_dissoc_chords(mat_id, dissoc_entries)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
