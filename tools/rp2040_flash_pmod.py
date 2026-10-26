#!/usr/bin/env python3
"""Host utility for hardware/rp2040/rp2040_flash_pmod.c."""

from __future__ import annotations

import argparse
import binascii
import glob
import os
import select
import sys
import termios
import time
from pathlib import Path


SECTOR_SIZE = 4096
CHUNK_SIZE = 4096
EXPECTED_JEDEC = "EF4018"


try:
    import serial
except ImportError:  # pragma: no cover - depends on host environment
    serial = None


class FlashPmodError(RuntimeError):
    pass


class PosixSerial:
    """Small Linux serial backend used when pyserial is unavailable."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 10.0, write_timeout: float = 10.0):
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
        attrs[3] = 0
        attrs[4] = termios.B115200
        attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def close(self) -> None:
        os.close(self.fd)

    def reset_input_buffer(self) -> None:
        termios.tcflush(self.fd, termios.TCIFLUSH)

    def flush(self) -> None:
        termios.tcdrain(self.fd)

    def write(self, data: bytes) -> int:
        total = 0
        deadline = time.monotonic() + self.write_timeout
        while total < len(data):
            remaining = max(0.0, deadline - time.monotonic())
            if remaining == 0:
                raise TimeoutError("serial write timeout")
            _, writable, _ = select.select([], [self.fd], [], remaining)
            if not writable:
                raise TimeoutError("serial write timeout")
            total += os.write(self.fd, data[total:])
        return total

    def read(self, size: int) -> bytes:
        out = bytearray()
        deadline = time.monotonic() + self.timeout
        while len(out) < size:
            remaining = max(0.0, deadline - time.monotonic())
            if remaining == 0:
                break
            readable, _, _ = select.select([self.fd], [], [], remaining)
            if not readable:
                break
            out += os.read(self.fd, size - len(out))
        return bytes(out)

    def readline(self) -> bytes:
        out = bytearray()
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            if remaining == 0:
                return bytes(out)
            readable, _, _ = select.select([self.fd], [], [], remaining)
            if not readable:
                return bytes(out)
            b = os.read(self.fd, 1)
            if not b:
                continue
            out += b
            if b == b"\n":
                return bytes(out)


class FlashPmod:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 10.0):
        serial_cls = serial.Serial if serial is not None else PosixSerial
        try:
            self.ser = serial_cls(port, baudrate=baud, timeout=timeout, write_timeout=timeout)
        except FileNotFoundError as exc:
            ports = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
            hint = f"; available serial ports: {', '.join(ports)}" if ports else "; no /dev/ttyACM* or /dev/ttyUSB* ports found"
            raise FlashPmodError(f"serial port {port} not found{hint}") from exc
        time.sleep(0.2)
        self.ser.reset_input_buffer()

    def close(self) -> None:
        self.ser.close()

    def _readline(self) -> str:
        raw = self.ser.readline()
        if not raw:
            raise FlashPmodError("timeout waiting for RP2040 response")
        return raw.decode("ascii", errors="replace").strip()

    def _command(self, line: str, ok_prefix: str = "OK") -> str:
        self.ser.write((line.rstrip() + "\n").encode("ascii"))
        self.ser.flush()
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            resp = self._readline()
            if not resp:
                continue
            if resp.startswith(ok_prefix):
                return resp
            if resp.startswith("ERR"):
                raise FlashPmodError(resp)
            # Ignore startup banner/help lines.
        raise FlashPmodError(f"no {ok_prefix!r} response for command {line!r}")

    def ping(self) -> str:
        return self._command("PING")

    def pins(self) -> str:
        return self._command("PINS")

    def pins_optional(self) -> str | None:
        try:
            return self.pins()
        except FlashPmodError as exc:
            if "UNKNOWN_CMD" in str(exc):
                return None
            raise

    def diag(self) -> str:
        return self._command("DIAG")

    def drive(self, cs: int, sck: int, mosi: int) -> str:
        return self._command(f"DRIVE {cs} {sck} {mosi}")

    def wake(self) -> str:
        return self._command("WAKE")

    def reset_flash(self) -> str:
        return self._command("RESET")

    def wren(self) -> str:
        return self._command("WREN")

    def jedec(self) -> str:
        resp = self._command("JEDEC")
        parts = resp.split()
        if len(parts) != 3 or parts[1] != "JEDEC":
            raise FlashPmodError(f"bad JEDEC response: {resp}")
        return parts[2].upper()

    def rdsr(self) -> int:
        resp = self._command("RDSR")
        return int(resp.split()[-1], 16)

    def read(self, addr: int, length: int) -> bytes:
        if length > CHUNK_SIZE:
            raise ValueError(f"read length must be <= {CHUNK_SIZE}")
        self.ser.write(f"READ {addr} {length}\n".encode("ascii"))
        self.ser.flush()
        while True:
            resp = self._readline()
            if resp.startswith("DATA "):
                got_len = int(resp.split()[1], 0)
                if got_len != length:
                    raise FlashPmodError(f"bad DATA length {got_len}, expected {length}")
                data = self.ser.read(length)
                if len(data) != length:
                    raise FlashPmodError(f"short read payload {len(data)}/{length}")
                tail = self._readline()
                if tail != "OK READ":
                    raise FlashPmodError(f"bad READ tail: {tail}")
                return data
            if resp.startswith("ERR"):
                raise FlashPmodError(resp)

    def erase4k(self, addr: int) -> None:
        if addr & (SECTOR_SIZE - 1):
            raise ValueError("erase4k address must be 4 KiB aligned")
        self._command(f"ERASE4K {addr}")

    def write_chunk(self, addr: int, data: bytes) -> None:
        if not data or len(data) > CHUNK_SIZE:
            raise ValueError(f"write chunk length must be 1..{CHUNK_SIZE}")
        crc = binascii.crc32(data) & 0xFFFFFFFF
        self.ser.write(f"WRITE {addr} {len(data)} 0x{crc:08X}\n".encode("ascii"))
        self.ser.flush()
        while True:
            resp = self._readline()
            if resp == "READY":
                break
            if resp.startswith("ERR"):
                raise FlashPmodError(resp)
        self.ser.write(data)
        self.ser.flush()
        tail = self._readline()
        if tail != "OK WRITE":
            raise FlashPmodError(f"bad WRITE tail: {tail}")


def autodetect_port() -> str:
    ports = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    if not ports:
        raise FlashPmodError("no /dev/ttyACM* or /dev/ttyUSB* ports found")
    return ports[0]


def parse_int(value: str) -> int:
    return int(value, 0)


def iter_dirty_sectors(data: bytes, offset: int, skip_ff: bool = True):
    start_sector = offset // SECTOR_SIZE
    end = offset + len(data)
    end_sector = (end + SECTOR_SIZE - 1) // SECTOR_SIZE
    for sector in range(start_sector, end_sector):
        sector_addr = sector * SECTOR_SIZE
        rel0 = max(0, sector_addr - offset)
        rel1 = min(len(data), sector_addr + SECTOR_SIZE - offset)
        chunk = data[rel0:rel1]
        if not chunk:
            continue
        if skip_ff and all(b == 0xFF for b in chunk):
            continue
        yield sector_addr, rel0, rel1


def require_jedec(dev: FlashPmod, expected: str, attempts: int = 1) -> None:
    expected = expected.upper() if expected else ""
    last = None
    for attempt in range(1, attempts + 1):
        last = dev.jedec()
        print(f"JEDEC[{attempt}/{attempts}]: {last}")
        if not expected or last == expected:
            return
        time.sleep(0.25)
    raise FlashPmodError(f"expected JEDEC {expected}, got {last}")


def hexdump_line(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def first_mismatch(expected: bytes, actual: bytes) -> int | None:
    for i, (exp, got) in enumerate(zip(expected, actual)):
        if exp != got:
            return i
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return None


def cmd_id(args) -> None:
    dev = FlashPmod(args.port or autodetect_port())
    try:
        print(dev.ping())
        pins = dev.pins_optional()
        if pins is not None:
            print(pins)
        require_jedec(dev, args.expected_jedec, attempts=3)
        print(f"RDSR: 0x{dev.rdsr():02X}")
    finally:
        dev.close()


def cmd_diag(args) -> None:
    dev = FlashPmod(args.port or autodetect_port())
    try:
        print(dev.ping())
        try:
            print(dev.pins())
            print(dev.diag())
        except FlashPmodError as exc:
            if "UNKNOWN_CMD" in str(exc):
                raise FlashPmodError(
                    "RP2040 firmware is old; reload build/rp2040_flash_pmod/rp2040_flash_pmod.uf2"
                ) from exc
            raise
        print(f"JEDEC: {dev.jedec()}")
    finally:
        dev.close()


def cmd_drive(args) -> None:
    dev = FlashPmod(args.port or autodetect_port())
    try:
        print(dev.drive(args.cs, args.sck, args.mosi))
    finally:
        dev.close()


def cmd_reset(args) -> None:
    dev = FlashPmod(args.port or autodetect_port())
    try:
        print(dev.ping())
        if args.wake_only:
            print(dev.wake())
        else:
            print(dev.reset_flash())
        print(f"JEDEC: {dev.jedec()}")
    finally:
        dev.close()


def cmd_wren(args) -> None:
    dev = FlashPmod(args.port or autodetect_port())
    try:
        print(dev.ping())
        print(dev.wren())
        print(f"RDSR: 0x{dev.rdsr():02X}")
    finally:
        dev.close()


def cmd_read(args) -> None:
    dev = FlashPmod(args.port or autodetect_port())
    try:
        require_jedec(dev, args.expected_jedec)
        remaining = args.length
        addr = args.addr
        out = bytearray()
        while remaining:
            n = min(CHUNK_SIZE, remaining)
            out += dev.read(addr, n)
            addr += n
            remaining -= n
        if args.output:
            Path(args.output).write_bytes(out)
            print(f"wrote {len(out)} bytes to {args.output}")
        else:
            for i in range(0, len(out), 16):
                row = out[i:i + 16]
                print(f"{args.addr + i:06X}: " + " ".join(f"{b:02X}" for b in row))
    finally:
        dev.close()


def cmd_write(args) -> None:
    image = Path(args.image).read_bytes()
    offset = args.offset
    sectors = list(iter_dirty_sectors(image, offset, skip_ff=not args.program_ff))
    if not sectors:
        print("nothing to program")
        return

    dev = FlashPmod(args.port or autodetect_port(), timeout=20.0)
    try:
        print(dev.ping())
        pins = dev.pins_optional()
        if pins is not None:
            print(pins)
        require_jedec(dev, args.expected_jedec, attempts=5)
        print(
            f"programming {args.image} ({len(image)} bytes) at 0x{offset:06X}; "
            f"{len(sectors)} dirty sectors"
        )

        for index, (sector_addr, rel0, rel1) in enumerate(sectors, 1):
            print(f"[{index:04d}/{len(sectors):04d}] erase 0x{sector_addr:06X}")
            dev.erase4k(sector_addr)

            pos = rel0
            while pos < rel1:
                write1 = min(pos + CHUNK_SIZE, rel1)
                chunk = image[pos:write1]
                abs_addr = offset + pos
                pos = write1
                if not args.program_ff and all(b == 0xFF for b in chunk):
                    continue
                print(f"           write 0x{abs_addr:06X} +{len(chunk)}")
                dev.write_chunk(abs_addr, chunk)

        if args.verify:
            print("verifying")
            for sector_addr, rel0, rel1 in sectors:
                expected = image[rel0:rel1]
                actual = bytearray()
                addr = offset + rel0
                remaining = len(expected)
                while remaining:
                    n = min(CHUNK_SIZE, remaining)
                    actual += dev.read(addr, n)
                    addr += n
                    remaining -= n
                actual_b = bytes(actual)
                mismatch = first_mismatch(expected, actual_b)
                if mismatch is not None:
                    win0 = max(0, mismatch - 8)
                    win1 = min(len(expected), mismatch + 24)
                    abs_mismatch = offset + rel0 + mismatch
                    raise FlashPmodError(
                        f"verify mismatch at 0x{abs_mismatch:06X}\n"
                        f"expected[{win0:04X}:{win1:04X}]: {hexdump_line(expected[win0:win1])}\n"
                        f"actual  [{win0:04X}:{win1:04X}]: {hexdump_line(actual_b[win0:win1])}"
                    )
            print("verify OK")
    finally:
        dev.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="serial port, defaults to first /dev/ttyACM*")
    parser.add_argument("--expected-jedec", default=EXPECTED_JEDEC)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_id = sub.add_parser("id", help="read JEDEC ID and status")
    p_id.set_defaults(func=cmd_id)

    p_diag = sub.add_parser("diag", help="show pin mapping and passive MISO line diagnostics")
    p_diag.set_defaults(func=cmd_diag)

    p_drive = sub.add_parser("drive", help="hold CS/SCK/MOSI static for meter probing")
    p_drive.add_argument("--cs", required=True, type=parse_int, choices=(0, 1))
    p_drive.add_argument("--sck", required=True, type=parse_int, choices=(0, 1))
    p_drive.add_argument("--mosi", required=True, type=parse_int, choices=(0, 1))
    p_drive.set_defaults(func=cmd_drive)

    p_reset = sub.add_parser("reset", help="wake or soft-reset the external SPI flash")
    p_reset.add_argument("--wake-only", action="store_true")
    p_reset.set_defaults(func=cmd_reset)

    p_wren = sub.add_parser("wren", help="issue WREN and report status register")
    p_wren.set_defaults(func=cmd_wren)

    p_read = sub.add_parser("read", help="read flash bytes")
    p_read.add_argument("--addr", required=True, type=parse_int)
    p_read.add_argument("--length", required=True, type=parse_int)
    p_read.add_argument("--output")
    p_read.set_defaults(func=cmd_read)

    p_write = sub.add_parser("write", help="erase/program/verify non-FF sectors")
    p_write.add_argument("image")
    p_write.add_argument("--offset", default=0, type=parse_int)
    p_write.add_argument("--program-ff", action="store_true", help="program all sectors, including all-FF sectors")
    p_write.add_argument("--no-verify", dest="verify", action="store_false")
    p_write.set_defaults(func=cmd_write, verify=True)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except FlashPmodError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
