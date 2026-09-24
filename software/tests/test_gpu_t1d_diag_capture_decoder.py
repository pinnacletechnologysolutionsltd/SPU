"""Regression tests for the frozen T1d sigrok-capture decoder."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECODER_PATH = ROOT / "tools" / "decode_gpu_t1d_diag_capture.py"
SPEC = importlib.util.spec_from_file_location("gpu_t1d_diag_decoder", DECODER_PATH)
assert SPEC is not None and SPEC.loader is not None
DECODER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DECODER)


READY = bytes.fromhex("D7 01 01 00 01 00 00 00 00 01 00 00 01 00 2F 7E")
TRANSACTION = bytes.fromhex("D7 01 02 01 7B 3F 20 79 01 02 00 00 01 00 7B 7E")


def _uart_samples(payload: bytes, samplerate: int = 24_000_000, baud: int = 115_200) -> bytes:
    samples: list[int] = [1] * 1_000
    samples_per_bit = samplerate / baud
    for value in payload:
        bits = [0] + [(value >> bit) & 1 for bit in range(8)] + [1]
        for bit_index, bit in enumerate(bits):
            left = round(bit_index * samples_per_bit)
            right = round((bit_index + 1) * samples_per_bit)
            samples.extend([bit] * (right - left))
        samples.extend([1] * round(2 * samples_per_bit))
    return bytes(samples)


def _write_sr(path: Path, samples: bytes, chunk_size: int | None = None) -> None:
    metadata = """[global]\nsigrok version=0.5.3\n[device 1]\ncapturefile=logic-1\ntotal probes=1\nsamplerate=24 MHz\nunitsize=1\nprobe1=D0\n"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("version", "2\n")
        archive.writestr("metadata", metadata)
        if chunk_size is None:
            archive.writestr("logic-1", samples)
        else:
            for index in range(0, len(samples), chunk_size):
                chunk_number = index // chunk_size + 1
                archive.writestr(
                    f"logic-1-{chunk_number}", samples[index:index + chunk_size]
                )


def test_frozen_records_decode_and_invalid_candidate_is_not_evidence(tmp_path: Path) -> None:
    invalid = bytearray(READY)
    invalid[14] ^= 0x01
    capture = tmp_path / "capture.sr"
    output = tmp_path / "telemetry.json"
    _write_sr(capture, _uart_samples(READY + bytes(invalid) + TRANSACTION))

    result = DECODER.decode_capture(capture, "D0", 115_200)
    assert [record["raw_hex"] for record in result["records"]] == [
        READY.hex(" "), TRANSACTION.hex(" ")
    ]
    assert len(result["invalid_record_candidates"]) == 1
    assert result["invalid_record_candidates"][0]["record_crc8_valid"] is False
    assert len(result["discarded_bytes"]) == 16

    completed = subprocess.run(
        [
            "python3", str(DECODER_PATH), "--input", str(capture), "--channel", "D0",
            "--baud", "115200", "--output", str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "decoded 2 valid record(s)" in completed.stdout
    document = json.loads(output.read_text(encoding="utf-8"))
    assert len(document["records"]) == 2


def test_chunked_srzip_stream_decodes(tmp_path: Path) -> None:
    capture = tmp_path / "chunked.srzip"
    _write_sr(capture, _uart_samples(READY + TRANSACTION), chunk_size=97)
    result = DECODER.decode_capture(capture, "D0", 115_200)
    assert result["session"]["capture_parts"][0] == "logic-1-1"
    assert len(result["session"]["capture_parts"]) > 1
    assert [record["raw_hex"] for record in result["records"]] == [
        READY.hex(" "), TRANSACTION.hex(" ")
    ]


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="spu_t1d_decoder_test_") as directory:
        test_root = Path(directory)
        test_frozen_records_decode_and_invalid_candidate_is_not_evidence(test_root)
        test_chunked_srzip_stream_decodes(test_root)
    print("PASS: T1d diagnostic capture decoder")
