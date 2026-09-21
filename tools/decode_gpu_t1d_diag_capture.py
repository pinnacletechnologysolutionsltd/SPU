#!/usr/bin/env python3
"""Decode the frozen GPU T1d diagnostic UART from a sigrok session.

The decoder is deliberately self-contained.  A sigrok ``.sr`` session is a
zip archive containing ``metadata`` and a packed ``logic-*`` sample stream;
the diagnostic capture uses one digital channel (D0) sampled at 24 MHz.

Only a complete 16-byte record with the required terminal marker and a valid
CRC8 is promoted to ``records`` in the output.  Invalid candidates, malformed
UART frames, and bytes not belonging to a valid record remain in the JSON so
that a later review cannot mistake a partial decode for evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path
from typing import Any


RECORD_LENGTH = 16
RECORD_MAGIC = 0xD7
RECORD_TERMINAL = 0x7E
CRC8_POLYNOMIAL = 0x07


def crc8_msb(data: bytes) -> int:
    """Return the frozen MSB-first CRC-8 over *data*."""

    crc = 0
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ CRC8_POLYNOMIAL) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def _parse_metadata(raw: bytes) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    section = "global"
    sections[section] = {}
    for raw_line in raw.decode("utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            sections.setdefault(section, {})
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            sections.setdefault(section, {})[key.strip().lower()] = value.strip()
    return sections


def _metadata_value(sections: dict[str, dict[str, str]], key: str) -> str | None:
    key = key.lower()
    for section_name in ("device 1", "global"):
        value = sections.get(section_name, {}).get(key)
        if value is not None:
            return value
    for values in sections.values():
        value = values.get(key)
        if value is not None:
            return value
    return None


def _parse_rate(value: str) -> int:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([kKmMgG]?)\s*[hH][zZ]\s*", value)
    if not match:
        raise ValueError(f"unsupported samplerate metadata: {value!r}")
    number = float(match.group(1))
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000, "g": 1_000_000_000}[match.group(2).lower()]
    rate = int(round(number * multiplier))
    if rate <= 0:
        raise ValueError("samplerate must be positive")
    return rate


def _read_sigrok_session(path: Path, channel: str) -> tuple[list[int], int, dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "metadata" not in names:
            raise ValueError(f"{path} is not a sigrok session: metadata is missing")
        metadata = _parse_metadata(archive.read("metadata"))
        capture_name = _metadata_value(metadata, "capturefile") or "logic-1"
        if capture_name not in names:
            raise ValueError(f"sigrok capture stream {capture_name!r} is missing")

        samplerate_value = _metadata_value(metadata, "samplerate")
        if samplerate_value is None:
            raise ValueError("sigrok metadata has no samplerate")
        samplerate = _parse_rate(samplerate_value)
        unitsize_value = _metadata_value(metadata, "unitsize") or "1"
        try:
            unitsize = int(unitsize_value, 10)
        except ValueError as exc:
            raise ValueError(f"invalid sigrok unitsize: {unitsize_value!r}") from exc
        if unitsize <= 0 or unitsize > 8:
            raise ValueError(f"unsupported sigrok unitsize: {unitsize}")

        probe_number = None
        wanted = channel.strip().lower()
        for section in metadata.values():
            for key, value in section.items():
                match = re.fullmatch(r"probe(\d+)", key)
                if match and value.strip().lower() == wanted:
                    probe_number = int(match.group(1))
                    break
            if probe_number is not None:
                break
        if probe_number is None:
            raise ValueError(f"channel {channel!r} is not present in sigrok metadata")

        packed = archive.read(capture_name)
        if len(packed) % unitsize:
            raise ValueError("sigrok logic stream is not aligned to unitsize")
        samples = [
            int.from_bytes(packed[offset:offset + unitsize], "little")
            for offset in range(0, len(packed), unitsize)
        ]
        session = {
            "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "capturefile": capture_name,
            "channel": channel,
            "probe_number": probe_number,
            "samplerate_hz": samplerate,
            "unitsize": unitsize,
            "sample_count": len(samples),
        }
        return samples, 1 << (probe_number - 1), session


def _sample(samples: list[int], index: int, mask: int) -> int:
    return 1 if samples[index] & mask else 0


def _decode_uart(
    samples: list[int], mask: int, samplerate: int, baud: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if baud <= 0:
        raise ValueError("baud must be positive")
    samples_per_bit = samplerate / baud
    frames: list[dict[str, Any]] = []
    invalid_frames: list[dict[str, Any]] = []
    incomplete_frames: list[dict[str, Any]] = []
    cursor = 0
    previous = 1
    sample_count = len(samples)
    while cursor < sample_count:
        current = _sample(samples, cursor, mask)
        if previous != 1 or current != 0:
            previous = current
            cursor += 1
            continue
        start = cursor
        centers = [int(math.floor(start + (bit + 0.5) * samples_per_bit)) for bit in range(10)]
        if centers[-1] >= sample_count:
            incomplete_frames.append({"start_sample": start, "reason": "capture_ended_mid_frame"})
            break
        bits = [_sample(samples, center, mask) for center in centers]
        frame = {
            "start_sample": start,
            "end_sample": int(math.ceil(start + 10 * samples_per_bit)) - 1,
            "start_bit": bits[0],
            "data_bits_lsb_first": bits[1:9],
            "stop_bit": bits[9],
        }
        if bits[0] != 0 or bits[9] != 1:
            frame["reason"] = "invalid_start_or_stop_bit"
            invalid_frames.append(frame)
        else:
            value = sum(bit << index for index, bit in enumerate(bits[1:9]))
            frame["byte"] = value
            frames.append(frame)
        # A UART frame occupies ten bit periods.  Advancing to its end avoids
        # treating data-bit transitions as new start edges.
        cursor = max(start + 1, int(math.floor(start + 10 * samples_per_bit)))
        previous = 1
    return frames, invalid_frames, incomplete_frames


def _record_fields(raw: bytes) -> dict[str, Any]:
    return {
        "magic": raw[0],
        "version": raw[1],
        "record_type": raw[2],
        "transaction_sequence": raw[3],
        "flags": raw[4],
        "accepted_count": raw[5],
        "payload_crc16": raw[6] | (raw[7] << 8),
        "active_bank": raw[8],
        "terminal_reason": raw[9],
        "frame_wait": raw[10] | (raw[11] << 8),
        "ready_state": raw[12],
        "reserved": raw[13],
        "record_crc8": raw[14],
        "terminal_marker": raw[15],
    }


def decode_capture(path: Path, channel: str, baud: int) -> dict[str, Any]:
    samples, mask, session = _read_sigrok_session(path, channel)
    frames, invalid_frames, incomplete_frames = _decode_uart(
        samples, mask, session["samplerate_hz"], baud
    )
    candidates: list[dict[str, Any]] = []
    valid_records: list[dict[str, Any]] = []
    used_indices: set[int] = set()
    candidate_indices: dict[int, str] = {}
    values = bytes(frame["byte"] for frame in frames)

    for start in range(max(0, len(values) - RECORD_LENGTH + 1)):
        if values[start] != RECORD_MAGIC or any(index in used_indices for index in range(start, start + RECORD_LENGTH)):
            continue
        raw = values[start:start + RECORD_LENGTH]
        calculated_crc = crc8_msb(raw[:14])
        terminal_valid = raw[15] == RECORD_TERMINAL
        crc_valid = raw[14] == calculated_crc
        candidate = {
            "byte_start": start,
            "byte_end": start + RECORD_LENGTH - 1,
            "raw_hex": raw.hex(" "),
            "terminal_marker_valid": terminal_valid,
            "record_crc8_expected": calculated_crc,
            "record_crc8_observed": raw[14],
            "record_crc8_valid": crc_valid,
        }
        if terminal_valid and crc_valid:
            for index in range(start, start + RECORD_LENGTH):
                used_indices.add(index)
            candidate["valid"] = True
            candidate.update({
                "start_sample": frames[start]["start_sample"],
                "end_sample": frames[start + RECORD_LENGTH - 1]["end_sample"],
                "fields": _record_fields(raw),
            })
            valid_records.append(candidate)
        else:
            candidate["valid"] = False
            candidates.append(candidate)
            for index in range(start, start + RECORD_LENGTH):
                candidate_indices.setdefault(index, "invalid_record_candidate")

    discarded_bytes = []
    for index, frame in enumerate(frames):
        if index in used_indices:
            continue
        discarded_bytes.append({
            "stream_index": index,
            "sample_start": frame["start_sample"],
            "sample_end": frame["end_sample"],
            "value": frame["byte"],
            "reason": candidate_indices.get(index, "not_part_of_valid_record"),
        })

    return {
        "format": "SPU_GPU_T1D_DIAG_CAPTURE_V1",
        "input": str(path),
        "session": session,
        "baud": baud,
        "framing": "8N1",
        "uart_frame_count": len(frames),
        "invalid_uart_frames": invalid_frames,
        "incomplete_uart_frames": incomplete_frames,
        "records": valid_records,
        "invalid_record_candidates": candidates,
        "discarded_bytes": discarded_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--baud", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = decode_capture(args.input, args.channel, args.baud)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"decoded {len(result['records'])} valid record(s); output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
