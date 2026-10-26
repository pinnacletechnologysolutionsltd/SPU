#!/usr/bin/env python3
"""tensegrity_demo.py — first-hour demo for the TENSEGRITYLINK spin (Wukong).

Transactional structural validation in silicon, in four acts:

1. Admit: load the canonical balanced tensegrity structure (12 nodes /
   30 edges, exact Z[phi] coordinates). The guard replays every check --
   topology, strut contact, cable slack, grid consistency, force-density
   equilibrium -- and commits a BALANCED verdict.
2. Reject-and-commit: load a structure whose members provably cannot be
   in force equilibrium. The guard catches it and commits the fault
   verdict -- the same verdict, for the same exact-arithmetic reason, as
   the software oracle running on your host.
3. Rollback: load a table whose payload CRC-32 is corrupt. The loader
   reports the error diagnostically, but the active verdict/vector is
   untouched -- a bad upload cannot corrupt the committed state. This is
   the transactional guarantee, observed on the wire.
4. Recover: reload the balanced structure; the active verdict returns
   to BALANCED.

Every expected value is computed live by the Python oracle
(software/lib/tensegrity_vectors.py), not hardcoded -- the demo is a
host-vs-silicon equivalence check, not a scripted light show.

Silicon status (docs/TENSEGRITY_BALANCER_HANDOVER_2026-07-15.md): the full
combined path -- SD, RP2350, B2/B3 transport, parser, intersection,
equilibrium, rollback, and recovery -- is board-proven as of 2026-07-19.  Use
the parser/service `stage` and bounded watchdog errors to localize a stall if
testing a different build.

Setup (one-time): the fixtures must be on the RP2350's SD card.
    python3 tools/tensegrity_demo.py --emit-fixtures /path/to/sd/TGR
then move the card to the RP2350 and run:
    python3 tools/tensegrity_demo.py --port /dev/ttyACM0 [--sd-dir /TGR]

Board: `bash hardware/boards/artix7/build_a7.sh 100t tensegritylink
synth/pnr/pack`, SRAM-load via DirtyJTAG. Mind AGENTS.md's J11 notes
(bottom-row remap, 100R series resistors, never power the RP2350 against
an unpowered Wukong).
"""

import argparse
import os
import sys
import time
import types

try:
    import serial
except ImportError:
    # Deferred, same pattern/lesson as robotics_demo.py: the fixture and
    # oracle logic must stay importable without pyserial installed.
    serial = types.ModuleType("serial")
    serial.Serial = None

REPO_ROOT = __file__.rsplit("/tools/", 1)[0]
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "software"))

from software.spu_host import SPUHostClient, SPUProtocolError  # noqa: E402
from lib.tensegrity_abi import encode_table  # noqa: E402
from lib.tensegrity_vectors import golden_vectors, run_oracle  # noqa: E402

# B3 flags byte (docs/SOUTHBRIDGE_SPI_PROTOCOL.md, 0xB3 section)
FLAG_ACTIVE_VALID = 0x08
FLAG_VERIFY_BUSY = 0x04

# Loader diagnostics used by this demo (same section)
LOADER_ERR_PAYLOAD_CRC = 7
LOADER_ERR_GUARD_TIMEOUT = 10
LOADER_ERR_PARSE_TIMEOUT = 11

CORRUPT_NAME = "99_corrupt_crc.tgr"
CORRUPT_VECTOR_ID = 99

VERIFY_POLL_S = 0.05
VERIFY_TIMEOUT_S = 3.0


def fixture_name(vector):
    return f"{vector.vector_id:02d}_{vector.name}.tgr"


def make_corrupt_table():
    """Canonical balanced table with its final payload byte flipped, so the
    header CRC-32 no longer matches: transport-accepts, sidecar-rejects."""
    table = bytearray(encode_table(golden_vectors()[0].system))
    table[-1] ^= 0xFF
    return bytes(table)


def emit_fixtures(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for vector in golden_vectors():
        blob = encode_table(vector.system)
        path = os.path.join(out_dir, fixture_name(vector))
        with open(path, "wb") as fh:
            fh.write(blob)
        print(f"  wrote {path} ({len(blob)} bytes)")
    corrupt = make_corrupt_table()
    path = os.path.join(out_dir, CORRUPT_NAME)
    with open(path, "wb") as fh:
        fh.write(corrupt)
    print(f"  wrote {path} ({len(corrupt)} bytes, payload CRC deliberately broken)")
    print("Copy this directory onto the RP2350's SD card, then rerun with --port.")


def wait_verdict(client):
    """Poll B3 until verify-busy clears; returns the settled status dict."""
    deadline = time.monotonic() + VERIFY_TIMEOUT_S
    while True:
        status = client.tensegrity_status()
        if not (status["flags"] & FLAG_VERIFY_BUSY):
            return status
        if time.monotonic() > deadline:
            return status  # caller sees verify-busy still set and reports it


def check_verdict(label, status, expect_state, expect_fault, expect_vector,
                  expect_error=0, expect_nodes=None, expect_edges=None):
    if status["flags"] & FLAG_VERIFY_BUSY:
        print(f"  {label}: STALLED verify-busy at stage="
              f"0x{status.get('stage', 0):02x}; the active verdict is unchanged.")
        return False
    if status["error"] == LOADER_ERR_GUARD_TIMEOUT:
        stage = status.get("stage", 0)
        print(f"  {label}: VERIFIER WATCHDOG -- service-stage={stage & 0x7f} "
              f"timed out; the previous committed verdict was preserved.")
        return False
    if status["error"] == LOADER_ERR_PARSE_TIMEOUT:
        stage = status.get("stage", 0)
        print(f"  {label}: PARSER WATCHDOG -- parser-substate={stage & 0x0f} "
              f"timed out; the previous committed verdict was preserved.")
        return False
    problems = []
    if status["state"] != expect_state.value:
        problems.append(f"state={status['state']} want {expect_state.value} ({expect_state.name})")
    if status["fault"] != expect_fault.value:
        problems.append(f"fault={status['fault']} want {expect_fault.value} ({expect_fault.name})")
    if status["vector"] != expect_vector:
        problems.append(f"vector={status['vector']} want {expect_vector}")
    if status["error"] != expect_error:
        problems.append(f"loader-error={status['error']} want {expect_error}")
    if expect_nodes is not None and status["nodes"] != expect_nodes:
        problems.append(f"nodes={status['nodes']} want {expect_nodes}")
    if expect_edges is not None and status["edges"] != expect_edges:
        problems.append(f"edges={status['edges']} want {expect_edges}")
    if problems:
        print(f"  {label}: MISMATCH -- " + "; ".join(problems))
        return False
    print(f"  {label}: {expect_state.name}/{expect_fault.name}"
          f" vector={expect_vector} error={expect_error}   [ok]")
    return True


def run_demo(client, sd_dir):
    vectors = golden_vectors()
    balanced = vectors[0]
    faulted = vectors[6]  # fault_not_in_equilibrium

    bal_state, bal_fault = run_oracle(balanced.system)
    flt_state, flt_fault = run_oracle(faulted.system)
    ok = True

    print("Act 1: admit the canonical balanced structure")
    client.load_tensegrity_sd(f"{sd_dir}/{fixture_name(balanced)}", balanced.vector_id)
    status = wait_verdict(client)
    ok &= check_verdict("balanced commit", status, bal_state, bal_fault,
                        balanced.vector_id,
                        expect_nodes=len(balanced.system.nodes),
                        expect_edges=len(balanced.system.edges))

    print("Act 2: the guard rejects a structure that cannot be in equilibrium")
    client.load_tensegrity_sd(f"{sd_dir}/{fixture_name(faulted)}", faulted.vector_id)
    status = wait_verdict(client)
    ok &= check_verdict("fault verdict commit", status, flt_state, flt_fault,
                        faulted.vector_id)
    print("     (same verdict as the exact-arithmetic oracle on this host --")
    print("      an audit-defensible 'why': the force rows provably cannot")
    print("      share a density ratio, checked by exact cross-multiplication)")

    print("Act 3: a corrupt upload cannot touch the committed state")
    client.load_tensegrity_sd(f"{sd_dir}/{CORRUPT_NAME}", CORRUPT_VECTOR_ID)
    status = wait_verdict(client)
    # bytes 1-7 must still report Act 2's committed verdict; only the loader
    # diagnostic changes. This is the transactional rollback on the wire.
    ok &= check_verdict("rollback", status, flt_state, flt_fault,
                        faulted.vector_id, expect_error=LOADER_ERR_PAYLOAD_CRC)

    print("Act 4: recover -- reload the balanced structure")
    client.load_tensegrity_sd(f"{sd_dir}/{fixture_name(balanced)}", balanced.vector_id)
    status = wait_verdict(client)
    ok &= check_verdict("recovery", status, bal_state, bal_fault,
                        balanced.vector_id)
    return ok


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", help="e.g. /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--sd-dir", default="/TGR",
                        help="fixture directory on the RP2350 SD card (default /TGR)")
    parser.add_argument("--emit-fixtures", metavar="DIR",
                        help="write the .tgr fixture set to DIR and exit (no hardware)")
    ns = parser.parse_args(argv)

    if ns.emit_fixtures:
        emit_fixtures(ns.emit_fixtures)
        return 0
    if not ns.port:
        parser.error("--port is required unless --emit-fixtures is given")
    if serial.Serial is None:
        print("ERROR: pyserial is not installed (pip install pyserial).", file=sys.stderr)
        return 1

    ser = serial.Serial(ns.port, ns.baud, timeout=0.05)
    client = SPUHostClient(ser)
    try:
        # A long-running RP2350 prints its banner only once. On a repeated
        # host invocation there may be no unread prompt to drain, so provoke
        # one without disturbing any FPGA or SD state.
        if not ser.in_waiting:
            ser.write(b"\n")
        client.connect()
        print("TENSEGRITYLINK demo -- transactional structural validation in silicon")
        print("=" * 72)
        ok = run_demo(client, ns.sd_dir.rstrip("/"))
        print("=" * 72)
        if ok:
            print("PASS: silicon verdicts matched the exact oracle on every act,")
            print("      and the corrupt upload provably could not corrupt state.")
            return 0
        print("FAIL: see mismatches above.")
        return 1
    except SPUProtocolError as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
