#!/usr/bin/env python3
"""RPLU UART uploader — send HEADER+DATA chords to RP2350 over USB CDC (stdio).

Usage:
  python3 tools/rplu_uart_uploader.py --port /dev/ttyACM0 --sel 1 --material 0 --addr 5 --data 0x1122334455667788

Notes:
- The RP2350 firmware must be running on the target Pico and the board connected via USB
  (RP2350 USB CDC device, e.g., /dev/ttyACM0 or COM3). The firmware forwards raw 8-byte
  packets received on USB stdio into the FPGA as Chords.
- This tool sends two 8-byte big-endian words: HEADER then DATA. HEADER layout (64-bit):
    [63:56] OPCODE = 0xA5
    [55:48] sel (8-bit; low 3 bits used)
    [47]    material (0/1)
    [46:37] addr (10-bit)
    [36:0]  reserved

Requires: pyserial (pip install pyserial)
"""

import argparse
import time
import sys

try:
    import serial
except Exception:
    print("pyserial is required: pip3 install pyserial")
    sys.exit(1)

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


def main():
    parser = argparse.ArgumentParser(description='Send one RPLU HEADER+DATA chord pair over USB to RP2350')
    parser.add_argument('--port', required=True, help='Serial device for RP2350 USB CDC (e.g. /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud for opening USB CDC (ignored for native USB but required by pyserial)')
    parser.add_argument('--sel', type=int, required=True, help='cfg selector (0=params,1=pade_num_q32,2=pade_den_q32,3=pade_num_q16,4=pade_den_q16,5=vnorm,6=vnorm_dissoc)')
    parser.add_argument('--material', type=int, default=0, choices=[0,1], help='material id (0 carbon, 1 iron)')
    parser.add_argument('--addr', type=int, required=True, help='address/index for the write (0..1023)')
    parser.add_argument('--data', type=lambda x: int(x,0), required=True, help='64-bit data payload (hex or dec)')
    parser.add_argument('--wait', type=float, default=0.01, help='seconds to wait between header and data (default 10 ms)')

    args = parser.parse_args()

    if args.data < 0 or args.data > (1<<64)-1:
        raise SystemExit('data out of 64-bit range')

    header = build_header(args.sel, args.material, args.addr)
    header_bytes = to_u64_be(header)
    data_bytes = to_u64_be(args.data)

    print(f"Opening serial port {args.port} @ {args.baud}...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        sys.exit(2)

    # Send header then data as raw bytes (big-endian)
    print(f"Sending HEADER: 0x{header:016x}")
    ser.write(header_bytes)
    ser.flush()
    time.sleep(args.wait)
    print(f"Sending DATA:   0x{args.data:016x}")
    ser.write(data_bytes)
    ser.flush()

    print('Done.')
    ser.close()


if __name__ == '__main__':
    main()
