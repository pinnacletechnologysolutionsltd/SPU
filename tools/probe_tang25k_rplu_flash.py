#!/usr/bin/env python3
"""Load the Tang Primer 25K RPLU probe and verify SPI/RPLU UART telemetry."""

import argparse
import os
import re
import select
import subprocess
import sys
import termios
import time
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BITSTREAM = ROOT / "build" / "tang_primer_25k_spu13_rplu_probe.fs"
DEFAULT_PORTS = [
    "/dev/serial/by-id/usb-SIPEED_USB_Debugger_2025030317-if01-port0",
    "/dev/ttyUSB1",
    "/dev/serial/by-id/usb-SIPEED_USB_Debugger_2025030317-if00-port0",
    "/dev/ttyUSB0",
]

JEDEC_RE = re.compile(r"B:([0-9A-Fa-f]{8}) A:([0-9A-Fa-f])")
RPLU_RE = re.compile(r"R:([0-9A-Fa-f]{8}) A:([0-9A-Fa-f])")
SDRAM_RE = re.compile(r"M:([0-9A-Fa-f]{8}) A:([0-9A-Fa-f])")
SDRAM_WORDS = 52
SDRAM_DQ_PIN_HINTS = {
    0: ("K2", "J3 pin 1"),
    1: ("K1", "J3 pin 2"),
    2: ("L1", "J3 pin 3"),
    3: ("L2", "J3 pin 4"),
    4: ("K4", "J3 pin 5"),
    5: ("J4", "J3 pin 6"),
    6: ("G1", "J3 pin 7"),
    7: ("G2", "J3 pin 8"),
    8: ("L3", "J3 pin 9"),
    9: ("L4", "J3 pin 10"),
    10: ("B2", "J3 pin 14"),
    11: ("C2", "J3 pin 13"),
    12: ("F2", "J3 pin 16"),
    13: ("F1", "J3 pin 15"),
    14: ("E1", "J3 pin 18"),
    15: ("A1", "J3 pin 17"),
}


def parse_u32(text):
    return int(text, 0)


def resolve_port(port):
    if port != "auto":
        return port
    for candidate in DEFAULT_PORTS:
        if os.path.exists(candidate):
            return candidate
    raise SystemExit("No Sipeed FTDI UART port found")


def configure_tty(fd, baud):
    if baud != 115200:
        raise SystemExit("Only 115200 baud is currently supported")

    attrs = termios.tcgetattr(fd)
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR | termios.IGNCR |
                  termios.ICRNL | termios.IXON | termios.IXOFF)
    attrs[1] &= ~termios.OPOST
    attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
    if hasattr(termios, "CRTSCTS"):
        attrs[2] &= ~termios.CRTSCTS
    attrs[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                  termios.ISIG | termios.IEXTEN)
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)


def load_bitstream(bitstream):
    if not bitstream.exists():
        raise SystemExit(f"Missing bitstream: {bitstream}")
    cmd = ["openFPGALoader", "-b", "tangprimer25k", str(bitstream)]
    subprocess.run(cmd, cwd=ROOT, check=True)


def capture_uart(port, seconds, baud, verbose, stop_when=None):
    fd = os.open(port, os.O_RDONLY | os.O_NONBLOCK)
    try:
        configure_tty(fd, baud)
        return capture_uart_fd(fd, seconds, verbose, stop_when)
    finally:
        os.close(fd)


def capture_uart_fd(fd, seconds, verbose, stop_when=None):
    deadline = time.monotonic() + seconds
    chunks = []
    text_so_far = ""
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.25)
        if not ready:
            continue
        data = os.read(fd, 4096)
        if not data:
            continue
        text = data.decode("ascii", errors="ignore")
        chunks.append(text)
        if verbose:
            sys.stdout.write(text)
            sys.stdout.flush()
        text_so_far = "".join(chunks)
        if stop_when is not None and stop_when(text_so_far):
            return text_so_far
    return text_so_far


def decode_rplu(value):
    return {
        "marker": (value >> 23) & 0x1FF,
        "mask": (value >> 10) & 0x1FFF,
        "addr": value & 0x3FF,
    }


def sdram_pattern(idx):
    idx &= 0x3F
    return 0xA55A ^ ((idx << 10) | (((~idx) & 0x3F) << 4) | (idx & 0x0F))


def expected_sdram_endpoints(stuck_high_mask=0):
    return ((sdram_pattern(0) | stuck_high_mask) << 16) | (
        sdram_pattern(SDRAM_WORDS - 1) | stuck_high_mask
    )


def expected_sdram_checksum(stuck_high_mask=0):
    return sum(
        sdram_pattern(idx) | stuck_high_mask for idx in range(SDRAM_WORDS)
    ) & 0xFFFFFFFF


def decode_sdram_status(value):
    return {
        "marker": (value >> 24) & 0xFF,
        "tag": (value >> 16) & 0xFF,
        "done": (value >> 15) & 0x1,
        "pass": (value >> 14) & 0x1,
        "fail": (value >> 13) & 0x1,
        "write_done": (value >> 12) & 0x1,
        "read_done": (value >> 11) & 0x1,
        "state": (value >> 8) & 0x7,
        "mismatches": value & 0x3F,
    }


def is_power_of_two(value):
    return value != 0 and (value & (value - 1)) == 0


def sdram_pin_hint(bit):
    hint = SDRAM_DQ_PIN_HINTS.get(bit)
    if hint is None:
        return ""
    fpga_pin, connector_pin = hint
    return f" FPGA pin {fpga_pin}, SDRAM connector {connector_pin}."


def diagnose_sdram_data_line(sdram):
    status = sdram["status_observed_decoded"]
    endpoints_value = sdram["endpoints_observed_value"]
    checksum_value = sdram["checksum_observed_value"]
    if status is None or endpoints_value is None or checksum_value is None:
        return None

    expected_endpoints = sdram["expected_endpoints"]
    expected_checksum = sdram["expected_checksum"]
    expected_first = (expected_endpoints >> 16) & 0xFFFF
    expected_last = expected_endpoints & 0xFFFF
    observed_first = (endpoints_value >> 16) & 0xFFFF
    observed_last = endpoints_value & 0xFFFF
    first_xor = observed_first ^ expected_first
    last_xor = observed_last ^ expected_last
    mismatches = status["mismatches"]
    if first_xor == 0 or first_xor != last_xor or not is_power_of_two(first_xor):
        return None

    bit = first_xor.bit_length() - 1
    bit_mask = 1 << bit
    checksum_delta = checksum_value - expected_checksum
    if mismatches and checksum_delta == mismatches * bit_mask:
        direction = "stuck high"
    elif mismatches and checksum_delta == -mismatches * bit_mask:
        direction = "stuck low"
    else:
        direction = "single-bit error"

    return (
        f"Likely SDRAM DQ[{bit}] {direction}: endpoints XOR=0x{first_xor:04X}, "
        f"checksum delta=0x{checksum_delta & 0xFFFFFFFF:08X}, "
        f"mismatches={mismatches}.{sdram_pin_hint(bit)}"
    )


def diagnose_sdram_error_masks(sdram):
    value = sdram["error_mask_observed_value"]
    if value is None:
        return None
    exp1_obs0 = (value >> 16) & 0xFFFF
    exp0_obs1 = value & 0xFFFF
    stuck_high_mask = sdram.get("stuck_high_mask", 0) & 0xFFFF
    if stuck_high_mask != 0 and exp1_obs0 == 0 and exp0_obs1 == stuck_high_mask:
        return (
            "SDRAM mask diagnosis: observed expected-0/read-1 mask matches "
            f"configured stuck-high mask 0x{stuck_high_mask:04X}."
        )
    if exp0_obs1 != 0 and exp1_obs0 == 0 and is_power_of_two(exp0_obs1):
        bit = exp0_obs1.bit_length() - 1
        return (
            f"SDRAM mask diagnosis: DQ[{bit}] reads high when expected low."
            f"{sdram_pin_hint(bit)}"
        )
    if exp1_obs0 != 0 and exp0_obs1 == 0 and is_power_of_two(exp1_obs0):
        bit = exp1_obs0.bit_length() - 1
        return (
            f"SDRAM mask diagnosis: DQ[{bit}] reads low when expected high."
            f"{sdram_pin_hint(bit)}"
        )
    return (
        "SDRAM mask diagnosis: "
        f"expected-1/read-0=0x{exp1_obs0:04X}, "
        f"expected-0/read-1=0x{exp0_obs1:04X}"
    )


def load_expected_checksum(value):
    if value != "auto":
        return parse_u32(value)

    summary = ROOT / "build" / "rplu_metrics" / "rplu_metric_summary.json"
    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8"))
        checksum = data.get("flash", {}).get("rtl_checksum")
        if checksum:
            return int(checksum, 16)

    payload = ROOT / "build" / "rplu_boot_chords.bin"
    if payload.exists():
        data = payload.read_bytes()
        if len(data) % 16 != 0:
            raise SystemExit(f"{payload} length is not a multiple of 16 bytes")
        total = 0
        for offset in range(0, len(data), 16):
            header = int.from_bytes(data[offset:offset + 8], "big")
            chord_data = int.from_bytes(data[offset + 8:offset + 16], "big")
            total = (
                total
                + ((header >> 32) & 0xFFFFFFFF)
                + (header & 0xFFFFFFFF)
                + ((chord_data >> 32) & 0xFFFFFFFF)
                + (chord_data & 0xFFFFFFFF)
            ) & 0xFFFFFFFF
        return total

    return None


def load_expected_loaded(value):
    if value != "auto":
        return parse_u32(value)

    summary = ROOT / "build" / "rplu_metrics" / "rplu_metric_summary.json"
    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8"))
        records = data.get("flash", {}).get("records")
        if records is not None:
            return int(records)

    payload = ROOT / "build" / "rplu_boot_chords.bin"
    if payload.exists():
        size = payload.stat().st_size
        if size % 16 != 0:
            raise SystemExit(f"{payload} length is not a multiple of 16 bytes")
        return size // 16

    return 2051


def find_capture_matches(
    text,
    expected_jedec,
    expected_marker,
    expected_mask,
    expected_addr,
    expected_loaded,
    expected_checksum,
    expected_rplu2_thimble_c0=None,
    expected_rplu2_quadray_delta=None,
    expected_rplu2_consume_status=None,
    sdram_stuck_high_mask=0,
):
    jedec_match = None
    for match in JEDEC_RE.finditer(text):
        value = int(match.group(1), 16)
        if (value & 0x00FFFFFF) == expected_jedec:
            jedec_match = match.group(0)
            break

    rplu_match = None
    rplu_decoded = None
    loaded_match = None
    checksum_match = None
    thimble_match = None
    thimble_observed = None
    thimble_value = None
    quadray_delta_match = None
    quadray_delta_observed = None
    quadray_delta_value = None
    consume_status_match = None
    consume_status_observed = None
    consume_status_value = None
    for match in RPLU_RE.finditer(text):
        value = int(match.group(1), 16)
        axis = int(match.group(2), 16)
        if axis == 0x8:
            thimble_observed = match.group(0)
            thimble_value = value
            if expected_rplu2_thimble_c0 is not None and value == expected_rplu2_thimble_c0:
                thimble_match = match.group(0)
            continue
        if axis == 0x9:
            quadray_delta_observed = match.group(0)
            quadray_delta_value = value
            if expected_rplu2_quadray_delta is not None and value == expected_rplu2_quadray_delta:
                quadray_delta_match = match.group(0)
            continue
        if axis == 0xA:
            consume_status_observed = match.group(0)
            consume_status_value = value
            if expected_rplu2_consume_status is not None and value == expected_rplu2_consume_status:
                consume_status_match = match.group(0)
            continue
        if axis == 0xE and expected_loaded is not None and (value & 0xFFFF) == expected_loaded:
            loaded_match = match.group(0)
            continue
        if axis == 0xF and expected_checksum is not None and value == expected_checksum:
            checksum_match = match.group(0)
            continue
        if axis != 0xD:
            continue
        decoded = decode_rplu(value)
        if (decoded["marker"] == expected_marker and
                decoded["mask"] == expected_mask and
                decoded["addr"] == expected_addr):
            rplu_match = match.group(0)
            rplu_decoded = decoded

    loaded_ok = expected_loaded is None or loaded_match is not None
    checksum_ok = expected_checksum is None or checksum_match is not None
    rplu2_consume = {
        "thimble_match": thimble_match,
        "thimble_observed": thimble_observed,
        "thimble_value": thimble_value,
        "quadray_delta_match": quadray_delta_match,
        "quadray_delta_observed": quadray_delta_observed,
        "quadray_delta_value": quadray_delta_value,
        "consume_status_match": consume_status_match,
        "consume_status_observed": consume_status_observed,
        "consume_status_value": consume_status_value,
        "expected_thimble_c0": expected_rplu2_thimble_c0,
        "expected_quadray_delta": expected_rplu2_quadray_delta,
        "expected_consume_status": expected_rplu2_consume_status,
        "ok": (
            (expected_rplu2_thimble_c0 is None or thimble_match is not None) and
            (expected_rplu2_quadray_delta is None or quadray_delta_match is not None) and
            (expected_rplu2_consume_status is None or consume_status_match is not None)
        ),
    }

    return {
        "jedec_match": jedec_match,
        "rplu_match": rplu_match,
        "rplu_decoded": rplu_decoded,
        "loaded_match": loaded_match,
        "checksum_match": checksum_match,
        "loaded_ok": loaded_ok,
        "checksum_ok": checksum_ok,
        "rplu2_consume": rplu2_consume,
        "sdram": find_sdram_selftest_matches(text, sdram_stuck_high_mask),
        "core_sdram": find_core_sdram_matches(text),
    }


def find_sdram_selftest_matches(text, stuck_high_mask=0):
    stuck_high_mask &= 0xFFFF
    expected_endpoints = expected_sdram_endpoints(stuck_high_mask)
    expected_checksum = expected_sdram_checksum(stuck_high_mask)
    status_match = None
    status_decoded = None
    status_observed = None
    status_observed_decoded = None
    endpoints_match = None
    endpoints_observed = None
    endpoints_observed_value = None
    checksum_match = None
    checksum_observed = None
    checksum_observed_value = None
    error_mask_observed = None
    error_mask_observed_value = None

    for match in SDRAM_RE.finditer(text):
        value = int(match.group(1), 16)
        axis = int(match.group(2), 16)
        if axis == 0x6:
            error_mask_observed = match.group(0)
            error_mask_observed_value = value
        elif axis == 0xA:
            decoded = decode_sdram_status(value)
            if decoded["marker"] == 0x5D and decoded["tag"] == 0xA5:
                status_observed = match.group(0)
                status_observed_decoded = decoded
            if (decoded["marker"] == 0x5D and
                    decoded["tag"] == 0xA5 and
                    decoded["done"] == 1 and
                    decoded["pass"] == 1 and
                    decoded["fail"] == 0 and
                    decoded["write_done"] == 1 and
                    decoded["read_done"] == 1 and
                    decoded["mismatches"] == 0):
                status_match = match.group(0)
                status_decoded = decoded
        elif axis == 0xB:
            endpoints_observed = match.group(0)
            endpoints_observed_value = value
            if value == expected_endpoints:
                endpoints_match = match.group(0)
        elif axis == 0xC:
            checksum_observed = match.group(0)
            checksum_observed_value = value
            if value == expected_checksum:
                checksum_match = match.group(0)

    return {
        "status_match": status_match,
        "status_decoded": status_decoded,
        "status_observed": status_observed,
        "status_observed_decoded": status_observed_decoded,
        "endpoints_match": endpoints_match,
        "endpoints_observed": endpoints_observed,
        "endpoints_observed_value": endpoints_observed_value,
        "checksum_match": checksum_match,
        "checksum_observed": checksum_observed,
        "checksum_observed_value": checksum_observed_value,
        "error_mask_observed": error_mask_observed,
        "error_mask_observed_value": error_mask_observed_value,
        "expected_endpoints": expected_endpoints,
        "expected_checksum": expected_checksum,
        "stuck_high_mask": stuck_high_mask,
        "ok": (
            status_match is not None and
            endpoints_match is not None and
            checksum_match is not None
        ),
    }


def find_core_sdram_matches(text):
    status_match = None
    status_decoded = None
    status_observed = None
    status_observed_decoded = None
    write_checksum_match = None
    write_checksum_value = None
    read_checksum_match = None
    read_checksum_value = None

    for match in SDRAM_RE.finditer(text):
        value = int(match.group(1), 16)
        axis = int(match.group(2), 16)
        if axis == 0x7:
            decoded = decode_sdram_status(value)
            if decoded["marker"] == 0xC0 and decoded["tag"] == 0x5D:
                status_observed = match.group(0)
                status_observed_decoded = decoded
            if (decoded["marker"] == 0xC0 and
                    decoded["tag"] == 0x5D and
                    decoded["done"] == 1 and
                    decoded["pass"] == 1 and
                    decoded["fail"] == 0 and
                    decoded["write_done"] == 1 and
                    decoded["read_done"] == 1):
                status_match = match.group(0)
                status_decoded = decoded
        elif axis == 0x8:
            write_checksum_match = match.group(0)
            write_checksum_value = value
        elif axis == 0x9:
            read_checksum_match = match.group(0)
            read_checksum_value = value

    checksums_ok = (
        write_checksum_value is not None and
        read_checksum_value is not None and
        write_checksum_value == read_checksum_value and
        write_checksum_value != 0
    )
    return {
        "status_match": status_match,
        "status_decoded": status_decoded,
        "status_observed": status_observed,
        "status_observed_decoded": status_observed_decoded,
        "write_checksum_match": write_checksum_match,
        "write_checksum_value": write_checksum_value,
        "read_checksum_match": read_checksum_match,
        "read_checksum_value": read_checksum_value,
        "ok": status_match is not None and checksums_ok,
    }


def capture_matches_ok(
    matches,
    expect_sdram_selftest=False,
    sdram_only=False,
    expect_core_sdram=False,
    expect_rplu2_consume=False,
):
    rplu_ok = (
        matches["jedec_match"] is not None and
        matches["rplu_match"] is not None and
        matches["loaded_ok"] and
        matches["checksum_ok"]
    )
    if sdram_only:
        return matches["sdram"]["ok"] if expect_sdram_selftest else True
    if expect_core_sdram and not matches["core_sdram"]["ok"]:
        return False
    if expect_rplu2_consume and not matches["rplu2_consume"]["ok"]:
        return False
    if expect_sdram_selftest:
        return rplu_ok and matches["sdram"]["ok"]
    return rplu_ok


def capture_satisfies(
    text,
    expected_jedec,
    expected_marker,
    expected_mask,
    expected_addr,
    expected_loaded,
    expected_checksum,
    expected_rplu2_thimble_c0,
    expected_rplu2_quadray_delta,
    expected_rplu2_consume_status,
    expect_sdram_selftest,
    expect_core_sdram,
    expect_rplu2_consume,
    sdram_only,
    sdram_stuck_high_mask,
):
    return capture_matches_ok(find_capture_matches(
        text,
        expected_jedec,
        expected_marker,
        expected_mask,
        expected_addr,
        expected_loaded,
        expected_checksum,
        expected_rplu2_thimble_c0 if expect_rplu2_consume else None,
        expected_rplu2_quadray_delta if expect_rplu2_consume else None,
        expected_rplu2_consume_status if expect_rplu2_consume else None,
        sdram_stuck_high_mask,
    ), expect_sdram_selftest, sdram_only, expect_core_sdram, expect_rplu2_consume)


def check_capture(
    text,
    expected_jedec,
    expected_marker,
    expected_mask,
    expected_addr,
    expected_loaded,
    expected_checksum,
    expected_rplu2_thimble_c0,
    expected_rplu2_quadray_delta,
    expected_rplu2_consume_status,
    expect_sdram_selftest,
    expect_core_sdram,
    expect_rplu2_consume,
    sdram_only,
    sdram_stuck_high_mask,
):
    matches = find_capture_matches(
        text,
        expected_jedec,
        expected_marker,
        expected_mask,
        expected_addr,
        expected_loaded,
        expected_checksum,
        expected_rplu2_thimble_c0 if expect_rplu2_consume else None,
        expected_rplu2_quadray_delta if expect_rplu2_consume else None,
        expected_rplu2_consume_status if expect_rplu2_consume else None,
        sdram_stuck_high_mask,
    )

    if capture_matches_ok(
            matches,
            expect_sdram_selftest,
            sdram_only,
            expect_core_sdram,
            expect_rplu2_consume):
        if not sdram_only:
            rplu_decoded = matches["rplu_decoded"]
            print(f"SPI JEDEC: {matches['jedec_match']}")
            print(
                "RPLU: "
                f"{matches['rplu_match']} "
                f"marker=0x{rplu_decoded['marker']:03X} "
                f"mask=0x{rplu_decoded['mask']:04X} "
                f"addr=0x{rplu_decoded['addr']:03X}"
            )
            if matches["loaded_match"]:
                print(f"RPLU loaded: {matches['loaded_match']} count={expected_loaded}")
            if matches["checksum_match"]:
                print(f"RPLU checksum: {matches['checksum_match']} checksum=0x{expected_checksum:08X}")
            if expect_rplu2_consume:
                consume = matches["rplu2_consume"]
                print(
                    "RPLU2 consume result: "
                    f"{consume['thimble_match']} "
                    f"value=0x{consume['expected_thimble_c0']:08X}"
                )
                print(
                    "RPLU2 consume quadray: "
                    f"{consume['quadray_delta_match']} "
                    f"delta=0x{consume['expected_quadray_delta']:08X}"
                )
                print(
                    "RPLU2 consume status: "
                    f"{consume['consume_status_match']} "
                    f"status=0x{consume['expected_consume_status']:08X}"
                )
        if expect_sdram_selftest:
            sdram = matches["sdram"]
            status = sdram["status_decoded"]
            endpoints = int(sdram["endpoints_match"].split()[0][2:], 16)
            print(
                "SDRAM selftest: "
                f"{sdram['status_match']} "
                f"state={status['state']} mismatches={status['mismatches']}"
            )
            if sdram["stuck_high_mask"]:
                print(f"SDRAM stuck-high mask: 0x{sdram['stuck_high_mask']:04X}")
            print(
                "SDRAM endpoints: "
                f"{sdram['endpoints_match']} "
                f"first=0x{endpoints >> 16:04X} last=0x{endpoints & 0xFFFF:04X}"
            )
            print(
                "SDRAM checksum: "
                f"{sdram['checksum_match']} checksum=0x{sdram['expected_checksum']:08X}"
            )
            print("SDRAM selftest PASS")
        if expect_core_sdram:
            core_sdram = matches["core_sdram"]
            status = core_sdram["status_decoded"]
            print(
                "Core SDRAM verify: "
                f"{core_sdram['status_match']} "
                f"state={status['state']}"
            )
            print(
                "Core SDRAM checksum: "
                f"write={core_sdram['write_checksum_match']} "
                f"read={core_sdram['read_checksum_match']} "
                f"checksum=0x{core_sdram['write_checksum_value']:08X}"
            )
            print("Core SDRAM readback PASS")
        if sdram_only:
            print("SDRAM hardware probe PASS")
        else:
            print("RPLU hardware probe PASS")
        return 0

    print("SDRAM hardware probe FAIL" if sdram_only else "RPLU hardware probe FAIL")
    if not sdram_only:
        if not matches["jedec_match"]:
            print(f"Missing JEDEC marker for 0x{expected_jedec:06X}")
        if not matches["rplu_match"]:
            print(
                "Missing RPLU marker "
                f"marker=0x{expected_marker:03X} "
                f"mask=0x{expected_mask:04X} "
                f"addr=0x{expected_addr:03X}"
            )
        if not matches["loaded_ok"]:
            print(f"Missing RPLU loaded count {expected_loaded}")
        if not matches["checksum_ok"]:
            print(f"Missing RPLU checksum 0x{expected_checksum:08X}")
        if expect_rplu2_consume:
            consume = matches["rplu2_consume"]
            if not consume["thimble_match"]:
                print(f"Missing RPLU2 consume result 0x{consume['expected_thimble_c0']:08X} on R axis 8")
                if consume["thimble_observed"]:
                    print(f"Observed RPLU2 consume result: {consume['thimble_observed']}")
            if not consume["quadray_delta_match"]:
                print(f"Missing RPLU2 quadray delta 0x{consume['expected_quadray_delta']:08X} on R axis 9")
                if consume["quadray_delta_observed"]:
                    print(f"Observed RPLU2 quadray delta: {consume['quadray_delta_observed']}")
            if not consume["consume_status_match"]:
                print(f"Missing RPLU2 consume status 0x{consume['expected_consume_status']:08X} on R axis A")
                if consume["consume_status_observed"]:
                    print(f"Observed RPLU2 consume status: {consume['consume_status_observed']}")
    if expect_sdram_selftest:
        sdram = matches["sdram"]
        if not sdram["status_match"]:
            print("Missing SDRAM selftest pass status on M axis A")
            status = sdram["status_observed_decoded"]
            if status:
                print(
                    "Observed SDRAM status: "
                    f"{sdram['status_observed']} "
                    f"done={status['done']} pass={status['pass']} fail={status['fail']} "
                    f"write_done={status['write_done']} read_done={status['read_done']} "
                    f"state={status['state']} mismatches={status['mismatches']}"
                )
        if not sdram["endpoints_match"]:
            print(f"Missing SDRAM endpoints 0x{sdram['expected_endpoints']:08X} on M axis B")
            if sdram["endpoints_observed"]:
                value = sdram["endpoints_observed_value"]
                print(
                    "Observed SDRAM endpoints: "
                    f"{sdram['endpoints_observed']} "
                    f"first=0x{value >> 16:04X} last=0x{value & 0xFFFF:04X}"
                )
        if not sdram["checksum_match"]:
            print(f"Missing SDRAM checksum 0x{sdram['expected_checksum']:08X} on M axis C")
            if sdram["checksum_observed"]:
                print(f"Observed SDRAM checksum: {sdram['checksum_observed']}")
        if sdram["error_mask_observed"]:
            value = sdram["error_mask_observed_value"]
            print(
                "Observed SDRAM bit-error masks: "
                f"{sdram['error_mask_observed']} "
                f"expected-1/read-0=0x{value >> 16:04X} "
                f"expected-0/read-1=0x{value & 0xFFFF:04X}"
            )
            mask_diagnosis = diagnose_sdram_error_masks(sdram)
            if mask_diagnosis:
                print(mask_diagnosis)
        diagnosis = diagnose_sdram_data_line(sdram)
        if diagnosis:
            print(diagnosis)
        value = sdram["endpoints_observed_value"]
        if value is not None and (value >> 16) == (value & 0xFFFF):
            print(
                "SDRAM readback is fixed; on Tang Primer 25K this usually points "
                "to a missing/inactive 40-pin SDRAM module or an SDRAM pin/clock issue."
            )
    if expect_core_sdram:
        core_sdram = matches["core_sdram"]
        if not core_sdram["status_match"]:
            print("Missing core SDRAM readback pass status on M axis 7")
            status = core_sdram["status_observed_decoded"]
            if status:
                print(
                    "Observed core SDRAM status: "
                    f"{core_sdram['status_observed']} "
                    f"done={status['done']} pass={status['pass']} fail={status['fail']} "
                    f"write_done={status['write_done']} read_done={status['read_done']} "
                    f"state={status['state']}"
                )
        if core_sdram["write_checksum_value"] is None:
            print("Missing core SDRAM write checksum on M axis 8")
        if core_sdram["read_checksum_value"] is None:
            print("Missing core SDRAM read checksum on M axis 9")
        if (core_sdram["write_checksum_value"] is not None and
                core_sdram["read_checksum_value"] is not None and
                core_sdram["write_checksum_value"] != core_sdram["read_checksum_value"]):
            print(
                "Core SDRAM checksum mismatch: "
                f"write=0x{core_sdram['write_checksum_value']:08X} "
                f"read=0x{core_sdram['read_checksum_value']:08X}"
            )
    lines = [line for line in text.splitlines() if line.strip()]
    if lines:
        print("Last telemetry lines:")
        for line in lines[-40:]:
            print(line)
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bitstream", type=Path, default=DEFAULT_BITSTREAM)
    parser.add_argument("--port", default="auto")
    parser.add_argument("--seconds", type=float, default=45.0)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--no-load", action="store_true")
    parser.add_argument("--settle", type=float, default=0.25)
    parser.add_argument("--expected-jedec", type=parse_u32, default=0xEF4018)
    parser.add_argument("--expected-rplu-marker", type=parse_u32, default=0x1A5)
    parser.add_argument("--expected-rplu-mask", type=parse_u32, default=0x0000)
    parser.add_argument("--expected-rplu-addr", type=parse_u32, default=0x3FF)
    parser.add_argument("--expected-rplu-loaded", default="auto")
    parser.add_argument("--expected-rplu-checksum", default="auto")
    parser.add_argument("--expect-rplu2-consume", action="store_true")
    parser.add_argument("--expected-rplu2-thimble-c0", type=parse_u32, default=0x00000002)
    parser.add_argument("--expected-rplu2-quadray-delta", type=parse_u32, default=0x00000000)
    parser.add_argument("--expected-rplu2-consume-status", type=parse_u32, default=0xC02E0001)
    parser.add_argument("--expect-sdram-selftest", action="store_true")
    parser.add_argument("--expect-core-sdram", action="store_true")
    parser.add_argument("--sdram-stuck-high-mask", type=parse_u32, default=0x0000)
    parser.add_argument("--sdram-only", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.sdram_stuck_high_mask & ~0xFFFF:
        raise SystemExit("--sdram-stuck-high-mask must fit in 16 bits")

    port = resolve_port(args.port)
    expected_loaded = load_expected_loaded(args.expected_rplu_loaded)
    expected_checksum = load_expected_checksum(args.expected_rplu_checksum)
    expect_sdram_selftest = args.expect_sdram_selftest or args.sdram_only
    stop_when = lambda text: capture_satisfies(
        text,
        args.expected_jedec,
        args.expected_rplu_marker,
        args.expected_rplu_mask,
        args.expected_rplu_addr,
        expected_loaded,
        expected_checksum,
        args.expected_rplu2_thimble_c0,
        args.expected_rplu2_quadray_delta,
        args.expected_rplu2_consume_status,
        expect_sdram_selftest,
        args.expect_core_sdram,
        args.expect_rplu2_consume,
        args.sdram_only,
        args.sdram_stuck_high_mask,
    )
    if not args.no_load:
        load_bitstream(args.bitstream)
        time.sleep(args.settle)
        text = capture_uart(port, args.seconds, args.baud, args.verbose, stop_when)
    else:
        text = capture_uart(port, args.seconds, args.baud, args.verbose, stop_when)
    return check_capture(
        text,
        args.expected_jedec,
        args.expected_rplu_marker,
        args.expected_rplu_mask,
        args.expected_rplu_addr,
        expected_loaded,
        expected_checksum,
        args.expected_rplu2_thimble_c0,
        args.expected_rplu2_quadray_delta,
        args.expected_rplu2_consume_status,
        expect_sdram_selftest,
        args.expect_core_sdram,
        args.expect_rplu2_consume,
        args.sdram_only,
        args.sdram_stuck_high_mask,
    )


if __name__ == "__main__":
    raise SystemExit(main())
