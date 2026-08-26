#!/usr/bin/env python3
"""read_gpu_framebuffer.py -- host-side reader for
spu13_tang25k_gpu_framebuffer_readout_probe.v's digital framebuffer
readout: syncs on the "SPU1" marker, reads one 640x480 R4G4B4 frame
(2 bytes/pixel), writes it as a PPM image, and independently checks
every pixel against the same oracle (software/lib/gpu_depth_v2_oracle.py
+ the probe's fixed test-triangle fixture) for a bit-exact match --
the actual proof, not just "a picture came out."

Always dumps the raw byte stream to build/gpu_framebuffer_readout_raw.bin,
and on any mismatch, tests whether a small byte-offset shift of the whole
stream collapses the mismatch count -- distinguishes a UART framing/
dropped-byte bug (host-side) from a real RTL/silicon content bug, since
the two look identical as a live pixel-by-pixel diff but very different
under a shift test (see 2026-08-25's "(50,50) and after" investigation).

Uses raw termios via a plain file descriptor (matching this repo's own
convention, e.g. tools/probe_tang25k_rplu_flash.py), not pyserial.

Usage:
  python3 tools/read_gpu_framebuffer.py /dev/ttyUSB1 [output.ppm]
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software" / "lib"))
from gpu_depth_v2_oracle import triangle_edges  # noqa: E402

WIDTH, HEIGHT = 640, 480
MARKER = b"SPU1"

V0_0, V1_0, V2_0 = (50, 50), (400, 60), (200, 300)
TRI_R0, TRI_G0, TRI_B0 = 15, 0, 0
V0_1, V1_1, V2_1 = (150, 100), (450, 150), (300, 400)
TRI_R1, TRI_G1, TRI_B1 = 0, 15, 0


def configure_serial(path: str) -> None:
    subprocess.run(["stty", "-F", path, "115200", "raw", "-echo"], check=True)


def read_exact(fd: int, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = os.read(fd, n - len(buf))
        if not chunk:
            raise EOFError(f"device closed after {len(buf)}/{n} bytes")
        buf += chunk
    return bytes(buf)


def sync_on_marker(fd: int) -> None:
    window = bytearray()
    while True:
        b = os.read(fd, 1)
        if not b:
            raise EOFError("device closed while syncing on marker")
        window += b
        if len(window) > len(MARKER):
            window = window[-len(MARKER):]
        if bytes(window) == MARKER:
            return


def expected_rgb444():
    e0 = triangle_edges(V0_0, V1_0, V2_0)[:3]
    e1 = triangle_edges(V0_1, V1_1, V2_1)[:3]

    def inside(edges, x, y):
        def f(e):
            a, b, c = e
            return a * x + b * y + c
        vals = [f(e) for e in edges]
        return all(v >= 0 for v in vals) or all(v <= 0 for v in vals)

    grid = {}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            c0 = inside(e0, x, y)
            c1 = inside(e1, x, y)
            if c0 and c1:
                grid[(x, y)] = (TRI_R1, TRI_G1, TRI_B1)
            elif c0:
                grid[(x, y)] = (TRI_R0, TRI_G0, TRI_B0)
            elif c1:
                grid[(x, y)] = (TRI_R1, TRI_G1, TRI_B1)
            else:
                grid[(x, y)] = (0, 0, 0)
    return grid


def main() -> int:
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <serial-device> [output.ppm]", file=sys.stderr)
        return 2
    dev_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "gpu_framebuffer_readout.ppm"

    configure_serial(dev_path)
    fd = os.open(dev_path, os.O_RDONLY)
    try:
        print(f"Syncing on {MARKER!r} marker...")
        sync_on_marker(fd)
        print("Synced. Reading frame (this is real UART at 115200 baud -- "
              "expect roughly a minute)...")
        raw = read_exact(fd, WIDTH * HEIGHT * 2)
    finally:
        os.close(fd)

    raw_dump_path = REPO / "build" / "gpu_framebuffer_readout_raw.bin"
    raw_dump_path.parent.mkdir(exist_ok=True)
    raw_dump_path.write_bytes(raw)
    print(f"Wrote raw byte stream to {raw_dump_path} for offline inspection.")

    expected = expected_rgb444()

    def count_mismatches(shift: int) -> int:
        # shift>0 drops `shift` leading bytes (as if the host missed them);
        # shift<0 prepends |shift| zero bytes (as if it saw extra bytes
        # before real data started). Byte-granularity, not pixel-granularity,
        # since a dropped/extra byte on a real UART link shifts the
        # R4|G4B4 grouping itself, not just which pixel a pair belongs to.
        shifted = raw[shift:] if shift >= 0 else (b"\x00" * (-shift) + raw)
        n = 0
        idx = 0
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if idx + 1 >= len(shifted):
                    return n
                b0, b1 = shifted[idx], shifted[idx + 1]
                idx += 2
                px = (b0 & 0xF, (b1 >> 4) & 0xF, b1 & 0xF)
                if px != expected[(x, y)]:
                    n += 1
        return n

    baseline = count_mismatches(0)
    if baseline > 0:
        print("Testing whether this is a byte-framing shift, not a real "
              "content mismatch (candidate offsets -4..+4 bytes):")
        best_shift, best_n = 0, baseline
        for s in range(-4, 5):
            if s == 0:
                continue
            n = count_mismatches(s)
            print(f"  shift {s:+d}: {n} mismatches")
            if n < best_n:
                best_shift, best_n = s, n
        if best_n < baseline // 2:
            print(f"  -> shift {best_shift:+d} cuts mismatches from "
                  f"{baseline} to {best_n}: this looks like a UART framing/"
                  f"byte-drop bug, not an RTL content bug.")
        else:
            print(f"  -> no shift meaningfully reduces the {baseline} "
                  f"mismatches: not a simple framing shift.")

    mismatches = 0
    rgb8 = bytearray(WIDTH * HEIGHT * 3)
    idx = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            b0 = raw[idx]
            b1 = raw[idx + 1]
            idx += 2
            r4 = b0 & 0xF
            g4 = (b1 >> 4) & 0xF
            b4 = b1 & 0xF
            exp_r, exp_g, exp_b = expected[(x, y)]
            if (r4, g4, b4) != (exp_r, exp_g, exp_b):
                mismatches += 1
                if mismatches <= 10:
                    print(f"  MISMATCH ({x},{y}): expected "
                          f"{(exp_r, exp_g, exp_b)} got {(r4, g4, b4)}")
            p = (y * WIDTH + x) * 3
            rgb8[p] = r4 * 17
            rgb8[p + 1] = g4 * 17
            rgb8[p + 2] = b4 * 17

    with open(out_path, "wb") as f:
        f.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        f.write(bytes(rgb8))

    total = WIDTH * HEIGHT
    print(f"Wrote {out_path} ({WIDTH}x{HEIGHT})")
    print(f"{total} pixels checked, {mismatches} mismatches")
    if mismatches:
        print("FAIL: framebuffer does not match the oracle bit-exactly")
        return 1
    print("PASS: framebuffer is a bit-exact match to the independent oracle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
