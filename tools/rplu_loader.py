#!/usr/bin/env python3
"""RPLU loader: produce Artery chords for runtime table writes.

Usage examples:
  # write a 64-bit coefficient (two-chord protocol)
  python3 tools/rplu_loader.py --sel 1 --material 0 --addr 5 --data 0x1122334455667788

The script prints two 64-bit hex chords (HEADER then DATA) to stdout, one per line.
The HEADER format (64-bit):
  [63:56] OPCODE = 0xA5
  [55:48] sel    = 8-bit selector (low 3 bits used)
  [47]     material (0 carbon, 1 iron)
  [46:37] addr   = 10-bit address
  [36:0]  reserved

The DATA chord is the full 64-bit payload representing cfg_wr_data.

In real firmware, write the HEADER and then the DATA word into the Ghost OS "wr_data" channel
(that is, send the two 64-bit words to the SPU via the Artery FIFO / wr_en+wr_data interface).

"""
import argparse

OPCODE = 0xA5

parser = argparse.ArgumentParser(description='Generate RPLU Artery chords')
parser.add_argument('--sel', type=int, required=True, help='cfg selector (0=params,1=pade_num_q32,2=pade_den_q32,3=pade_num_q16,4=pade_den_q16,5=vnorm,6=vnorm_dissoc)')
parser.add_argument('--material', type=int, default=0, choices=[0,1], help='material id (0 carbon, 1 iron)')
parser.add_argument('--addr', type=int, required=True, help='address/index for the write')
parser.add_argument('--data', type=lambda x: int(x,0), required=True, help='64-bit data payload (hex or dec)')
args = parser.parse_args()

if args.sel < 0 or args.sel > 7:
    raise SystemExit('sel must be 0..7')
if args.addr < 0 or args.addr > 1023:
    raise SystemExit('addr must be 0..1023')
if args.data < 0 or args.data > (1<<64)-1:
    raise SystemExit('data out of 64-bit range')

# build header
header = (OPCODE & 0xff) << 56
header |= (args.sel & 0xff) << 48
header |= (args.material & 0x1) << 47
header |= (args.addr & 0x3ff) << 37

print('0x{:016x}'.format(header))
print('0x{:016x}'.format(args.data))
