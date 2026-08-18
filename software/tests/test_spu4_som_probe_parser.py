#!/usr/bin/env python3
"""test_spu4_som_probe_parser.py — hardware-free test for
software/lib/spu4_som_probe_parser.py, the shared UART result-line parser
for both SPU-4 SOM edge probes (fixed self-test and interactive).

No hardware required. Run: python3 software/tests/test_spu4_som_probe_parser.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from software.lib.spu4_som_probe_parser import parse_line

checks = 0
failures = []


def check(desc, condition):
    global checks
    checks += 1
    if not condition:
        failures.append(desc)


# ── Known-good lines ────────────────────────────────────────────────────

# The fixed probe's documented golden line (build_25k_spu4_som_edge_probe.sh,
# tang_primer_25k_spu4_som_edge_probe.v's header): PASS, node 1, Q=0x1900,
# id=0x1020 (ABI_MAJOR=1 ABI_MINOR=0 WRAPPER_ID=2 reserved=0).
golden = parse_line("SOM:P N=1 Q=00001900 S=07 L=012 I=1020\r\n")
check("golden line parses", golden is not None)
check("golden status_char == 'P'", golden.status_char == "P")
check("golden best_node == 1", golden.best_node == 1)
check("golden best_quadrance == 0x1900", golden.best_quadrance == 0x1900)
check("golden status == 0x07", golden.status == 0x07)
check("golden latency == 0x012", golden.latency == 0x012)
check("golden id == 0x1020", golden.id == 0x1020)
check("golden status decode: busy", golden.busy is True)
check("golden status decode: done", golden.done is True)
check("golden status decode: hydrated", golden.hydrated is True)
check("golden status decode: start_ignored", golden.start_ignored is False)

# "Still running" line — no CRLF, lowercase hex digits (real hardware only
# ever emits uppercase 'SOM:'/field-letter ASCII, but hex-digit case should
# still be tolerated defensively).
running = parse_line("SOM:. N=0 Q=deadbeef S=05 L=fff I=1020")
check("'still running' line with lowercase hex digits parses",
      running is not None and running.status_char == ".")
check("running best_quadrance == 0xdeadbeef",
      running.best_quadrance == 0xDEADBEEF)

# The interactive probe (Phase B1) reuses the identical byte layout with a
# different status-character alphabet ('D' done, 'F' malformed query) — the
# parser must not special-case the fixed probe's 'P'/'F'/'.' alphabet.
interactive_done = parse_line("SOM:D N=2 Q=00000000 S=06 L=001 I=1120\r\n")
check("interactive-probe 'D' status_char parses",
      interactive_done is not None and interactive_done.status_char == "D")

# ── Malformed / unrelated lines are rejected, not mis-parsed ───────────────

check("empty string returns None", parse_line("") is None)
check("whitespace-only line returns None", parse_line("   \r\n") is None)
check("boot-banner noise returns None",
      parse_line("SPU RP diagnostic console ready") is None)
check("truncated line (missing I field) returns None",
      parse_line("SOM:P N=1 Q=00001900 S=07 L=012") is None)
check("short Q field (7 hex digits) returns None",
      parse_line("SOM:P N=1 Q=0001900 S=07 L=012 I=1020") is None)
check("non-hex N field returns None",
      parse_line("SOM:P N=Z Q=00001900 S=07 L=012 I=1020") is None)
check("missing 'SOM:' prefix returns None",
      parse_line("N=1 Q=00001900 S=07 L=012 I=1020") is None)


if failures:
    print(f"FAIL: {len(failures)}/{checks} checks failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS ({checks} checks)")
