#!/usr/bin/env python3
"""test_spu_host_parser.py — hardware-free parser/transport test for
software/spu_host. Feeds canned byte streams shaped exactly like the real
hardware/rp_common/spu_diag.c console output through a fake serial port,
so the response parser is exercised without a board attached.

No hardware required. Run: python3 software/tests/test_spu_host_parser.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from software.spu_host.client import SPUHostClient, SPUProtocolError
from software.spu_host.som1 import (
    SOM1FrameError,
    SOM1Result,
    encode_som1_frame,
    parse_som1_frame,
)

BANNER = b"\r\nSPU RP diagnostic console ready\r\nType 'help' for commands.\r\n> "


class FakeSerial:
    """Plays back canned command -> response-lines pairs, reproducing the
    firmware's echo-then-respond-then-prompt byte pattern exactly."""

    def __init__(self, responses):
        self._responses = responses
        self._out = bytearray(BANNER)

    @property
    def in_waiting(self):
        return len(self._out)

    def read(self, n):
        chunk = bytes(self._out[:n])
        del self._out[:n]
        return chunk

    def write(self, data):
        cmd = data.decode("ascii").rstrip("\r\n")
        echo = data.replace(b"\n", b"\r\n")  # char echo + CRLF-on-Enter
        lines = self._responses.get(cmd)
        if lines is None:
            lines = ["ERR unknown command: " + cmd]
        body = ("\r\n".join(lines) + "\r\n").encode("ascii")
        self._out += echo + body + b"> "


checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


def make_client(responses):
    ser = FakeSerial(responses)
    client = SPUHostClient(ser, timeout_s=1.0)
    client.connect()
    return client


def test_status():
    client = make_client({
        "status": [
            "OK status raw=13 A5 00 00",
            "   lfi=0x000D flags=0xA5 mode=0x00 fifo_full=0 ratio_valid=1 ratio=2",
        ]
    })
    s = client.status()
    check("status.raw bytes", s["raw"] == bytes.fromhex("13A50000"))
    check("status.lfi", s["lfi"] == 0x000D)
    check("status.flags", s["flags"] == 0xA5)
    check("status.mode", s["mode"] == 0x00)
    check("status.fifo_full", s["fifo_full"] is False)
    check("status.ratio_valid", s["ratio_valid"] is True)
    check("status.ratio", s["ratio"] == 2)


def test_manifold():
    payload = bytes(range(32))
    client = make_client({"manifold": ["OK manifold " + payload.hex(" ").upper()]})
    m = client.manifold()
    check("manifold byte count", len(m) == 32)
    check("manifold roundtrip", m == payload)


def test_scale_table():
    payload = bytes(range(9))
    client = make_client({"scale": ["OK scale " + payload.hex(" ").upper()]})
    sc = client.scale_table()
    check("scale_table byte count", len(sc) == 9)
    check("scale_table roundtrip", sc == payload)


def test_qr_commit():
    client = make_client({
        "qr": [
            "OK qr valid=1 lane=3"
            " A=0x0000000000010000 B=0x0000000000000001"
            " C=0x0000000000000000 D=0xFFFFFFFFFFFFFFFF"
        ]
    })
    qr = client.qr_commit()
    check("qr.valid", qr["valid"] is True)
    check("qr.lane", qr["lane"] == 3)
    check("qr.A", qr["A"] == 0x00010000)
    check("qr.D", qr["D"] == 0xFFFFFFFFFFFFFFFF)


def test_hex_projection():
    client = make_client({
        "hex": ["OK hex valid=1 q=-2 r=5 raw=13 A5 00 00 05"]
    })
    h = client.hex_projection()
    check("hex.valid", h["valid"] is True)
    check("hex.q", h["q"] == -2)
    check("hex.r", h["r"] == 5)
    check("hex.raw", h["raw"] == bytes.fromhex("13A5000005"))


def test_rplu_config_telemetry_minimal():
    client = make_client({
        "cfgtele": [
            "OK cfgtele magic=SPUC count=16 last_sel=0 last_material=1"
            " last_addr=2 last_data=0x0000000000010000 checksum=0x3A0AB5E9"
        ]
    })
    t = client.rplu_config_telemetry()
    check("cfgtele.magic_ok (minimal)", t["magic_ok"] is True)
    check("cfgtele.count (minimal)", t["count"] == 16)
    check("cfgtele.checksum (minimal)", t["checksum"] == 0x3A0AB5E9)
    check("cfgtele no rplu2 fields when absent", "rplu2_sum" not in t)


def test_rplu_config_telemetry_with_rplu2():
    client = make_client({
        "cfgtele": [
            "OK cfgtele magic=SPUC count=149 last_sel=6 last_material=0"
            " last_addr=0 last_data=0x0000000000000003 checksum=0xBA708FD4"
            " rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001 rplu2_num0=0x00000002"
            " rplu2_delta=0x00000000 rplu2_row1=0x00000001 rplu2_kappa=0x00000003"
        ]
    })
    t = client.rplu_config_telemetry()
    check("cfgtele.count (149)", t["count"] == 149)
    check("cfgtele.rplu2_sum", t["rplu2_sum"] == 0x0AA480E7)
    check("cfgtele.rplu2_kappa", t["rplu2_kappa"] == 0x00000003)


def test_write_chord():
    client = make_client({
        "chord 0011223344556677": ["OK chord 00 11 22 33 44 55 66 77"]
    })
    result = client.write_chord(bytes.fromhex("0011223344556677"))
    check("write_chord echoes 8 bytes", result == bytes.fromhex("0011223344556677"))


def test_write_rplu_cfg():
    client = make_client({
        "rplu 3 5 15 0x00000000DEADBEEF": [
            "OK rplu header=0xA503503C00000000 data=0x00000000DEADBEEF"
        ]
    })
    r = client.write_rplu_cfg(3, 5, 15, 0xDEADBEEF)
    check("rplu.header", r["header"] == 0xA503503C00000000)
    check("rplu.data", r["data"] == 0xDEADBEEF)


def test_tensegrity_transport():
    client = make_client({
        "tgrload /TGR/06.tgr 6": ["OK tgrload bytes=468 vector=6"],
        "tgrstatus": [
            "OK tgrstatus version=1 state=8 fault=5 vector=6"
            " flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468"
        ],
    })
    load = client.load_tensegrity_sd("/TGR/06.tgr", 6)
    check("tgrload byte count", load == {"bytes": 468, "vector": 6})
    status = client.tensegrity_status()
    check("tgrstatus exact verdict", status["state"] == 8 and status["fault"] == 5)
    check("tgrstatus diagnostics", status["flags"] == 8 and
          status["error"] == 0 and status["received"] == 468 and
          status["expected"] == 468)


def make_som1_frame():
    return encode_som1_frame(
        SOM1Result(
            version=1,
            flags=0x1D,
            error=0,
            map_generation=3,
            result_generation=9,
            winner=4,
            runner_up=2,
            label=1,
            best_q=0x0000001100000002,
            second_q=0x0000002200000003,
            confidence_gap=0x0000001100000001,
        )
    )


def test_som1_result():
    frame = make_som1_frame()
    check("som1 software encoder round trip", encode_som1_frame(
        parse_som1_frame(frame)
    ) == frame)
    client = make_client({"som1": ["OK som1 raw=" + frame.hex(" ").upper()]})
    result = client.som1_result()
    check("som1 generations", result.map_generation == 3 and
          result.result_generation == 9)
    check("som1 nodes/label", (result.winner, result.runner_up, result.label) ==
          (4, 2, 1))
    check("som1 flags", result.valid and not result.busy and
          result.has_second and result.ambiguous and result.map_valid)
    check("som1 evidence", result.best_q == 0x0000001100000002 and
          result.confidence_gap == 0x0000001100000001)


def test_som1_rejects_malformed():
    good = make_som1_frame()
    mutations = [
        good[:-1],
        b"BAD!" + good[4:],
        good[:4] + bytes([2]) + good[5:],
        good[:5] + bytes([51]) + good[6:],
        good[:6] + bytes([good[6] | 0x80]) + good[7:],
        good[:22] + b"\x00\x01" + good[24:],
        good[:30] + bytes([good[30] ^ 1]) + good[31:],
    ]
    for index, malformed in enumerate(mutations):
        raised = False
        try:
            parse_som1_frame(malformed)
        except SOM1FrameError:
            raised = True
        check("som1 malformed case %d rejected" % index, raised)


def test_err_response_raises():
    client = make_client({"status": ["ERR unknown command: status"]})
    raised = False
    try:
        client.status()
    except SPUProtocolError:
        raised = True
    check("ERR response raises SPUProtocolError", raised)


def main():
    test_status()
    test_manifold()
    test_scale_table()
    test_qr_commit()
    test_hex_projection()
    test_rplu_config_telemetry_minimal()
    test_rplu_config_telemetry_with_rplu2()
    test_write_chord()
    test_write_rplu_cfg()
    test_tensegrity_transport()
    test_som1_result()
    test_som1_rejects_malformed()
    test_err_response_raises()

    print(f"spu_host parser: {checks} checks, {len(failures)} failed")
    if failures:
        for f in failures:
            print("  FAIL:", f)
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
