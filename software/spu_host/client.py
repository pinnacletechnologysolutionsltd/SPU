"""client.py — typed wrapper over the Southbridge SPI protocol,
via the RP2350/RP2040 diag console (hardware/rp_common/spu_diag.c).

Opcode -> method mapping (docs/SOUTHBRIDGE_SPI_PROTOCOL.md is the wire
contract of record; this table is the console-command view of it):

    0xAC status    -> status()
    0xA0 manifold  -> manifold()
    0xAD scale     -> scale_table()
    0xAE qr        -> qr_commit()
    0xAF hex       -> hex_projection()
    0xB0 cfgtele   -> rplu_config_telemetry()
    0xB1 chord     -> write_chord(data)
    0xB2 tgrload   -> load_tensegrity_sd(path, vector_id)
    0xB3 tgrstatus -> tensegrity_status()
    0xA5 rplu      -> write_rplu_cfg(sel, material, addr, data)

`raw(cmd)` is the escape hatch for firmware-specific console commands not
part of the frozen protocol (ping, hydrate, classify, result, sd*, ...) —
those vary by probe build, so they are not given typed wrappers here.

**Open discrepancy (docs/SOUTHBRIDGE_SPI_PROTOCOL.md 0xB0 section):** the
protocol doc's original text calls 0xB0 "Sentinel Telemetry" (8 satellite
nodes x 8 bytes), but every currently-exercised firmware path
(`cmd_cfgtele` in spu_diag.c) decodes the same 64 bytes as RPLU2
config-write telemetry (`magic=SPUC`, write-record echo, checksum). This
client follows the firmware that is actually running today; the method
name reflects that, not the original doc text. If a future bitstream
truly reports 8 sentinel nodes on 0xB0, it needs its own method (and the
protocol doc needs the dual-meaning resolved, per its 0xB0 note).
"""

import re

from .console import DiagConsole
from .som1 import parse_som1_frame

_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(\S*)$")
_HEXBYTE_RE = re.compile(r"^[0-9A-Fa-f]{2}$")


class SPUProtocolError(RuntimeError):
    """Raised when the console replies ERR, or a response doesn't parse."""


def _tokenize(lines):
    """Split response lines into (result, kv-dict, leftover-hex-tokens).

    Handles both pure key=value lines (qr, hex's named fields) and the
    "raw=XX" + trailing bare hex-byte tokens style used for byte arrays
    (status, manifold, scale) — the bare tokens are collected in order and
    the caller reassembles them against whichever key introduced them.
    """
    result = None
    kv = {}
    hex_tokens = []
    for line in lines:
        tokens = line.split()
        for tok in tokens:
            if tok in ("OK", "ERR"):
                result = tok
                continue
            m = _KV_RE.match(tok)
            if m:
                kv[m.group(1)] = m.group(2)
            elif _HEXBYTE_RE.match(tok):
                hex_tokens.append(tok)
            # else: command-name word or unrecognized token; ignored
    return result, kv, hex_tokens


def _int_auto(s):
    return int(s, 0)


def _bytes_field(kv, hex_tokens, key):
    """Reassemble a byte-array field: kv[key] holds the first byte (if the
    field used a "key=XX" prefix) and hex_tokens holds the rest, in order."""
    parts = []
    if key in kv and _HEXBYTE_RE.match(kv[key]):
        parts.append(kv[key])
    parts.extend(hex_tokens)
    return bytes.fromhex("".join(parts))


class SPUHostClient:
    """High-level, board-agnostic client for the southbridge console.

    Usage:
        import serial
        from spu_host import SPUHostClient
        ser = serial.Serial("/dev/ttyACM0", 115200, timeout=0.1)
        client = SPUHostClient(ser)
        client.connect()
        print(client.status())
    """

    def __init__(self, ser, timeout_s=2.0):
        self._console = DiagConsole(ser, timeout_s=timeout_s)

    def connect(self):
        """Drain the startup banner. Call once after opening the port."""
        self._console.connect()

    def raw(self, cmd):
        """Escape hatch: send any console command, get back its raw
        response lines (list of str), OK/ERR-prefix included on line 0."""
        return self._console.command(cmd)

    def _run(self, cmd):
        lines = self._console.command(cmd)
        if not lines:
            raise SPUProtocolError("empty response to %r" % cmd)
        result, kv, hex_tokens = _tokenize(lines)
        if result == "ERR":
            raise SPUProtocolError("%s -> %s" % (cmd, " ".join(lines)))
        if result != "OK":
            raise SPUProtocolError(
                "%s -> unrecognized response %r" % (cmd, lines)
            )
        return kv, hex_tokens

    # ── 0xAC status ──────────────────────────────────────────────────
    def status(self):
        kv, hex_tokens = self._run("status")
        raw = _bytes_field(kv, hex_tokens, "raw")
        return {
            "raw": raw,
            "lfi": _int_auto(kv["lfi"]),
            "flags": _int_auto(kv["flags"]),
            "mode": _int_auto(kv["mode"]),
            "fifo_full": kv["fifo_full"] == "1",
            "ratio_valid": kv["ratio_valid"] == "1",
            "ratio": int(kv["ratio"]),
        }

    # ── 0xA0 manifold ────────────────────────────────────────────────
    def manifold(self):
        _kv, hex_tokens = self._run("manifold")
        return bytes.fromhex("".join(hex_tokens))

    # ── 0xAD scale table ─────────────────────────────────────────────
    def scale_table(self):
        _kv, hex_tokens = self._run("scale")
        return bytes.fromhex("".join(hex_tokens))

    # ── 0xAE QR commit ───────────────────────────────────────────────
    def qr_commit(self):
        kv, _hex_tokens = self._run("qr")
        return {
            "valid": kv["valid"] == "1",
            "lane": int(kv["lane"]),
            "A": _int_auto(kv["A"]),
            "B": _int_auto(kv["B"]),
            "C": _int_auto(kv["C"]),
            "D": _int_auto(kv["D"]),
        }

    # ── 0xAF HEX projection ──────────────────────────────────────────
    def hex_projection(self):
        kv, hex_tokens = self._run("hex")
        raw = _bytes_field(kv, hex_tokens, "raw")
        return {
            "valid": kv["valid"] == "1",
            "q": int(kv["q"]),
            "r": int(kv["r"]),
            "raw": raw,
        }

    # ── 0xB0 RPLU config-write telemetry (see module docstring re: the
    #    "sentinel telemetry" naming discrepancy in the protocol doc) ──
    def rplu_config_telemetry(self):
        kv, hex_tokens = self._run("cfgtele")
        if "raw" in kv or hex_tokens:
            return {"magic_ok": False, "raw": _bytes_field(kv, hex_tokens, "raw")}
        out = {
            "magic_ok": True,
            "count": int(kv["count"]),
            "last_sel": int(kv["last_sel"]),
            "last_material": int(kv["last_material"]),
            "last_addr": int(kv["last_addr"]),
            "last_data": _int_auto(kv["last_data"]),
            "checksum": _int_auto(kv["checksum"]),
        }
        if "rplu2_sum" in kv:
            out.update(
                rplu2_sum=_int_auto(kv["rplu2_sum"]),
                rplu2_status=_int_auto(kv["rplu2_status"]),
                rplu2_num0=_int_auto(kv["rplu2_num0"]),
                rplu2_delta=_int_auto(kv["rplu2_delta"]),
                rplu2_row1=_int_auto(kv["rplu2_row1"]),
                rplu2_kappa=_int_auto(kv["rplu2_kappa"]),
            )
        return out

    # ── 0xB1 chord (instruction) write ──────────────────────────────
    def write_chord(self, data):
        """data: 8-byte instruction, as bytes/bytearray or a 64-bit int."""
        if isinstance(data, int):
            data = data.to_bytes(8, "big")
        if len(data) != 8:
            raise ValueError("chord must be exactly 8 bytes")
        kv, hex_tokens = self._run("chord " + data.hex())
        return bytes.fromhex("".join(hex_tokens)) if hex_tokens else kv

    # ── 0xB2/0xB3 transactional TGR1 sidecar ───────────────────────
    def load_tensegrity_sd(self, path, vector_id=0):
        """Load a .tgr file already present on the RP2350 SD filesystem."""
        kv, _hex_tokens = self._run("tgrload %s %d" % (path, vector_id))
        return {"bytes": int(kv["bytes"]), "vector": int(kv["vector"])}

    def tensegrity_status(self):
        kv, _hex_tokens = self._run("tgrstatus")
        return {
            "version": int(kv["version"]),
            "state": int(kv["state"]),
            "fault": int(kv["fault"]),
            "stage": int(kv.get("stage", "0")),
            "vector": int(kv["vector"]),
            "flags": _int_auto(kv["flags"]),
            "error": int(kv["error"]),
            "nodes": int(kv["nodes"]),
            "edges": int(kv["edges"]),
            "received": int(kv["received"]),
            "expected": int(kv["expected"]),
        }

    # ── SOM1 versioned decision evidence ────────────────────────────
    def som1_result(self):
        kv, hex_tokens = self._run("som1")
        return parse_som1_frame(_bytes_field(kv, hex_tokens, "raw"))

    # ── 0xA5 RPLU config write ──────────────────────────────────────
    def write_rplu_cfg(self, sel, material, addr, data):
        """sel: 0-7, material: 0-15, addr: 0-1023, data: 64-bit int."""
        kv, _hex_tokens = self._run(
            "rplu %d %d %d 0x%016X" % (sel, material, addr, data & 0xFFFFFFFFFFFFFFFF)
        )
        return {
            "header": _int_auto(kv["header"]),
            "data": _int_auto(kv["data"]),
        }
