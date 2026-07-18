#!/usr/bin/env python3
"""test_tensegrity_demo.py — hardware-free regression for tools/tensegrity_demo.py.

Checks, without a board attached:
1. Fixture emission: all seven golden .tgr tables byte-identical to
   encode_table() output under the NN_name.tgr convention, plus a corrupt
   fixture that differs from the balanced table in exactly one byte and
   genuinely fails the header CRC-32.
2. The full four-act demo flow against a fake serial port emulating the
   sidecar's real commit/rollback semantics (docs/SOUTHBRIDGE_SPI_PROTOCOL.md,
   0xB3 section): well-formed tables commit their guard verdict (computed by
   the same Python oracle the demo checks against); CRC-corrupt tables set
   loader error 7 while bytes 1-7 keep reporting the last committed verdict.
3. Sabotage paths, each of which must fail the demo:
   - a sidecar that reports BALANCED for the not-in-equilibrium fixture
     (the exact false-negative class the V:6 51.89 MHz silicon bug showed);
   - a sidecar that fails to roll back on a corrupt upload (clobbers the
     active verdict instead of preserving it);
   - a sidecar stuck verify-busy (the known combined-image issue -- the
     demo must report it and exit nonzero, not hang or false-pass).
   - stage-coded guard and parser watchdog rollbacks.

No hardware required. Run: python3 software/tests/test_tensegrity_demo.py
"""

import os
import shutil
import sys
import tempfile
import zlib

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
sys.path.insert(0, os.path.join(REPO_ROOT, "software"))

import tensegrity_demo as td  # noqa: E402
from lib.tensegrity_abi import HEADER, decode_table, encode_table  # noqa: E402
from lib.tensegrity_vectors import golden_vectors, run_oracle  # noqa: E402

BANNER = b"\r\nSPU RP diagnostic console ready\r\nType 'help' for commands.\r\n> "

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── Part 1: fixture emission ───────────────────────────────────────────────

tmpdir = tempfile.mkdtemp(prefix="tgr_demo_test_")
try:
    td.emit_fixtures(tmpdir)
    vectors = golden_vectors()
    check("emits 7 golden + 1 corrupt fixture",
          len(os.listdir(tmpdir)) == len(vectors) + 1)
    for vector in vectors:
        path = os.path.join(tmpdir, td.fixture_name(vector))
        blob = open(path, "rb").read()
        check(f"{td.fixture_name(vector)} byte-identical to encode_table",
              blob == encode_table(vector.system))

    balanced = open(os.path.join(tmpdir, td.fixture_name(vectors[0])), "rb").read()
    corrupt = open(os.path.join(tmpdir, td.CORRUPT_NAME), "rb").read()
    check("corrupt fixture same length as balanced", len(corrupt) == len(balanced))
    check("corrupt fixture differs in exactly one byte",
          sum(a != b for a, b in zip(corrupt, balanced)) == 1)
    crc_claim = HEADER.unpack(corrupt[:HEADER.size])[5]
    check("corrupt fixture genuinely fails its header CRC-32",
          (zlib.crc32(corrupt[HEADER.size:]) & 0xFFFFFFFF) != crc_claim)
    fixtures = {name: open(os.path.join(tmpdir, name), "rb").read()
                for name in os.listdir(tmpdir)}
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)


# ── Part 2: fake console + sidecar with real commit/rollback semantics ────

class FakeTgrSerial:
    """Emulates spu_diag.c's tgrload/tgrstatus over a fake SD directory,
    with the sidecar semantics from the protocol doc's 0xB3 section."""

    def __init__(self, sd_files, lie_balanced_on=None, no_rollback=False,
                 stuck_busy=False, watchdog_timeout=False,
                 parser_timeout=False):
        self._out = bytearray(BANNER)
        self._sd = sd_files  # {basename: bytes}
        self._lie_on = lie_balanced_on      # fixture name -> report BALANCED
        self._no_rollback = no_rollback     # corrupt upload clobbers verdict
        self._stuck_busy = stuck_busy
        self._watchdog_timeout = watchdog_timeout
        self._parser_timeout = parser_timeout
        # Active (committed) status: state, fault, vector, nodes, edges
        self._active = dict(state=0, fault=0, vector=0, nodes=0, edges=0)
        self._error = 0

    @property
    def in_waiting(self):
        return len(self._out)

    def read(self, n):
        chunk = bytes(self._out[:n])
        del self._out[:n]
        return chunk

    def _tgrload(self, path, vector_id):
        name = path.rsplit("/", 1)[-1]
        blob = self._sd.get(name)
        if blob is None:
            return ["ERR TGR1 file not found"]
        crc_claim = HEADER.unpack(blob[:HEADER.size])[5]
        crc_real = zlib.crc32(blob[HEADER.size:]) & 0xFFFFFFFF
        if crc_real != crc_claim:
            self._error = td.LOADER_ERR_PAYLOAD_CRC
            if self._no_rollback:  # sabotage: clobber committed state anyway
                self._active = dict(state=0, fault=0, vector=vector_id,
                                    nodes=0, edges=0)
        elif self._watchdog_timeout:
            # Bounded combined-service failure: active state is untouched.
            self._error = td.LOADER_ERR_GUARD_TIMEOUT
        elif self._parser_timeout:
            # Bounded BRAM replay failure: active state is untouched.
            self._error = td.LOADER_ERR_PARSE_TIMEOUT
        else:
            system = decode_table(blob)
            state, fault = run_oracle(system)
            if self._lie_on and name == self._lie_on:
                state, fault = run_oracle(golden_vectors()[0].system)  # BALANCED lie
            self._active = dict(state=state.value, fault=fault.value,
                                vector=vector_id, nodes=len(system.nodes),
                                edges=len(system.edges))
            self._error = 0
        return ["OK tgrload bytes=%d vector=%d" % (len(blob), vector_id)]

    def _tgrstatus(self):
        flags = td.FLAG_ACTIVE_VALID
        if self._stuck_busy:
            flags |= td.FLAG_VERIFY_BUSY
        if self._error:
            flags |= 0x01
        a = self._active
        stage = (0x80 | 5) if self._watchdog_timeout else (
            (0x90 | 3) if self._parser_timeout else (
                5 if self._stuck_busy else 8))
        return ["OK tgrstatus version=1 state=%d fault=%d stage=%d vector=%d"
                " flags=0x%02X error=%d nodes=%d edges=%d"
                " received=0 expected=0"
                % (a["state"], a["fault"], stage,
                   a["vector"], flags,
                   self._error, a["nodes"], a["edges"])]

    def write(self, data):
        cmd = data.decode("ascii").rstrip("\r\n")
        echo = data.replace(b"\n", b"\r\n")
        parts = cmd.split()
        if parts and parts[0] == "tgrload":
            lines = self._tgrload(parts[1], int(parts[2]))
        elif cmd == "tgrstatus":
            lines = self._tgrstatus()
        else:
            lines = ["ERR unknown command: " + cmd]
        self._out += echo + ("\r\n".join(lines) + "\r\n").encode("ascii") + b"> "

    def close(self):
        pass


def run_demo(**fake_kwargs):
    ser = FakeTgrSerial(fixtures, **fake_kwargs)
    td.VERIFY_TIMEOUT_S = 0.2  # don't sit in the stuck-busy poll for 3s
    real_ctor = td.serial.Serial
    td.serial.Serial = lambda *a, **k: ser
    try:
        return td.main(["--port", "/dev/fake"])
    finally:
        td.serial.Serial = real_ctor


check("faithful sidecar: full four-act demo exits 0", run_demo() == 0)

lie_target = td.fixture_name(golden_vectors()[6])
check("sidecar lying BALANCED about the equilibrium fault exits 1 "
      "(the V:6 false-negative class)",
      run_demo(lie_balanced_on=lie_target) == 1)

check("sidecar that fails to roll back on corrupt upload exits 1",
      run_demo(no_rollback=True) == 1)

check("sidecar stuck verify-busy exits 1 (known combined-image issue)",
      run_demo(stuck_busy=True) == 1)

check("stage-coded verifier watchdog exits 1 without indefinite polling",
      run_demo(watchdog_timeout=True) == 1)

check("stage-coded parser watchdog exits 1 and preserves active state",
      run_demo(parser_timeout=True) == 1)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
