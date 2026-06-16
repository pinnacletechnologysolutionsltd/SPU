#!/usr/bin/env python3
"""RPLU loader: produce Artery chords for runtime table writes.

Usage examples:
  # write a 64-bit coefficient (two-chord protocol)
  python3 tools/rplu_loader.py --sel 1 --material 0 --addr 5 --data 0x1122334455667788

The script prints two 64-bit hex chords (HEADER then DATA) to stdout, one per line.
The HEADER format (64-bit):
  [63:56] OPCODE = 0xA5
  [55:48] sel    = 8-bit selector (low 3 bits used)
  [47:44] material = 4-bit material ID
  [43:34] addr     = 10-bit address
  [33:0]  reserved

The DATA chord is the full 64-bit payload representing cfg_wr_data.

In real firmware, write the HEADER and then the DATA word into the Ghost OS "wr_data" channel
(that is, send the two 64-bit words to the SPU via the Artery FIFO / wr_en+wr_data interface).

"""
import argparse

OPCODE = 0xA5

parser = argparse.ArgumentParser(description='Generate RPLU Artery chords')
parser.add_argument('--sel', type=int, required=False, help='cfg selector (0=params,1=pade_num_q32,2=pade_den_q32,3=pade_num_q16,4=pade_den_q16,5=vnorm,6=vnorm_dissoc,7=poly_step)')
parser.add_argument('--poly-step', action='store_true', help='Emit POLY_STEP chord (sel=7).')
parser.add_argument('--material', type=int, default=0, choices=range(16), metavar='0..15', help='material id')
parser.add_argument('--addr', type=lambda x: int(x, 0), required=True, help='address/index for the write')
parser.add_argument('--data', type=lambda x: int(x,0), required=False, help='64-bit data payload (hex or dec)')
args = parser.parse_args()

if args.poly_step:
    args.sel = 7
    if args.data is None:
        args.data = 0

if args.sel is None:
    raise SystemExit('sel must be provided (or use --poly-step)')
if args.sel < 0 or args.sel > 7:
    raise SystemExit('sel must be 0..7')
if args.addr < 0 or args.addr > 1023:
    raise SystemExit('addr must be 0..1023')
if args.data < 0 or args.data > (1<<64)-1:
    raise SystemExit('data out of 64-bit range')

# build header
header = (OPCODE & 0xff) << 56
header |= (args.sel & 0xff) << 48
header |= (args.material & 0xf) << 44
header |= (args.addr & 0x3ff) << 34

print('0x{:016x}'.format(header))
print('0x{:016x}'.format(args.data))
