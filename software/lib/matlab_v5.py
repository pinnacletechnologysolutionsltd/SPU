"""Small, dependency-free reader for MATLAB level-5 data files.

This intentionally supports the data classes needed by the Paderborn bearing
corpus: numeric arrays, character arrays, cells, and structures, optionally
wrapped in miCOMPRESSED elements.  It is not intended to replace scipy.io for
arbitrary MATLAB objects.
"""

from __future__ import annotations

import array
import math
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MI_INT8 = 1
MI_UINT8 = 2
MI_INT16 = 3
MI_UINT16 = 4
MI_INT32 = 5
MI_UINT32 = 6
MI_SINGLE = 7
MI_DOUBLE = 9
MI_INT64 = 12
MI_UINT64 = 13
MI_MATRIX = 14
MI_COMPRESSED = 15

MX_CELL = 1
MX_STRUCT = 2
MX_CHAR = 4
MX_DOUBLE = 6
MX_SINGLE = 7
MX_INT8 = 8
MX_UINT8 = 9
MX_INT16 = 10
MX_UINT16 = 11
MX_INT32 = 12
MX_UINT32 = 13
MX_INT64 = 14
MX_UINT64 = 15

_ARRAY_TYPES = {
    MI_INT8: "b",
    MI_UINT8: "B",
    MI_INT16: "h",
    MI_UINT16: "H",
    MI_INT32: "i",
    MI_UINT32: "I",
    MI_SINGLE: "f",
    MI_DOUBLE: "d",
    MI_INT64: "q",
    MI_UINT64: "Q",
}


class MatlabV5Error(ValueError):
    """Raised when a file is malformed or uses an unsupported MATLAB type."""


@dataclass(frozen=True)
class NumericArray:
    """Column-major MATLAB numeric array."""

    dimensions: tuple[int, ...]
    values: array.array

    def __len__(self) -> int:
        return len(self.values)

    def scalar(self) -> int | float:
        if len(self.values) != 1:
            raise MatlabV5Error("numeric array is not scalar")
        return self.values[0]


@dataclass(frozen=True)
class _Element:
    data_type: int
    payload: memoryview
    next_offset: int


def _element(data: memoryview, offset: int, endian: str) -> _Element:
    if offset + 8 > len(data):
        raise MatlabV5Error("truncated MATLAB data-element tag")
    tag = struct.unpack_from(endian + "I", data, offset)[0]
    small_size = tag >> 16
    if small_size:
        data_type = tag & 0xFFFF
        if small_size > 4:
            raise MatlabV5Error("invalid small data-element size")
        return _Element(data_type, data[offset + 4 : offset + 4 + small_size], offset + 8)

    size = struct.unpack_from(endian + "I", data, offset + 4)[0]
    payload_start = offset + 8
    payload_end = payload_start + size
    if payload_end > len(data):
        raise MatlabV5Error("truncated MATLAB data-element payload")
    return _Element(
        tag,
        data[payload_start:payload_end],
        payload_end + ((-size) & 7),
    )


def _numeric(data_type: int, payload: memoryview, endian: str) -> array.array:
    try:
        typecode = _ARRAY_TYPES[data_type]
    except KeyError as exc:
        raise MatlabV5Error(f"unsupported numeric data type {data_type}") from exc
    result = array.array(typecode)
    result.frombytes(payload.tobytes())
    file_little = endian == "<"
    if result.itemsize > 1 and file_little != (sys.byteorder == "little"):
        result.byteswap()
    return result


def _matrix(payload: memoryview, endian: str) -> tuple[str, Any]:
    offset = 0
    flags = _element(payload, offset, endian)
    offset = flags.next_offset
    flag_values = _numeric(flags.data_type, flags.payload, endian)
    if not flag_values:
        raise MatlabV5Error("matrix has no array flags")
    array_class = int(flag_values[0]) & 0xFF

    dims_element = _element(payload, offset, endian)
    offset = dims_element.next_offset
    dimensions = tuple(int(value) for value in _numeric(
        dims_element.data_type, dims_element.payload, endian
    ))
    if not dimensions or any(value < 0 for value in dimensions):
        raise MatlabV5Error("matrix has invalid dimensions")
    element_count = math.prod(dimensions)

    name_element = _element(payload, offset, endian)
    offset = name_element.next_offset
    name = name_element.payload.tobytes().decode("utf-8", errors="strict")

    if array_class == MX_STRUCT:
        length_element = _element(payload, offset, endian)
        offset = length_element.next_offset
        lengths = _numeric(length_element.data_type, length_element.payload, endian)
        if len(lengths) != 1 or lengths[0] <= 0:
            raise MatlabV5Error("structure has invalid field-name length")
        field_width = int(lengths[0])

        fields_element = _element(payload, offset, endian)
        offset = fields_element.next_offset
        raw_fields = fields_element.payload.tobytes()
        if len(raw_fields) % field_width:
            raise MatlabV5Error("structure field table is misaligned")
        field_names = [
            raw_fields[index : index + field_width].split(b"\0", 1)[0].decode("utf-8")
            for index in range(0, len(raw_fields), field_width)
        ]
        records: list[dict[str, Any]] = []
        for _ in range(element_count):
            record: dict[str, Any] = {}
            for field_name in field_names:
                child = _element(payload, offset, endian)
                offset = child.next_offset
                if child.data_type != MI_MATRIX:
                    raise MatlabV5Error("structure field is not an miMATRIX")
                _, record[field_name] = _matrix(child.payload, endian)
            records.append(record)
        return name, records[0] if element_count == 1 else records

    if array_class == MX_CELL:
        cells: list[Any] = []
        for _ in range(element_count):
            child = _element(payload, offset, endian)
            offset = child.next_offset
            if child.data_type != MI_MATRIX:
                raise MatlabV5Error("cell member is not an miMATRIX")
            _, value = _matrix(child.payload, endian)
            cells.append(value)
        return name, cells

    real = _element(payload, offset, endian)
    if array_class == MX_CHAR:
        chars = _numeric(real.data_type, real.payload, endian)
        return name, "".join(chr(value) for value in chars if value)

    if array_class in {
        MX_DOUBLE, MX_SINGLE, MX_INT8, MX_UINT8, MX_INT16, MX_UINT16,
        MX_INT32, MX_UINT32, MX_INT64, MX_UINT64,
    }:
        values = _numeric(real.data_type, real.payload, endian)
        if len(values) != element_count:
            raise MatlabV5Error(
                f"numeric matrix {name!r} has {len(values)} values, expected {element_count}"
            )
        return name, NumericArray(dimensions, values)

    raise MatlabV5Error(f"unsupported MATLAB array class {array_class} in {name!r}")


def _stream(data: memoryview, endian: str, variables: dict[str, Any]) -> None:
    offset = 0
    while offset < len(data):
        if not any(data[offset:]):
            break
        element = _element(data, offset, endian)
        offset = element.next_offset
        if element.data_type == MI_COMPRESSED:
            inflated = memoryview(zlib.decompress(element.payload))
            _stream(inflated, endian, variables)
        elif element.data_type == MI_MATRIX:
            name, value = _matrix(element.payload, endian)
            variables[name] = value
        else:
            raise MatlabV5Error(f"unsupported top-level data type {element.data_type}")


def load_matlab_v5(path: str | Path) -> dict[str, Any]:
    """Load supported variables from a MATLAB level-5 file."""

    raw = Path(path).read_bytes()
    if len(raw) < 128:
        raise MatlabV5Error("file is shorter than the MATLAB v5 header")
    marker = raw[126:128]
    if marker == b"IM":
        endian = "<"
    elif marker == b"MI":
        endian = ">"
    else:
        raise MatlabV5Error("file does not have a MATLAB v5 endian marker")
    variables: dict[str, Any] = {}
    _stream(memoryview(raw)[128:], endian, variables)
    return variables
