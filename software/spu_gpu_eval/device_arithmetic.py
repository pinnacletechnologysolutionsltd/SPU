"""Finite-width T1d depth setup arithmetic from the selected RTL profile."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .device_packet import DeviceTriangle


ROOT = Path(__file__).resolve().parents[2]
RECIPROCAL_ROM = ROOT / "hardware/rtl/arch/gpu_reciprocal_lut_q15.mem"


def signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def _wrap(value: int, width: int) -> int:
    return signed(value, width)


@lru_cache(maxsize=1)
def reciprocal_rom() -> tuple[int, ...]:
    words = tuple(int(line.strip(), 16) for line in RECIPROCAL_ROM.read_text().splitlines() if line.strip())
    if len(words) != 256 or any(not 0 <= word <= 0xFFFF for word in words):
        raise ValueError("T1d reciprocal ROM must contain 256 unsigned 16-bit words")
    return words


@dataclass(frozen=True)
class PreparedDepth:
    a_z: int
    b_z: int
    c_z: int
    frac_bits: int
    denominator: int
    mantissa: int
    normalization_shift: int
    reciprocal_y: int
    rom_index: int


def _reciprocal(denominator: int) -> tuple[int, int, int, int, int]:
    if denominator == 0:
        return 0, 0, 0, 0, 0
    msb = denominator.bit_length() - 1
    shift = msb - 15
    mantissa = ((denominator >> shift) if shift >= 0 else (denominator << -shift)) & 0xFFFF
    exponent = (31 + shift) & 0x7F
    index = (mantissa >> 7) & 0xFF
    y0 = reciprocal_rom()[index]
    prod0 = (mantissa * y0) & ((1 << 33) - 1)
    err = ((1 << 32) - prod0) & ((1 << 33) - 1)
    prod1 = (err * y0) & ((1 << 49) - 1)
    y = (prod1 >> 31) & 0xFFFF
    return y, exponent, mantissa, shift, index


def prepare_depth(triangle: DeviceTriangle) -> PreparedDepth:
    sums = [0, 0, 0]
    for edge, z in zip(triangle.edges, triangle.z):
        a, b, c = edge
        for index, coefficient in enumerate((a, b, c)):
            term = (abs(coefficient) * z) & ((1 << 37) - 1)
            signed_term = -term if coefficient < 0 else term
            sums[index] = _wrap(sums[index] + signed_term, 40)

    denominator = _wrap(sum(edge[2] for edge in triangle.edges), 34)
    d_negative = denominator < 0
    d_abs = abs(denominator) & ((1 << 34) - 1)
    reciprocal_y, exponent, mantissa, shift, rom_index = _reciprocal(d_abs)
    scaled = []
    for total in sums:
        product = abs(total) * reciprocal_y
        scaled.append(_wrap(-product if ((total < 0) != d_negative) else product, 56))
    return PreparedDepth(
        scaled[0], scaled[1], scaled[2], exponent, denominator,
        mantissa, shift, reciprocal_y, rom_index,
    )
