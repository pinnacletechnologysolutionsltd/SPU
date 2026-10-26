#!/usr/bin/env python3
"""Identify a board's UART baud rate — and thereby its oscillator frequency.

Several board tops derive their UART baud by dividing the raw board clock by a
fixed constant (`BAUD_DIV = 434` in spu_a7_uart_probe_top.v and spu_a7_top.v's
diagnostic UART). That constant yields 115200 baud only if the board clock is
50 MHz; a 100 MHz clock puts the same line at 230400. The baud at which the
output is legible is therefore a direct measurement of the oscillator, needing
no scope, counter, or logic analyzer.

Used on 2026-07-31 to settle the Wukong Artix-7 100T oscillator at 50 MHz,
which fixes the divided core-spin `clk_fast` at 781.25 kHz and the southbridge
SPI ceiling at 130 kHz. See docs/SOUTHBRIDGE_SPI_PROTOCOL.md, "Confirming the
oscillator".

    openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_UARTPROBE.bit
    python3 tools/uart_baud_probe.py

IMPORTANT: this sets the baud and reads on the SAME file descriptor. Using
`stty` and then `cat` does NOT work — the termios setting is reset when cat
opens the port, so every rate returns byte-identical data and the test reports
the same wrong answer at every baud.
"""
import argparse
import os
import termios
import time

DEFAULT_PORT = "/dev/ttyUSB0"

# Candidate rates. 115200 and 230400 are the two that discriminate a 50 MHz
# board clock from a 100 MHz one; the others catch a mis-set divider.
RATES = [
    ("57600", termios.B57600),
    ("115200", termios.B115200),
    ("230400", termios.B230400),
    ("460800", termios.B460800),
]


def configure(fd, speed):
    """Raw 8N1 at `speed`. Mirrors probe_tang25k_rplu_flash.py's configure_tty."""
    a = termios.tcgetattr(fd)
    a[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
              termios.ISTRIP | termios.INLCR | termios.IGNCR |
              termios.ICRNL | termios.IXON | termios.IXOFF)
    a[1] &= ~termios.OPOST
    a[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    a[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
    if hasattr(termios, "CRTSCTS"):
        a[2] &= ~termios.CRTSCTS
    a[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
              termios.ISIG | termios.IEXTEN)
    a[4] = speed
    a[5] = speed
    a[6][termios.VMIN] = 0
    a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)


def capture(port, speed, seconds, limit=4096):
    fd = os.open(port, os.O_RDONLY | os.O_NONBLOCK)
    try:
        configure(fd, speed)
        time.sleep(0.2)                       # let the line settle
        termios.tcflush(fd, termios.TCIOFLUSH)  # drop bytes clocked at the old rate
        buf = b""
        end = time.time() + seconds
        while time.time() < end and len(buf) < limit:
            try:
                chunk = os.read(fd, 256)
                if chunk:
                    buf += chunk
            except BlockingIOError:
                time.sleep(0.01)
        return buf
    finally:
        os.close(fd)


def printable_ratio(data):
    if not data:
        return 0.0
    ok = sum(1 for c in data if 32 <= c < 127 or c in (10, 13))
    return ok / len(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", default=DEFAULT_PORT)
    ap.add_argument("--seconds", type=float, default=3.0,
                    help="capture window per rate (default 3.0)")
    ns = ap.parse_args()

    if not os.path.exists(ns.port):
        raise SystemExit(f"No such port: {ns.port}")

    results = []
    for name, speed in RATES:
        data = capture(ns.port, speed, ns.seconds)
        ratio = printable_ratio(data)
        results.append((name, data, ratio))
        print(f"=== {name} baud: {len(data)} bytes, {ratio*100:.1f}% printable ===")
        if data:
            print("  hex : " + data[:32].hex(" "))
            print("  text: " + "".join(chr(c) if 32 <= c < 127 else "."
                                       for c in data[:96]))
        print()

    # A clean rate is near-fully printable with a meaningful sample. Garbage
    # from a wrong baud typically lands well under half printable.
    clean = [(n, d, r) for n, d, r in results if r >= 0.95 and len(d) >= 8]
    if len(clean) == 1:
        name = clean[0][0]
        print(f"Legible at {name} baud.")
        if name == "115200":
            print("  -> board clock is 50 MHz (BAUD_DIV=434 => 50e6/434 = 115207)")
        elif name == "230400":
            print("  -> board clock is 100 MHz (BAUD_DIV=434 => 100e6/434 = 230415)")
    elif not clean:
        print("No rate produced legible output.")
        print("  Is a bitstream loaded? SRAM is volatile — a power cycle wipes it.")
        print("  Check with: openFPGALoader -c dirtyJtag --detect")
    else:
        # Should not happen with a fixed-divider UART; report rather than guess.
        print("Ambiguous: multiple rates look legible — " +
              ", ".join(n for n, _, _ in clean))


if __name__ == "__main__":
    main()
