"""Parser for the fixed SOM1 decision-evidence frame."""

from dataclasses import dataclass
import struct
import zlib


SOM1_MAGIC = b"SOM1"
SOM1_VERSION = 1
SOM1_FRAME_BYTES = 52
_SOM1_STRUCT = struct.Struct(">4sBBBBIIHHHHQQQI")


class SOM1FrameError(ValueError):
    """Raised when a SOM1 frame fails structural or CRC validation."""


@dataclass(frozen=True)
class SOM1Result:
    version: int
    flags: int
    error: int
    map_generation: int
    result_generation: int
    winner: int
    runner_up: int
    label: int
    best_q: int
    second_q: int
    confidence_gap: int

    @property
    def valid(self):
        return bool(self.flags & 0x01)

    @property
    def busy(self):
        return bool(self.flags & 0x02)

    @property
    def has_second(self):
        return bool(self.flags & 0x04)

    @property
    def ambiguous(self):
        return bool(self.flags & 0x08)

    @property
    def map_valid(self):
        return bool(self.flags & 0x10)


def unpack_quadrance(value):
    """Return the packed Q(sqrt(3)) distance as unsigned P, signed Q."""
    p = (value >> 32) & 0xFFFFFFFF
    q = value & 0xFFFFFFFF
    if q & 0x80000000:
        q -= 1 << 32
    return p, q


def parse_som1_frame(raw):
    raw = bytes(raw)
    if len(raw) != SOM1_FRAME_BYTES:
        raise SOM1FrameError(
            "SOM1 frame must be %d bytes, got %d" % (SOM1_FRAME_BYTES, len(raw))
        )

    (
        magic,
        version,
        declared_length,
        flags,
        error,
        map_generation,
        result_generation,
        winner,
        runner_up,
        label,
        reserved,
        best_q,
        second_q,
        confidence_gap,
        stored_crc,
    ) = _SOM1_STRUCT.unpack(raw)

    if magic != SOM1_MAGIC:
        raise SOM1FrameError("bad SOM1 magic %r" % (magic,))
    if version != SOM1_VERSION:
        raise SOM1FrameError("unsupported SOM1 version %d" % version)
    if declared_length != SOM1_FRAME_BYTES:
        raise SOM1FrameError("SOM1 declared length is %d" % declared_length)
    if flags & 0xE0:
        raise SOM1FrameError("SOM1 reserved flag bits are nonzero")
    if reserved != 0:
        raise SOM1FrameError("SOM1 reserved field is nonzero")
    expected_crc = zlib.crc32(raw[:48]) & 0xFFFFFFFF
    if stored_crc != expected_crc:
        raise SOM1FrameError(
            "SOM1 CRC-32 mismatch: stored=0x%08X expected=0x%08X"
            % (stored_crc, expected_crc)
        )

    return SOM1Result(
        version=version,
        flags=flags,
        error=error,
        map_generation=map_generation,
        result_generation=result_generation,
        winner=winner,
        runner_up=runner_up,
        label=label,
        best_q=best_q,
        second_q=second_q,
        confidence_gap=confidence_gap,
    )
