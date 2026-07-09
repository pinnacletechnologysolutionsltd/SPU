"""console.py — line-oriented transport for the RP2350/RP2040 diag console.

The firmware (hardware/rp_common/spu_diag.c) echoes every received character,
answers with one or more "OK ..." / "ERR ..." lines terminated by CRLF, then
prints a bare "> " prompt with NO trailing newline before waiting for the
next command. That prompt is the only reliable end-of-response marker, so
the reader accumulates raw bytes until the buffer ends with it.
"""

import time

PROMPT = b"> "
DEFAULT_TIMEOUT_S = 2.0


class ConsoleTimeoutError(TimeoutError):
    """Raised when the console does not produce a prompt within the timeout."""


class DiagConsole:
    """Raw transport: send one command line, get back its response lines.

    Works over anything exposing pyserial's `Serial`-like interface
    (`read(n)`, `in_waiting`, `write(bytes)`); a real `serial.Serial` in
    production, a canned byte-feeder in tests (see
    software/tests/test_spu_host_parser.py).
    """

    def __init__(self, ser, timeout_s=DEFAULT_TIMEOUT_S):
        self._ser = ser
        self._timeout_s = timeout_s

    def _read_until_prompt(self, timeout_s):
        deadline = time.monotonic() + timeout_s
        buf = b""
        while time.monotonic() < deadline:
            waiting = getattr(self._ser, "in_waiting", 1) or 1
            chunk = self._ser.read(waiting)
            if chunk:
                buf += chunk
                if buf.endswith(PROMPT):
                    return buf
                deadline = time.monotonic() + timeout_s
            else:
                time.sleep(0.005)
        raise ConsoleTimeoutError(
            "no '> ' prompt within %.1fs; got %r" % (timeout_s, buf)
        )

    def connect(self, timeout_s=None):
        """Drain the startup banner up to its first prompt. Call once after
        opening the port; harmless to call again (returns whatever is
        pending, which may be empty)."""
        return self._read_until_prompt(timeout_s or self._timeout_s)

    def command(self, line, timeout_s=None):
        """Send one command line, return its response as a list of decoded
        text lines (echo of the command and the trailing prompt stripped)."""
        self._ser.write(line.encode("ascii") + b"\n")
        raw = self._read_until_prompt(timeout_s or self._timeout_s)
        body = raw[: -len(PROMPT)]
        text = body.decode("ascii", errors="replace")
        lines = [l.strip("\r") for l in text.split("\n")]
        lines = [l for l in lines if l != ""]
        # First line is the character-echoed command itself (the firmware
        # echoes each typed char, then the CR/LF for Enter) — drop it.
        if lines and lines[0].strip() == line.strip():
            lines = lines[1:]
        return lines
