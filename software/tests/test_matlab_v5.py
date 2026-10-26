#!/usr/bin/env python3
"""Focused tests for the dependency-free MATLAB v5 reader."""

from __future__ import annotations

import struct
import tempfile
import zlib
from pathlib import Path

import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))

from lib.matlab_v5 import MatlabV5Error, NumericArray, load_matlab_v5


def element(data_type: int, payload: bytes) -> bytes:
    padding = b"\0" * ((-len(payload)) & 7)
    return struct.pack("<II", data_type, len(payload)) + payload + padding


def small_element(data_type: int, payload: bytes) -> bytes:
    assert len(payload) <= 4
    return struct.pack("<HH", data_type, len(payload)) + payload.ljust(4, b"\0")


def matrix(name: str, array_class: int, dims: tuple[int, ...], body: bytes) -> bytes:
    payload = element(6, struct.pack("<II", array_class, 0))
    payload += element(5, struct.pack("<" + "i" * len(dims), *dims))
    payload += small_element(1, name.encode("ascii")) if len(name) <= 4 else element(1, name.encode("ascii"))
    payload += body
    return element(14, payload)


def numeric_matrix(name: str, values: tuple[float, ...]) -> bytes:
    return matrix(name, 6, (1, len(values)), element(9, struct.pack("<" + "d" * len(values), *values)))


def char_matrix(name: str, value: str) -> bytes:
    return matrix(name, 4, (1, len(value)), element(4, struct.pack("<" + "H" * len(value), *(ord(c) for c in value))))


def struct_matrix(name: str) -> bytes:
    width = 8
    fields = b"Data\0\0\0\0" + b"Unit\0\0\0\0"
    body = small_element(5, struct.pack("<i", width))
    body += element(1, fields)
    body += numeric_matrix("", (1.25, -2.5))
    body += char_matrix("", "A")
    return matrix(name, 2, (1, 1), body)


def main() -> None:
    header = b"MATLAB 5.0 MAT-file, SPU test".ljust(124, b" ") + b"\0\1IM"
    payload = numeric_matrix("x", (1.0, 2.0, 3.0))
    compressed = element(15, zlib.compress(struct_matrix("sample")))
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "fixture.mat"
        path.write_bytes(header + payload + compressed)
        loaded = load_matlab_v5(path)
        assert set(loaded) == {"x", "sample"}
        assert isinstance(loaded["x"], NumericArray)
        assert tuple(loaded["x"].values) == (1.0, 2.0, 3.0)
        assert tuple(loaded["sample"]["Data"].values) == (1.25, -2.5)
        assert loaded["sample"]["Unit"] == "A"

        bad = Path(temp) / "bad.mat"
        bad.write_bytes(b"not a mat file")
        try:
            load_matlab_v5(bad)
        except MatlabV5Error:
            pass
        else:
            raise AssertionError("malformed file was accepted")

    print("PASS: MATLAB v5 reader (8 checks)")


if __name__ == "__main__":
    main()
