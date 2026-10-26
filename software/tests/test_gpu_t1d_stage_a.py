"""Stage A checks for the frozen T1d UART fixture and packet boundary."""

from pathlib import Path
import json
from fractions import Fraction


ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "fixtures"


TRIANGLES = [
    {
        "a0": 0, "b0": 560, "c0": 0,
        "a1": 460, "b1": -80, "c1": -18400,
        "a2": -460, "b2": -480, "c2": 276000,
        "r": 15, "g": 0, "b": 0, "z0": 700, "z1": 3600, "z2": 400,
    },
    {
        "a0": 0, "b0": 560, "c0": 0,
        "a1": 460, "b1": -480, "c1": -18400,
        "a2": -460, "b2": -80, "c2": 276000,
        "r": 0, "g": 15, "b": 0, "z0": 700, "z1": 400, "z2": 3600,
    },
]


def decode_scene(payload):
    scene = int.from_bytes(payload, "little")
    names = (
        ("a0", 16), ("b0", 16), ("c0", 32),
        ("a1", 16), ("b1", 16), ("c1", 32),
        ("a2", 16), ("b2", 16), ("c2", 32),
        ("r", 4), ("g", 4), ("b", 4),
        ("z0", 16), ("z1", 16), ("z2", 16),
    )
    decoded = []
    for triangle in range(2):
        fields = {}
        offset = triangle * 252
        for name, width in names:
            value = (scene >> offset) & ((1 << width) - 1)
            if name[0] in "abc" and name[1:] in ("0", "1", "2"):
                if value & (1 << (width - 1)):
                    value -= 1 << width
            fields[name] = value
            offset += width
        decoded.append(fields)
    return decoded


def edge_values(triangle, x, y):
    return [
        triangle["a0"] * x + triangle["b0"] * y + triangle["c0"],
        triangle["a1"] * x + triangle["b1"] * y + triangle["c1"],
        triangle["a2"] * x + triangle["b2"] * y + triangle["c2"],
    ]


def covered(triangle, x, y):
    values = edge_values(triangle, x, y)
    return all(value >= 0 for value in values)


def exact_depth(triangle, x, y):
    values = edge_values(triangle, x, y)
    denominator = sum(values)
    return Fraction(
        values[0] * triangle["z0"]
        + values[1] * triangle["z1"]
        + values[2] * triangle["z2"],
        denominator,
    )


def test_frozen_t1d_fixture():
    payload = bytes.fromhex(
        (FIXTURES / "gpu_t1d_scene_payload_63b.hex").read_text().strip()
    )
    wire = bytes.fromhex(
        (FIXTURES / "gpu_t1d_scene_wire_64b.hex").read_text().strip()
    )
    decoded = json.loads(
        (FIXTURES / "gpu_t1d_scene_decoded.json").read_text()
    )
    assert len(payload) == 63
    assert len(wire) == 64
    assert wire == b"\xA5" + payload
    assert decoded["payload_bytes"] == 63
    assert decoded["wire_bytes"] == 64
    assert decoded["start_byte"] == "A5"


def test_payload_packing_matches_scene_loader():
    payload = bytes.fromhex(
        (FIXTURES / "gpu_t1d_scene_payload_63b.hex").read_text().strip()
    )
    scene = int.from_bytes(payload, "little")
    assert scene.bit_length() <= 504
    assert scene.to_bytes(63, "little") == payload


def test_decoded_scene_and_diagnostic_pixels():
    payload = bytes.fromhex(
        (FIXTURES / "gpu_t1d_scene_payload_63b.hex").read_text().strip()
    )
    decoded = json.loads((FIXTURES / "gpu_t1d_scene_decoded.json").read_text())
    reference = json.loads((FIXTURES / "gpu_t1d_scene_reference.json").read_text())
    assert decoded["triangles"] == TRIANGLES
    actual = decoded_scene = decode_scene(payload)
    assert decoded_scene == TRIANGLES

    for point in reference["diagnostic_pixels"]:
        x, y = point["x"], point["y"]
        hits = [covered(triangle, x, y) for triangle in actual]
        if point["coverage"] == "background":
            assert hits == [False, False]
        elif point["coverage"] == "triangle0":
            assert hits == [True, False]
        elif point["coverage"] == "triangle1":
            assert hits == [False, True]
        else:
            assert hits == [True, True]
            d0, d1 = exact_depth(actual[0], x, y), exact_depth(actual[1], x, y)
            expected = "triangle0" if d0 < d1 else "triangle1" if d1 < d0 else "tie_triangle0"
            assert point["near"] == expected
        selected = actual[0] if point["rgb"] == [15, 0, 0] else actual[1]
        assert point["rgb"] == [selected["r"], selected["g"], selected["b"]]


if __name__ == "__main__":
    test_frozen_t1d_fixture()
    test_payload_packing_matches_scene_loader()
    print("PASS: T1d Stage A fixture checks")
