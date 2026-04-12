#!/usr/bin/env python3
"""RPLU minipro uploader

Generates a binary file containing one or more HEADER+DATA chord pairs (8+8 bytes, big-endian)
and optionally invokes `minipro` to flash the resulting file to an SPI flash chip.

Usage examples:
  # Single chord pair, write to rplu_chords.bin (no flashing):
  python3 tools/rplu_minipro_uploader.py --sel 1 --material 0 --addr 5 --data 0x1122334455667788

  # Batch file (two-line pairs as produced by tools/rplu_loader.py):
  python3 tools/rplu_minipro_uploader.py --batch-file my_chords.txt --outfile my_chords.bin

  # Build binary and run minipro (requires you to know the chip name):
  python3 tools/rplu_minipro_uploader.py --sel 1 --material 0 --addr 5 --data 0x... --flash --chip W25Q128 --yes

  # Or provide a full minipro command template (must contain {binfile}):
  python3 tools/rplu_minipro_uploader.py --batch-file my_chords.txt --flash --minipro-cmd "minipro -p W25Q128 -w {binfile}"

Notes:
 - The binary format is a simple concatenation of 8-byte big-endian HEADER then 8-byte big-endian DATA for each record.
 - HEADER format (64-bit):
     [63:56] OPCODE = 0xA5
     [55:48] sel (8-bit; low 3 bits used)
     [47]    material (0/1)
     [46:37] addr (10-bit)
     [36:0]  reserved

"""

import argparse
import sys
import os
import shlex
import subprocess

OPCODE = 0xA5


def to_u64_be(v):
    return int(v).to_bytes(8, 'big')


def build_header(sel, material, addr):
    if sel < 0 or sel > 0xFF:
        raise ValueError('sel out of range')
    if material not in (0, 1):
        raise ValueError('material must be 0 or 1')
    if addr < 0 or addr > 0x3FF:
        raise ValueError('addr out of range')
    header = (OPCODE & 0xFF) << 56
    header |= (sel & 0xFF) << 48
    header |= (material & 0x1) << 47
    header |= (addr & 0x3FF) << 37
    return header


def parse_int_like(s):
    s = s.strip()
    if s.lower().startswith('0x'):
        return int(s, 16)
    return int(s, 0)


def read_batch_file(path):
    lines = [l.strip() for l in open(path, 'r', encoding='utf-8').read().splitlines() if l.strip() and not l.strip().startswith('#')]
    if not lines:
        raise SystemExit('empty batch file')
    entries = []
    # If file looks like pairs of single-token hex lines (rplu_loader output), parse pairs
    single_token_lines = all(len(l.split()) == 1 for l in lines)
    if single_token_lines and len(lines) % 2 == 0:
        for i in range(0, len(lines), 2):
            h = parse_int_like(lines[i])
            d = parse_int_like(lines[i+1])
            entries.append((h, d))
        return entries

    # Otherwise accept lines with two tokens (header data) or four tokens (sel material addr data)
    for l in lines:
        toks = l.split()
        if len(toks) == 2:
            h = parse_int_like(toks[0])
            d = parse_int_like(toks[1])
            entries.append((h, d))
        elif len(toks) == 4:
            sel = int(toks[0], 0)
            material = int(toks[1], 0)
            addr = int(toks[2], 0)
            data = parse_int_like(toks[3])
            h = build_header(sel, material, addr)
            entries.append((h, data))
        else:
            raise SystemExit(f'bad batch line: "{l}" (expected 2 or 4 tokens)')
    return entries


def write_bin(entries, outfile):
    with open(outfile, 'wb') as f:
        for h, d in entries:
            if h < 0 or h > (1 << 64) - 1:
                raise SystemExit('header out of 64-bit range')
            if d < 0 or d > (1 << 64) - 1:
                raise SystemExit('data out of 64-bit range')
            f.write(to_u64_be(h))
            f.write(to_u64_be(d))


def main():
    p = argparse.ArgumentParser(description='Generate RPLU chord binary and optionally flash with minipro')
    p.add_argument('--outfile', default='rplu_chords.bin', help='Output binary file')

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--batch-file', help='Text file with chords (see README)')
    group.add_argument('--sel', type=int, help='selector for single write (0..255)')

    # single-write fields
    p.add_argument('--material', type=int, default=0, choices=[0, 1], help='material id (0/1)')
    p.add_argument('--addr', type=int, help='address for single write (0..1023)')
    p.add_argument('--data', type=lambda x: int(x, 0), help='64-bit data payload for single write')

    # flashing options
    p.add_argument('--flash', action='store_true', help='Run minipro to flash the produced binary')
    p.add_argument('--chip', help='minipro chip name (e.g., W25Q128) — used if --minipro-cmd is not supplied')
    p.add_argument('--minipro-cmd', help='Full minipro command template, must include {binfile} (e.g., "minipro -p W25Q128 -w {binfile}")')
    p.add_argument('--yes', action='store_true', help='Skip confirmation prompt before running minipro')

    args = p.parse_args()

    entries = []
    if args.batch_file:
        if not os.path.exists(args.batch_file):
            raise SystemExit('batch file not found')
        entries = read_batch_file(args.batch_file)
    else:
        # single write
        if args.sel is None or args.addr is None or args.data is None:
            raise SystemExit('for single write provide --sel, --addr and --data')
        header = build_header(args.sel, args.material, args.addr)
        entries = [(header, args.data)]

    outfile = args.outfile
    write_bin(entries, outfile)
    print(f'Wrote {len(entries)} chord pair(s) to {outfile}')

    if not args.flash:
        print('Not flashing; run minipro manually if desired. Example:')
        print(f'  minipro -p W25Q128 -w {outfile}')
        return

    # flash requested
    if args.minipro_cmd:
        if '{binfile}' not in args.minipro_cmd:
            raise SystemExit('--minipro-cmd must contain the {binfile} placeholder')
        cmd = args.minipro_cmd.format(binfile=outfile)
    elif args.chip:
        cmd = f'minipro -p {shlex.quote(args.chip)} -w {shlex.quote(outfile)}'
    else:
        raise SystemExit('When --flash is given, provide --chip or --minipro-cmd')

    print('About to run:', cmd)
    if not args.yes:
        try:
            input('Press Enter to run minipro, or Ctrl-C to abort...')
        except KeyboardInterrupt:
            print('\nAborted')
            sys.exit(1)

    # execute
    try:
        ret = subprocess.run(shlex.split(cmd), check=False)
        if ret.returncode != 0:
            raise SystemExit(f'minipro failed (exit {ret.returncode})')
    except FileNotFoundError:
        raise SystemExit('minipro not found in PATH — install minipro or provide --minipro-cmd')

    print('Flashing complete')


if __name__ == '__main__':
    main()
