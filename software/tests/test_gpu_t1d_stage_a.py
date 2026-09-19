"""Stage A checks for the frozen T1d UART fixture and packet boundary."""

from pathlib import Path
import json


ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "fixtures"


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


if __name__ == "__main__":
    test_frozen_t1d_fixture()
    test_payload_packing_matches_scene_loader()
    print("PASS: T1d Stage A fixture checks")
