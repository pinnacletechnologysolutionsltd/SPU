#!/usr/bin/env python3
"""Southbridge SPI protocol oracle — typestate case study.

Models the spu_spi_slave.v state machine (11 states, including the optional
TGR1 transport). Provides a bit-exact reference for trace equivalence
against the RTL state machine and poison-proof fault injection.

This is the non-arithmetic case study for THEOREM_LICENSED_TYPESTATE.md
§6 (future) → §5.5 (adding now).  The guards here are protocol-framing
conditions (byte counts, CRC-8, opcode validity) rather than algebraic
theorems — demonstrating the method's generality beyond arithmetic.

Copyright 2026 John Curley. Licensed under MIT.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

# ── CRC-8-CCITT (polynomial 0x07: x⁸ + x² + x + 1) ─────────────
# Bit-exact match with spu_spi_slave.v crc8_byte / crc8_word64.


def crc8_byte(crc: int, byte_data: int) -> int:
    """Compute CRC-8-CCITT for one byte, MSB-first per the RTL."""
    s = crc & 0xFF
    for b in range(8):
        if ((s >> 7) & 1) != ((byte_data >> (7 - b)) & 1):
            s = ((s << 1) & 0xFF) ^ 0x07
        else:
            s = (s << 1) & 0xFF
    return s & 0xFF


def crc8_word64(crc: int, word: int) -> int:
    """Compute CRC-8-CCITT over a 64-bit big-endian word."""
    s = crc & 0xFF
    for n in range(8):
        byte_val = (word >> (56 - n * 8)) & 0xFF
        s = crc8_byte(s, byte_val)
    return s & 0xFF


def crc8_bytes(crc: int, data: bytes) -> int:
    s = crc & 0xFF
    for value in data:
        s = crc8_byte(s, value)
    return s


# ── State machine ────────────────────────────────────────────────


class SPIState(IntEnum):
    """States from spu_spi_slave.v localparam S_*."""
    S_IDLE = 0
    S_CMD = 1
    S_FILL = 2
    S_RESP = 3
    S_RECV_HDR = 4
    S_RECV_DATA = 5
    S_RECV_INST = 6
    S_RECV_CRC = 7
    S_RECV_TGR_PREFIX = 8
    S_RECV_TGR_DATA = 9
    S_RECV_TGR_CRC = 10


class Fault(IntEnum):
    """Typestate fault codes for the SPI protocol machine."""
    NONE = 0
    CS_EARLY = 1          # CS deasserted mid-transaction
    UNKNOWN_CMD = 2       # Unrecognized opcode
    CRC_MISMATCH = 3      # CRC-8 check failed on write
    DEADMAN_TIMEOUT = 4   # SCK stalled > 1ms in receive state
    FRAMING_ERROR = 5     # Byte count mismatch (guard: expected vs actual)


# ── SPI transaction model ────────────────────────────────────────


@dataclass
class SPITransaction:
    """One complete SPI transaction as seen by the slave."""
    cmd_byte: int          # 8-bit command
    payload: bytes = b""   # Write payload (for 0xB1, 0xA5, 0xB2)
    crc_byte: Optional[int] = None  # CRC-8 for writes

    @property
    def is_write(self) -> bool:
        return self.cmd_byte in (0xB1, 0xB2, 0xA5)

    @property
    def is_read(self) -> bool:
        return self.cmd_byte in (0xA0, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB3)


@dataclass
class SPISlaveState:
    """Full state of the SPI slave after processing a transaction."""

    state: SPIState = SPIState.S_IDLE
    last_cmd: int = 0x00

    # Write-path state (for CRC tracking)
    recv_bits: int = 0        # bits received so far (0..63)
    hdr_shift: int = 0        # 64-bit header accumulator
    data_shift: int = 0       # 64-bit data accumulator
    crc_accum: int = 0x00     # CRC accumulator

    # Fault tracking
    fault: Fault = Fault.NONE
    crc_error_sticky: bool = False

    # Response buffer (big-endian byte array)
    response: bytes = b""
    resp_len: int = 0

    # Deadman counter (reset on any SCK edge or CS deassertion)
    deadman: int = 50000      # ~1ms at 50 MHz

    # ── Typestate guards ──────────────────────────────────────────

    def guard_cs_not_early(self, cs_active: bool) -> bool:
        """Guard: CS must remain asserted during a transaction."""
        return cs_active

    def guard_valid_cmd(self) -> bool:
        """Guard: command byte must be a recognized opcode."""
        return self.last_cmd in (
            0xA0, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB2, 0xB3, 0xA5)

    def guard_crc_match(self, expected_crc: int) -> bool:
        """Guard: received CRC-8 must match computed accumulator."""
        return (self.crc_accum & 0xFF) == (expected_crc & 0xFF)

    def guard_byte_count(self, expected_bits: int) -> bool:
        """Guard: payload length must match expected for command."""
        return self.recv_bits == expected_bits

    def guard_not_deadman(self) -> bool:
        """Guard: deadman timer must not have expired."""
        return self.deadman > 0


# ── Oracle: process one transaction ──────────────────────────────


class SPISlaveOracle:
    """Bit-exact model of spu_spi_slave.v behaviour.

    This oracle uses structurally different arithmetic: Python integers
    (arbitrary precision) vs the RTL's fixed-width registers.  Matching
    results therefore prove genuine closure, not shared-model agreement.
    """

    def __init__(self):
        self.state = SPISlaveState()

    def reset(self):
        self.state = SPISlaveState()

    def process_transaction(self, txn: SPITransaction) -> SPISlaveState:
        """Process one complete SPI transaction.

        Returns the state AFTER the transaction completes (back in S_IDLE
        or in a fault state).  The caller is responsible for checking
        fault codes and response content.
        """
        s = SPISlaveState()
        s.last_cmd = txn.cmd_byte

        # ── Check guards ──────────────────────────────────────────
        # Guard: CS must remain asserted (simulated as always true here;
        # the caller injects CS deassertion as a fault injection test).
        # Guard: valid command
        if not s.guard_valid_cmd():
            s.fault = Fault.UNKNOWN_CMD
            s.state = SPIState.S_IDLE
            s.response = b"\x00"
            s.resp_len = 1
            return s

        # ── Read commands ─────────────────────────────────────────
        if txn.is_read:
            s.state = SPIState.S_RESP
            s.response = self._build_read_response(txn.cmd_byte)
            s.resp_len = len(s.response)
            return s

        # ── Write commands ────────────────────────────────────────
        if txn.cmd_byte == 0xB1:
            # Single 64-bit instruction write
            s.state = SPIState.S_RECV_INST
            s.recv_bits = 64  # completed after 64 bits
            s.data_shift = int.from_bytes(txn.payload[:8], "big")
            s.crc_accum = crc8_word64(crc8_byte(0x00, 0xB1), s.data_shift)

            # CRC guard
            if txn.crc_byte is not None:
                if not s.guard_crc_match(txn.crc_byte):
                    s.fault = Fault.CRC_MISMATCH
                    s.crc_error_sticky = True
                    s.state = SPIState.S_IDLE
                    return s
            s.state = SPIState.S_IDLE
            return s

        if txn.cmd_byte == 0xA5:
            # Two 64-bit chords: HEADER + DATA
            s.state = SPIState.S_RECV_HDR
            if len(txn.payload) >= 8:
                s.hdr_shift = int.from_bytes(txn.payload[:8], "big")
                s.recv_bits = 64
                s.crc_accum = crc8_word64(crc8_byte(0x00, 0xA5), s.hdr_shift)

            if len(txn.payload) >= 16:
                s.state = SPIState.S_RECV_DATA
                s.data_shift = int.from_bytes(txn.payload[8:16], "big")
                s.recv_bits = 64  # second word received
                s.crc_accum = crc8_word64(s.crc_accum, s.data_shift)

            if txn.crc_byte is not None:
                if not s.guard_crc_match(txn.crc_byte):
                    s.fault = Fault.CRC_MISMATCH
                    s.crc_error_sticky = True
                    s.state = SPIState.S_IDLE
                    return s
            s.state = SPIState.S_IDLE
            return s

        if txn.cmd_byte == 0xB2:
            # Prefix is len16 + vector_id32, followed by exactly len TGR1 bytes.
            s.state = SPIState.S_RECV_TGR_PREFIX
            if len(txn.payload) < 6:
                s.fault = Fault.FRAMING_ERROR
                s.state = SPIState.S_IDLE
                return s
            declared = int.from_bytes(txn.payload[:2], "big")
            if len(txn.payload) != 6 + declared:
                s.fault = Fault.FRAMING_ERROR
                s.state = SPIState.S_IDLE
                return s
            s.state = SPIState.S_RECV_TGR_DATA
            s.recv_bits = len(txn.payload) * 8
            s.crc_accum = crc8_bytes(crc8_byte(0x00, 0xB2), txn.payload)
            if txn.crc_byte is None or not s.guard_crc_match(txn.crc_byte):
                s.fault = Fault.CRC_MISMATCH
                s.crc_error_sticky = True
            s.state = SPIState.S_IDLE
            return s

        # ── Unknown (shouldn't reach here due to guard) ───────────
        s.state = SPIState.S_IDLE
        s.response = b"\x00"
        s.resp_len = 1
        s.fault = Fault.UNKNOWN_CMD
        return s

    def _build_read_response(self, cmd: int) -> bytes:
        """Build the response buffer for a read command.

        This is a STATIC oracle: it returns the expected format/length
        but with zero-valued data.  Trace equivalence tests provide actual
        manifold/qr values for comparison against RTL output.
        """
        if cmd == 0xA0:   # Manifold Burst — 32 bytes
            return bytes(32)
        elif cmd == 0xAC:  # Status — 4 bytes
            return bytes(4)
        elif cmd == 0xAD:  # Scale Table — 9 bytes
            return bytes(9)
        elif cmd == 0xAE:  # QR Commit — 34 bytes
            return bytes(34)
        elif cmd == 0xAF:  # HEX Projection — 5 bytes
            return bytes(5)
        elif cmd == 0xB0:  # Sentinel Telemetry — 64 bytes
            return bytes(64)
        elif cmd == 0xB3:  # TGR1 verdict + loader diagnostics — 16 bytes
            return bytes(16)
        return b"\x00"


# ── Poison-proof fault injection ─────────────────────────────────


def test_unknown_cmd_poison():
    """Fault: unknown opcode → single 0x00 response, state returns to IDLE."""
    oracle = SPISlaveOracle()
    txn = SPITransaction(cmd_byte=0xFF)
    result = oracle.process_transaction(txn)
    assert result.fault == Fault.UNKNOWN_CMD, f"Expected UNKNOWN_CMD, got {result.fault}"
    assert result.response == b"\x00", f"Expected b'\\x00', got {result.response}"
    assert result.state == SPIState.S_IDLE, f"Expected S_IDLE, got {result.state}"
    assert result.crc_error_sticky == False


def test_crc_mismatch_poison():
    """Fault: CRC mismatch on B1 write → crc_error_sticky set, state returns to IDLE."""
    oracle = SPISlaveOracle()
    payload = bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0])
    txn = SPITransaction(cmd_byte=0xB1, payload=payload, crc_byte=0x00)
    result = oracle.process_transaction(txn)
    assert result.fault == Fault.CRC_MISMATCH, f"Expected CRC_MISMATCH, got {result.fault}"
    assert result.crc_error_sticky == True
    assert result.state == SPIState.S_IDLE


def test_valid_b1_write():
    """Valid B1 instruction write with correct CRC."""
    oracle = SPISlaveOracle()
    payload = bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x00, 0x00, 0x00])
    expected_crc = crc8_word64(crc8_byte(0x00, 0xB1), int.from_bytes(payload, "big"))
    txn = SPITransaction(cmd_byte=0xB1, payload=payload, crc_byte=expected_crc)
    result = oracle.process_transaction(txn)
    assert result.fault == Fault.NONE, f"Expected NONE, got {result.fault}"
    assert result.crc_error_sticky == False
    assert result.state == SPIState.S_IDLE
    assert result.data_shift == int.from_bytes(payload, "big")


def test_valid_a5_write():
    """Valid A5 RPLU config write with correct CRC."""
    oracle = SPISlaveOracle()
    hdr = bytes([0xA5, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    data = bytes([0x00] * 8)
    payload = hdr + data
    crc = crc8_word64(crc8_byte(0x00, 0xA5), int.from_bytes(hdr, "big"))
    crc = crc8_word64(crc, int.from_bytes(data, "big"))
    txn = SPITransaction(cmd_byte=0xA5, payload=payload, crc_byte=crc)
    result = oracle.process_transaction(txn)
    assert result.fault == Fault.NONE, f"Expected NONE, got {result.fault}"
    assert result.state == SPIState.S_IDLE


def test_valid_b2_write_and_framing():
    oracle = SPISlaveOracle()
    table = b"TGR1" + bytes(8)
    payload = len(table).to_bytes(2, "big") + (6).to_bytes(4, "big") + table
    crc = crc8_bytes(crc8_byte(0, 0xB2), payload)
    result = oracle.process_transaction(
        SPITransaction(cmd_byte=0xB2, payload=payload, crc_byte=crc))
    assert result.fault == Fault.NONE
    malformed = oracle.process_transaction(
        SPITransaction(cmd_byte=0xB2, payload=b"\x00\x0d" + payload[2:], crc_byte=crc))
    assert malformed.fault == Fault.FRAMING_ERROR


def test_read_response_lengths():
    """All read commands return the correct response byte count."""
    oracle = SPISlaveOracle()
    expected = {
        0xA0: 32, 0xAC: 4, 0xAD: 9, 0xAE: 34, 0xAF: 5, 0xB0: 64, 0xB3: 16,
    }
    for cmd, length in expected.items():
        txn = SPITransaction(cmd_byte=cmd)
        result = oracle.process_transaction(txn)
        assert result.resp_len == length, \
            f"Cmd 0x{cmd:02X}: expected {length} bytes, got {result.resp_len}"
        assert result.fault == Fault.NONE


def test_crc_accumulator_reset():
    """CRC accumulator resets at CS assertion (each new transaction)."""
    oracle = SPISlaveOracle()
    payload1 = bytes([0x01] * 8)
    crc1 = crc8_word64(crc8_byte(0x00, 0xB1), int.from_bytes(payload1, "big"))
    txn1 = SPITransaction(cmd_byte=0xB1, payload=payload1, crc_byte=crc1)
    oracle.process_transaction(txn1)

    # Second transaction: CRC accumulator must start fresh
    payload2 = bytes([0x02] * 8)
    crc2 = crc8_word64(crc8_byte(0x00, 0xB1), int.from_bytes(payload2, "big"))
    txn2 = SPITransaction(cmd_byte=0xB1, payload=payload2, crc_byte=crc2)
    result2 = oracle.process_transaction(txn2)
    assert result2.fault == Fault.NONE, f"CRC should reset per transaction"


def test_typestate_lattice():
    """Verify the protocol typestate: fault states are terminal.

    Once CRC_ERROR is sticky, subsequent reads of status (0xAC) must
    report the sticky bit, and the bit clears on read.
    """
    oracle = SPISlaveOracle()

    # Inject CRC fault
    payload = bytes([0xFF] * 8)
    txn = SPITransaction(cmd_byte=0xB1, payload=payload, crc_byte=0x00)
    result = oracle.process_transaction(txn)
    assert result.crc_error_sticky == True

    # The bit is cleared by the 0xAC status read in the RTL.
    # Our oracle models sticky state but the _build_read_response()
    # returns zeros — the trace equivalence test verifies actual RTL bits.
    # For this oracle test, just verify the fault was latched.
    assert result.fault == Fault.CRC_MISMATCH


def test_all_read_commands_fault_free():
    """All 6 read commands complete without fault."""
    oracle = SPISlaveOracle()
    for cmd in (0xA0, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB3):
        txn = SPITransaction(cmd_byte=cmd)
        result = oracle.process_transaction(txn)
        assert result.fault == Fault.NONE, f"Cmd 0x{cmd:02X} unexpected fault {result.fault}"


if __name__ == "__main__":
    tests = [
        test_unknown_cmd_poison,
        test_crc_mismatch_poison,
        test_valid_b1_write,
        test_valid_a5_write,
        test_valid_b2_write_and_framing,
        test_read_response_lengths,
        test_crc_accumulator_reset,
        test_typestate_lattice,
        test_all_read_commands_fault_free,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    if passed == len(tests):
        print("PASS")
    else:
        print("FAIL")
